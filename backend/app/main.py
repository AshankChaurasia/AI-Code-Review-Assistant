from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from auth.auth import router as auth_router, GetCurrentUser
from review.gemini_review import gemini_code_review
from review.review_logic import run_flake8
from model.review_database import Reviews
from Database import get_db, init_db
from datetime import datetime
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    if init_db():
        logger.info("Database initialized successfully")
    else:
        logger.error("Database initialization failed")


@app.post("/review")
async def review_code(
    file: UploadFile = File(...),
    current_user: str = Depends(GetCurrentUser),
    db=Depends(get_db)
):
    try:
        logger.info(f"Starting review for user: {current_user}")
        
        # Read file content with timeout
        content = await asyncio.wait_for(file.read(), timeout=30.0)
        code = content.decode("utf-8")
        logger.info("File read successfully")

        # Run static analysis
        static_results = run_flake8(code)
        logger.info("Static analysis completed")

        # Get AI review
        ai_results = gemini_code_review(code, static_results)
        logger.info("AI review completed")

        # Save review to database
        review_entry = Reviews(
            email=current_user,
            code=code,
            static_result=static_results,
            ai_result=str(ai_results),
            created_at=datetime.utcnow()
        )
        db.add(review_entry)
        db.commit()
        db.refresh(review_entry)
        logger.info(f"Review saved with ID: {review_entry.id}")

        return {
            "user": current_user,
            "review_id": review_entry.id,
            "static_result": static_results,
            "ai_result": ai_results
        }

    except asyncio.TimeoutError:
        logger.error("Operation timed out")
        db.rollback()
        raise HTTPException(status_code=504, detail="Request timed out")

    except Exception as e:
        logger.error(f"Error in review: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing review: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)