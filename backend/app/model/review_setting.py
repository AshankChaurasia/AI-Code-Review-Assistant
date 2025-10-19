# review_setting.py
from sqlalchemy.orm import Session
from model.review_database import Reviews
from Database import SessionLocal

def save_review(email: str, code: str, static_result: str, ai_result: str):
    """Save a code review result to the database."""
    db: Session = SessionLocal()
    try:
        review = Reviews(
            email=email,
            code=code,
            static_result=static_result,
            ai_result=str(ai_result),
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return {"message": "Review saved successfully", "id": review.id}
    except Exception as e:
        db.rollback()
        return {"error": f"Failed to save review: {e}"}
    finally:
        db.close()