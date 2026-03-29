from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.message import Message
from app.models.room import Room
from app.schemas.message import MessageResponse

router = APIRouter(prefix="/rooms/{room_id}/messages", tags=["messages"])


@router.get("/", response_model=list[MessageResponse])
def get_messages(
    room_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    messages = (
        db.query(Message)
        .filter(Message.room_id == room_id)
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    # Return in chronological order
    return list(reversed(messages))
