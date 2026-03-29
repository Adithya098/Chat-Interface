from pydantic import BaseModel
from datetime import datetime


class MessageResponse(BaseModel):
    id: int
    room_id: int
    sender_id: int
    type: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
