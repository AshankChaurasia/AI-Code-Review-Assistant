from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm import Session
import os
import logging
from dotenv import load_dotenv, find_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to find a .env file in current directory or any parent directory
dotenv_path = find_dotenv(usecwd=True)
if dotenv_path:
    load_dotenv(dotenv_path)
    logger.info(f"Loaded environment variables from: {dotenv_path}")
else:
    logger.info(".env file not found in project tree; relying on environment variables from the OS.")

# Require DATABASE_URL to be set in the environment.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    logger.error("DATABASE_URL environment variable is NOT set. Set DATABASE_URL before starting the app.")
    raise RuntimeError("DATABASE_URL environment variable is required")

logger.info("Connecting to database (connection string hidden).")

# Create SQLAlchemy engine with pool_pre_ping for production readiness
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a single Base instance used by all models
Base = declarative_base()

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    try:
        # Import models here to avoid circular imports
        from model.account_database import Accounts  # noqa: F401
        from model.review_database import Reviews    # noqa: F401

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Verify tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Available tables: {tables}")
        
        # Verify expected tables exist
        expected_tables = {'accounts', 'reviews'}
        actual_tables = set(tables)
        
        if not expected_tables.issubset(actual_tables):
            missing = expected_tables - actual_tables
            logger.warning(f"Missing tables: {missing}")
            return False
            
        logger.info("All required tables are present")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        return False