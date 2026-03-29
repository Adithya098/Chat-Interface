from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.connection_manager import manager
from app.models.document import Document
from app.models.message import Message
from app.models.room import Room
from app.models.room_member import RoomMember
from app.models.user import User
from app.schemas.message import MessageResponse

router = APIRouter(prefix="/rooms/{room_id}/messages", tags=["messages"])

_DOC_PREFIX = "/documents/"


def _file_id_from_message_content(content: str) -> str | None:
    if not content.startswith(_DOC_PREFIX):
        return None
    rest = content[len(_DOC_PREFIX) :].split("?")[0].strip("/")
    return rest or None


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

    rows = (
        db.query(Message, User.name)
        .join(User, Message.sender_id == User.id)
        .filter(Message.room_id == room_id)
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    rows_chrono = list(reversed(rows))

    file_ids = [
        fid
        for msg, _ in rows_chrono
        if msg.type == "file" and (fid := _file_id_from_message_content(msg.content))
    ]
    filenames: dict[str, str] = {}
    if file_ids:
        for doc in db.query(Document).filter(Document.file_id.in_(file_ids)).all():
            filenames[doc.file_id] = doc.original_filename

    out: list[MessageResponse] = []
    for msg, sender_name in rows_chrono:
        fid = _file_id_from_message_content(msg.content) if msg.type == "file" else None
        out.append(
            MessageResponse(
                id=msg.id,
                room_id=msg.room_id,
                sender_id=msg.sender_id,
                sender_name=sender_name,
                type=msg.type,
                content=msg.content,
                created_at=msg.created_at,
                filename=filenames.get(fid) if fid else None,
            )
        )
    return out


@router.delete("/{message_id}")
async def delete_message(
    room_id: int,
    message_id: int,
    admin_id: int = Query(...),
    db: Session = Depends(get_db),
):
    # Verify admin
    admin = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == admin_id,
        RoomMember.role == "admin",
        RoomMember.status == "approved",
    ).first()
    if not admin:
        raise HTTPException(status_code=403, detail="Only admins can delete messages")

    msg = db.query(Message).filter(
        Message.id == message_id,
        Message.room_id == room_id,
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(msg)
    db.commit()

    await manager.broadcast(room_id, {"type": "message_deleted", "message_id": message_id})

    return {"detail": "Message deleted", "message_id": message_id}
