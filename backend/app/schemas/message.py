from pydantic import BaseModel
from datetime import datetime


class ReplySnippet(BaseModel):
    id: int
    sender_name: str
    content: str


class MessageResponse(BaseModel):
    id: int
    room_id: int
    sender_id: int
    sender_name: str
    type: str
    content: str
    created_at: datetime
    filename: str | None = None
    reply_to: int | None = None
    reply_snippet: ReplySnippet | None = None
