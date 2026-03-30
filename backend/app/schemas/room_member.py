from pydantic import BaseModel
from datetime import datetime


class JoinRequest(BaseModel):
    user_id: int
    role: str = "write"  # read | write | admin


class ApproveRejectRequest(BaseModel):
    admin_id: int  # who is performing the action
    user_id: int   # who is being approved/rejected


class RoomMemberResponse(BaseModel):
    id: int
    user_id: int
    room_id: int
    role: str
    status: str
    joined_at: datetime

    model_config = {"from_attributes": True}
