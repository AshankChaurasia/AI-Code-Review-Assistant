from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from Database import Base

class Reviews(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    code = Column(String, nullable=False)
    static_result = Column(String)
    ai_result = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)