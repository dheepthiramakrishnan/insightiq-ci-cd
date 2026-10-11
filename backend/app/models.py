"""
models.py
----------
SQLAlchemy ORM models representing MySQL tables for InsightIQ.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """Represents an application user."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    datasets = relationship(
        "UploadedDataset", back_populates="owner", cascade="all, delete-orphan"
    )


class UploadedDataset(Base):
    """Represents metadata for an uploaded sales dataset CSV."""

    __tablename__ = "uploaded_datasets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    row_count = Column(Integer, default=0)
    total_sales = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="datasets")

    # Cached AI insights (JSON-serialized text) so we don't re-call
    # the Gemini API every time the Insights page is opened.
    ai_insights = Column(Text, nullable=True)
