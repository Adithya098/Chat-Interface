from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Document(Base):
    """Room-shared upload: stable file_id, original filename preserved, object in S3 or local."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(36), unique=True, nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(512), nullable=False)
    s3_url = Column(Text, nullable=True)
    s3_key = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
