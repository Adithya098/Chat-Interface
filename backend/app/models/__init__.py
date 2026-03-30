"""Convenience exports for all SQLAlchemy models used by the backend.

Importing this module ensures model classes are registered in SQLAlchemy metadata, 
so that the tables can be created and migrations can discover user, room, membership, message, and document entities."""

from app.models.user import User
from app.models.room import Room
from app.models.room_member import RoomMember
from app.models.message import Message
from app.models.document import Document

__all__ = ["User", "Room", "RoomMember", "Message", "Document"]
