"""Pydantic schemas for room membership actions and representations.

This module defines join request payloads, admin moderation request payloads, 
and membership response objects used by member-management endpoints."""

from pydantic import BaseModel
from datetime import datetime


class JoinRequest(BaseModel):
    """Request payload used when a user asks to join a room with a target role."""
    user_id: int
    role: str = "write"  # read | write | admin


class ApproveRejectRequest(BaseModel):
    """Request payload for admin moderation actions on a specific user membership."""
    admin_id: int  # who is performing the action
    user_id: int   # who is being approved/rejected


class RoomMemberResponse(BaseModel):
    """Serialized room membership record returned by member management endpoints."""
    id: int
    user_id: int
    room_id: int
    role: str
    status: str
    joined_at: datetime

    model_config = {"from_attributes": True}
