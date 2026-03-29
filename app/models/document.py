from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Document(Base):
    """Room-shared upload: stable file_id; file bytes in Supabase Storage or local disk."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(36), unique=True, nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(512), nullable=False)
    storage_bucket = Column(String(255), nullable=True)
    storage_path = Column(String(1024), nullable=True)
    storage_public_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
