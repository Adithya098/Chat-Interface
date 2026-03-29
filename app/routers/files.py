import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.room import Room
from app.models.room_member import RoomMember
from app.models.message import Message

router = APIRouter(tags=["files"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".txt", ".doc", ".docx", ".csv", ".zip"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/rooms/{room_id}/upload")
def upload_file(
    room_id: int,
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Verify room exists
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Verify user is approved member with write/admin
    member = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == user_id,
        RoomMember.status == "approved",
        RoomMember.role.in_(["write", "admin"]),
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not authorized to upload in this room")

    # Validate extension
    _, ext = os.path.splitext(file.filename or "")
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed")

    # Read and validate size
    contents = file.file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    # Save file with unique name
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(file_path, "wb") as f:
        f.write(contents)

    # Save file message to DB
    file_url = f"/files/{unique_name}"
    db_msg = Message(
        room_id=room_id,
        sender_id=user_id,
        type="file",
        content=file_url,
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)

    return {
        "message_id": db_msg.id,
        "file_url": file_url,
        "filename": file.filename,
        "created_at": db_msg.created_at.isoformat(),
    }


@router.get("/files/{filename}")
def get_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
