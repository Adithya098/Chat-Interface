from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.room import Room
from app.models.room_member import RoomMember
from app.models.user import User
from app.schemas.room import RoomCreate, RoomResponse

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("/", response_model=RoomResponse, status_code=201)
def create_room(room: RoomCreate, db: Session = Depends(get_db)):
    # Verify creator exists
    creator = db.query(User).filter(User.id == room.created_by).first()
    if not creator:
        raise HTTPException(status_code=404, detail="Creator user not found")

    db_room = Room(name=room.name, created_by=room.created_by)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)

    # Auto-add creator as admin member (approved)
    member = RoomMember(
        user_id=room.created_by,
        room_id=db_room.id,
        role="admin",
        status="approved",
    )
    db.add(member)
    db.commit()

    return db_room


@router.get("/", response_model=list[RoomResponse])
def get_rooms(db: Session = Depends(get_db)):
    return db.query(Room).all()


@router.get("/{room_id}", response_model=RoomResponse)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room
