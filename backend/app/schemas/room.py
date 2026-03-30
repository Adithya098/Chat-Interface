"""Pydantic schemas for room creation inputs and room response outputs.

This module defines the data contract for creating rooms and serializing persisted room entities returned by room APIs."""

from pydantic import BaseModel
from datetime import datetime


class RoomCreate(BaseModel):
    """Request payload for creating a room and specifying its creator user ID."""
    name: str
    created_by: int


class RoomResponse(BaseModel):
    """Serialized room data returned by room API endpoints."""
    id: int
    name: str
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}
