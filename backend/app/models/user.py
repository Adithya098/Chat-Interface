"""SQLAlchemy model definition for application users.

This file declares the users table fields for identity and authentication-related data, 
including display name, unique email, optional password hash/mobile, and creation timestamp metadata."""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """Represents a chat user identity with login and profile attributes."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)   # bcrypt hash
    mobile = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
