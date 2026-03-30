"""Message retrieval and moderation endpoints for room conversations.

This module returns paginated message history with sender names, 
resolves file metadata for file-type messages, enriches replies with compact original-message snippets, 
and allows admins to delete messages while broadcasting realtime deletion events."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.connection_manager import manager
from app.models.document import Document
from app.models.message import Message
from app.models.room import Room
from app.models.room_member import RoomMember
from app.models.user import User
from app.schemas.message import MessageResponse, ReplySnippet

router = APIRouter(prefix="/rooms/{room_id}/messages", tags=["messages"])

_DOC_PREFIX = "/documents/"


def _file_id_from_message_content(content: str) -> str | None:
    """Extracts the document file ID from a message content path when the prefix matches."""
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
    """Returns paginated room messages with sender names, file metadata, and reply snippets."""
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

    # Resolve reply snippets: gather all reply_to IDs, fetch originals in one query
    reply_ids = [msg.reply_to for msg, _ in rows_chrono if msg.reply_to is not None]
    reply_map: dict[int, ReplySnippet] = {}
    if reply_ids:
        from sqlalchemy.orm import aliased
        OrigUser = aliased(User)
        orig_rows = (
            db.query(Message, OrigUser.name)
            .join(OrigUser, Message.sender_id == OrigUser.id)
            .filter(Message.id.in_(reply_ids))
            .all()
        )
        for orig_msg, orig_name in orig_rows:
            preview = orig_msg.content[:120]
            reply_map[orig_msg.id] = ReplySnippet(
                id=orig_msg.id,
                sender_name=orig_name,
                content=preview,
            )

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
                reply_to=msg.reply_to,
                reply_snippet=reply_map.get(msg.reply_to) if msg.reply_to else None,
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
    """Deletes a room message when requested by an approved admin and broadcasts removal."""
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
