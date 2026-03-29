from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.room import Room
from app.models.room_member import RoomMember
from app.schemas.room_member import JoinRequest, ApproveRejectRequest, RoomMemberResponse

router = APIRouter(prefix="/rooms/{room_id}", tags=["members"])


def _get_room_or_404(room_id: int, db: Session) -> Room:
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


def _get_admin_or_403(room_id: int, admin_id: int, db: Session) -> RoomMember:
    admin = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == admin_id,
        RoomMember.role == "admin",
        RoomMember.status == "approved",
    ).first()
    if not admin:
        raise HTTPException(status_code=403, detail="Only admins can perform this action")
    return admin


@router.post("/join", response_model=RoomMemberResponse, status_code=201)
def join_room(room_id: int, req: JoinRequest, db: Session = Depends(get_db)):
    _get_room_or_404(room_id, db)

    # Check user exists
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already a member
    existing = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == req.user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already a member or pending request exists")

    # Validate role
    if req.role not in ("read", "write"):
        raise HTTPException(status_code=400, detail="Role must be 'read' or 'write'")

    member = RoomMember(
        user_id=req.user_id,
        room_id=room_id,
        role=req.role,
        status="pending",
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.post("/approve", response_model=RoomMemberResponse)
def approve_member(room_id: int, req: ApproveRejectRequest, db: Session = Depends(get_db)):
    _get_room_or_404(room_id, db)
    _get_admin_or_403(room_id, req.admin_id, db)

    member = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == req.user_id,
        RoomMember.status == "pending",
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="No pending request found for this user")

    member.status = "approved"
    db.commit()
    db.refresh(member)
    return member


@router.post("/reject", response_model=RoomMemberResponse)
def reject_member(room_id: int, req: ApproveRejectRequest, db: Session = Depends(get_db)):
    _get_room_or_404(room_id, db)
    _get_admin_or_403(room_id, req.admin_id, db)

    member = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == req.user_id,
        RoomMember.status == "pending",
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="No pending request found for this user")

    member.status = "rejected"
    db.commit()
    db.refresh(member)
    return member


@router.get("/members", response_model=list[RoomMemberResponse])
def list_members(room_id: int, db: Session = Depends(get_db)):
    _get_room_or_404(room_id, db)
    return db.query(RoomMember).filter(RoomMember.room_id == room_id).all()


@router.get("/pending", response_model=list[RoomMemberResponse])
def list_pending(room_id: int, db: Session = Depends(get_db)):
    _get_room_or_404(room_id, db)
    return db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.status == "pending",
    ).all()
