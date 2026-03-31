"""Room management endpoints for creating and reading chat rooms.

This module validates room creators, persists new room records,
auto-enrolls creators as approved admins, and provides list/detail APIs
for room discovery. All endpoints require a valid JWT — the creator
identity is extracted from the token, not the request body."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.room import Room
from app.models.room_member import RoomMember
from app.models.user import User
from app.schemas.room import RoomCreate, RoomResponse
from app.auth import get_current_user

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("/", response_model=RoomResponse, status_code=201)
def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Creates a room and automatically adds the token-authenticated caller as approved admin."""
    db_room = Room(name=room.name, created_by=current_user.id)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)

    member = RoomMember(
        user_id=current_user.id,
        room_id=db_room.id,
        role="admin",
        status="approved",
    )
    db.add(member)
    db.commit()

    return db_room


@router.get("/", response_model=list[RoomResponse])
def get_rooms(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Returns all chat rooms — requires a valid JWT."""
    return db.query(Room).all()


@router.get("/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Returns room details for a specific room ID — requires a valid JWT."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room
