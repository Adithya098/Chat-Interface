from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.models.room_member import RoomMember
from app.models.user import User
from app.models.message import Message
from app.connection_manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    user_id: int = Query(...),
):
    # Get a DB session for auth checks
    db = SessionLocal()

    try:
        # 1. Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.close(code=4001, reason="User not found")
            return

        # 2. Verify user is an approved member of this room
        member = db.query(RoomMember).filter(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user_id,
            RoomMember.status == "approved",
        ).first()
        if not member:
            await websocket.close(code=4003, reason="Not an approved member of this room")
            return

        user_name = user.name

        # 3. Connect
        await manager.connect(room_id, user_id, websocket)

        # 4. Send online users list to the newly connected user
        online = manager.get_online_users(room_id)
        await manager.send_to_user(room_id, user_id, {
            "type": "online_users",
            "users": online,
        })

    except Exception:
        db.close()
        return

    db.close()

    # 5. Listen for messages
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "message":
                role = member.role
                if role not in ("write", "admin"):
                    await manager.send_to_user(room_id, user_id, {
                        "type": "error",
                        "content": "You don't have write permission in this room",
                    })
                    continue

                # Save message to DB
                msg_db = SessionLocal()
                try:
                    db_msg = Message(
                        room_id=room_id,
                        sender_id=user_id,
                        type="text",
                        content=data.get("content", ""),
                    )
                    msg_db.add(db_msg)
                    msg_db.commit()
                    msg_db.refresh(db_msg)

                    # Broadcast with DB id and timestamp
                    await manager.broadcast(room_id, {
                        "type": "message",
                        "id": db_msg.id,
                        "sender_id": user_id,
                        "sender_name": user_name,
                        "content": db_msg.content,
                        "created_at": db_msg.created_at.isoformat(),
                    })
                finally:
                    msg_db.close()

            elif msg_type == "typing":
                await manager.broadcast(room_id, {
                    "type": "typing",
                    "user_id": user_id,
                    "user_name": user_name,
                }, exclude_user=user_id)

            elif msg_type == "stop_typing":
                await manager.broadcast(room_id, {
                    "type": "stop_typing",
                    "user_id": user_id,
                    "user_name": user_name,
                }, exclude_user=user_id)

            elif msg_type == "file":
                # Client sends this after REST upload to notify the room
                # {"type": "file", "file_url": "/files/abc.png", "filename": "photo.png", "message_id": 5}
                role = member.role
                if role not in ("write", "admin"):
                    await manager.send_to_user(room_id, user_id, {
                        "type": "error",
                        "content": "You don't have write permission in this room",
                    })
                    continue

                await manager.broadcast(room_id, {
                    "type": "file",
                    "id": data.get("message_id"),
                    "sender_id": user_id,
                    "sender_name": user_name,
                    "file_url": data.get("file_url", ""),
                    "filename": data.get("filename", ""),
                })

    except WebSocketDisconnect:
        manager.disconnect(room_id, user_id)
        await manager.broadcast(room_id, {
            "type": "system",
            "content": f"User {user_id} left the room",
        })
    except Exception:
        manager.disconnect(room_id, user_id)
