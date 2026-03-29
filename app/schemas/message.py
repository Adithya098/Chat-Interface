from pydantic import BaseModel
from datetime import datetime


class MessageResponse(BaseModel):
    id: int
    room_id: int
    sender_id: int
    sender_name: str
    type: str
    content: str
    created_at: datetime
    filename: str | None = None
