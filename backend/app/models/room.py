"""SQLAlchemy model definition for chat rooms.

This file declares the rooms table structure, including room identity, human-readable name, 
creator linkage to a user record, and room creation timestamp."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Room(Base):
    """Represents a chat room created by a user and identified by name."""
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
