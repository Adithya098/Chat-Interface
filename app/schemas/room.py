from pydantic import BaseModel
from datetime import datetime


class RoomCreate(BaseModel):
    name: str
    created_by: int


class RoomResponse(BaseModel):
    id: int
    name: str
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}
