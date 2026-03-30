from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.connection_manager import manager
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
    if req.role not in ("read", "write", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'read', 'write', or 'admin'")

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


@router.delete("/members/{user_id}")
async def remove_member(
    room_id: int,
    user_id: int,
    admin_id: int = Query(...),
    db: Session = Depends(get_db),
):
    _get_room_or_404(room_id, db)
    _get_admin_or_403(room_id, admin_id, db)

    if admin_id == user_id:
        raise HTTPException(status_code=400, detail="Admins cannot remove themselves")

    member = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Prevent removing admin if they're the last admin
    if member.role == "admin":
        admin_count = db.query(RoomMember).filter(
            RoomMember.room_id == room_id,
            RoomMember.role == "admin",
            RoomMember.status == "approved",
        ).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last admin")

    # Fetch room and admin names for the notification message
    room = db.query(Room).filter(Room.id == room_id).first()
    admin_user = db.query(User).filter(User.id == admin_id).first()
    room_name = room.name if room else f"room {room_id}"
    admin_name = admin_user.name if admin_user else f"Admin {admin_id}"

    db.delete(member)
    db.commit()

    await manager.kick_user(
        room_id,
        user_id,
        reason=f"You were removed from '{room_name}' by {admin_name}",
    )
    await manager.broadcast(room_id, {"type": "member_removed", "user_id": user_id})

    return {"detail": "Member removed"}


@router.get("/members", response_model=list[RoomMemberResponse])
def list_members(room_id: int, db: Session = Depends(get_db)):
    _get_room_or_404(room_id, db)
    return db.query(RoomMember).filter(RoomMember.room_id == room_id).all()


@router.post("/promote")
async def promote_member(room_id: int, req: ApproveRejectRequest, db: Session = Depends(get_db)):
    """Admin promotes a member to admin role."""
    _get_room_or_404(room_id, db)
    _get_admin_or_403(room_id, req.admin_id, db)

    member = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == req.user_id,
        RoomMember.status == "approved",
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member.role == "admin":
        raise HTTPException(status_code=400, detail="User is already an admin")

    member.role = "admin"
    db.commit()
    db.refresh(member)

    # Promoted to admin notification (disabled)
    # await manager.broadcast(room_id, {
    #     "type": "system",
    #     "content": f"User {req.user_id} was promoted to admin",
    # })

    return member


@router.post("/leave")
async def leave_room(
    room_id: int,
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """User leaves a room voluntarily."""
    _get_room_or_404(room_id, db)

    member = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Not a member of this room")

    # Prevent the last admin from leaving
    if member.role == "admin":
        admin_count = db.query(RoomMember).filter(
            RoomMember.room_id == room_id,
            RoomMember.role == "admin",
            RoomMember.status == "approved",
        ).count()
        if admin_count == 1:
            raise HTTPException(status_code=400, detail="Cannot leave: you are the only admin")

    db.delete(member)
    db.commit()

    await manager.kick_user(room_id, user_id, reason="You left the room")
    await manager.broadcast(room_id, {
        "type": "system",
        "content": f"User {user_id} left the room",
    })

    return {"detail": "Left room successfully"}


@router.get("/pending", response_model=list[RoomMemberResponse])
def list_pending(room_id: int, db: Session = Depends(get_db)):
    _get_room_or_404(room_id, db)
    return db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.status == "pending",
    ).all()
