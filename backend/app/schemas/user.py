from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str
    mobile: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Keep old schema for backward compat (used internally)
class UserCreate(BaseModel):
    name: str
    email: EmailStr


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    mobile: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
