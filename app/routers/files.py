import os
import uuid
import mimetypes
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.room import Room
from app.models.room_member import RoomMember
from app.models.message import Message
from app.models.document import Document

router = APIRouter(tags=["files"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".txt", ".doc", ".docx", ".csv", ".zip"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _s3_client():
    region = os.getenv("AWS_REGION", "us-east-1")
    return boto3.client("s3", region_name=region)


def _build_s3_https_url(bucket: str, key: str, region: str) -> str:
    if region == "us-east-1":
        return f"https://{bucket}.s3.amazonaws.com/{key}"
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"


def _upload_bytes_to_s3(
    bucket: str,
    key: str,
    body: bytes,
    content_type: Optional[str],
    original_filename: str,
) -> str:
    client = _s3_client()
    region = os.getenv("AWS_REGION", "us-east-1")
    extra = {
        "Metadata": {"original-filename": original_filename[:1024]},
    }
    if content_type:
        extra["ContentType"] = content_type
    client.put_object(Bucket=bucket, Key=key, Body=body, **extra)
    return _build_s3_https_url(bucket, key, region)


def _approved_room_member(db: Session, room_id: int, user_id: int, need_write: bool = False):
    q = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == user_id,
        RoomMember.status == "approved",
    )
    if need_write:
        q = q.filter(RoomMember.role.in_(["write", "admin"]))
    return q.first()


@router.post("/rooms/{room_id}/upload")
def upload_file(
    room_id: int,
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if not _approved_room_member(db, room_id, user_id, need_write=True):
        raise HTTPException(status_code=403, detail="Not authorized to upload in this room")

    original_name = file.filename or "upload"
    _, ext = os.path.splitext(original_name)
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed")

    contents = file.file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    file_id = str(uuid.uuid4())
    stored_suffix = f"{file_id}{ext}"
    content_type, _ = mimetypes.guess_type(original_name)
    bucket = os.getenv("AWS_S3_BUCKET", "").strip()

    s3_url = None
    s3_key = None

    if bucket:
        s3_key = f"rooms/{room_id}/{stored_suffix}"
        try:
            s3_url = _upload_bytes_to_s3(bucket, s3_key, contents, content_type, original_name)
        except ClientError as e:
            raise HTTPException(status_code=502, detail=f"S3 upload failed: {e}") from e
    else:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, stored_suffix)
        with open(file_path, "wb") as f:
            f.write(contents)

    doc = Document(
        file_id=file_id,
        room_id=room_id,
        sender_id=user_id,
        original_filename=original_name,
        s3_url=s3_url,
        s3_key=s3_key,
    )
    db.add(doc)
    db.flush()

    file_url = f"/documents/{file_id}"
    db_msg = Message(
        room_id=room_id,
        sender_id=user_id,
        type="file",
        content=file_url,
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    db.refresh(doc)

    return {
        "message_id": db_msg.id,
        "file_id": doc.file_id,
        "file_url": file_url,
        "filename": doc.original_filename,
        "s3_url": doc.s3_url,
        "created_at": db_msg.created_at.isoformat(),
    }


@router.get("/rooms/{room_id}/documents")
def list_room_documents(
    room_id: int,
    user_id: int = Query(..., description="User requesting the list (must be an approved member)"),
    db: Session = Depends(get_db),
):
    if not db.query(Room).filter(Room.id == room_id).first():
        raise HTTPException(status_code=404, detail="Room not found")
    if not _approved_room_member(db, room_id, user_id, need_write=False):
        raise HTTPException(status_code=403, detail="Not a member of this room")

    rows = (
        db.query(Document)
        .filter(Document.room_id == room_id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return [
        {
            "file_id": d.file_id,
            "original_filename": d.original_filename,
            "sender_id": d.sender_id,
            "open_url": f"/documents/{d.file_id}",
            "s3_url": d.s3_url,
            "created_at": d.created_at.isoformat(),
        }
        for d in rows
    ]


@router.get("/documents/{file_id}")
def open_document(
    file_id: str,
    user_id: int = Query(..., description="User opening the file (must be an approved member)"),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.file_id == file_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not _approved_room_member(db, doc.room_id, user_id, need_write=False):
        raise HTTPException(status_code=403, detail="Not authorized to open this document")

    bucket = os.getenv("AWS_S3_BUCKET", "").strip()
    if doc.s3_key and bucket:
        try:
            client = _s3_client()
            expires = int(os.getenv("S3_PRESIGN_EXPIRES_SECONDS", "3600"))
            url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": doc.s3_key},
                ExpiresIn=expires,
            )
            return RedirectResponse(url=url)
        except ClientError as e:
            raise HTTPException(status_code=502, detail=f"Could not generate download URL: {e}") from e

    _, ext = os.path.splitext(doc.original_filename)
    ext = ext.lower()
    local_name = f"{doc.file_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, local_name)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    return FileResponse(
        file_path,
        filename=doc.original_filename,
        media_type=mimetypes.guess_type(doc.original_filename)[0] or "application/octet-stream",
    )


@router.get("/files/{filename}")
def get_file(filename: str):
    """Legacy local uploads (hex name only). New uploads use /documents/{file_id}."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
