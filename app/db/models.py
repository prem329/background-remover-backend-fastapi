from sqlalchemy import Column, Index, Integer, String, ForeignKey, DateTime, column
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    
class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    job_id = Column(String, unique=True, index=True)

    original_path = Column(String)
    processed_path = Column(String)

    status = Column(String, default="processing")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
Index("idx_user_created", Image.user_id, Image.created_at)