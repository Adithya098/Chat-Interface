"""Realtime websocket endpoint for room chat event handling.

This module authenticates websocket users against approved room membership, 
manages connect/disconnect presence updates, receives message/typing/file events from clients, 
persists chat messages, broadcasts payloads to room participants, and cleans up connection state on disconnect/errors."""

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
    """Handles websocket lifecycle for a room member, including auth checks and message fanout."""
    # Get a DB session for auth checks
    db = SessionLocal()
    accepted = False

    try:
        # Accept first so all failures can return a proper websocket close frame.
        await websocket.accept()
        accepted = True

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

        # 4. Broadcast online users list to everyone in the room
        online = manager.get_online_users(room_id)
        await manager.broadcast(room_id, {
            "type": "online_users",
            "users": online,
        })

    except Exception:
        if accepted:
            await websocket.close(code=1011, reason="Internal server error")
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
                    reply_to_id = data.get("reply_to")
                    # Build reply snippet if replying
                    reply_snippet = None
                    if reply_to_id is not None:
                        orig = msg_db.query(Message).filter(Message.id == reply_to_id).first()
                        if orig:
                            orig_user = msg_db.query(User).filter(User.id == orig.sender_id).first()
                            reply_snippet = {
                                "id": orig.id,
                                "sender_name": orig_user.name if orig_user else f"User {orig.sender_id}",
                                "content": orig.content[:120],
                            }

                    db_msg = Message(
                        room_id=room_id,
                        sender_id=user_id,
                        type="text",
                        content=data.get("content", ""),
                        reply_to=reply_to_id,
                    )
                    msg_db.add(db_msg)
                    msg_db.commit()
                    msg_db.refresh(db_msg)

                    # Broadcast with DB id and timestamp
                    broadcast_payload = {
                        "type": "message",
                        "id": db_msg.id,
                        "sender_id": user_id,
                        "sender_name": user_name,
                        "content": db_msg.content,
                        "created_at": db_msg.created_at.isoformat(),
                        "reply_to": reply_to_id,
                        "reply_snippet": reply_snippet,
                    }
                    await manager.broadcast(room_id, broadcast_payload)
                finally:
                    msg_db.close()

            elif msg_type == "typing":
                # print(f"[WS][typing-in] room={room_id} user_id={user_id} user_name={user_name}", flush=True)
                await manager.broadcast(room_id, {
                    "type": "typing",
                    "user_id": user_id,
                    "user_name": user_name,
                }, exclude_websocket=websocket)

            elif msg_type == "stop_typing":
                # print(f"[WS][stop-typing-in] room={room_id} user_id={user_id} user_name={user_name}", flush=True)
                await manager.broadcast(room_id, {
                    "type": "stop_typing",
                    "user_id": user_id,
                    "user_name": user_name,
                }, exclude_websocket=websocket)

            elif msg_type == "file":
                # Client sends this after REST upload to notify the room
                # {"type": "file", "file_url": "/documents/<file_id>", "filename": "<original name>", "message_id": 5}
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
        manager.disconnect(room_id, user_id, websocket)
        await manager.broadcast(room_id, {
            "type": "stop_typing",
            "user_id": user_id,
            "user_name": user_name,
        })
        # User left notification (disabled)
        # await manager.broadcast(room_id, {
        #     "type": "system",
        #     "content": f"User {user_id} left the room",
        # })
        online = manager.get_online_users(room_id)
        await manager.broadcast(room_id, {
            "type": "online_users",
            "users": online,
        })
    except Exception:
        manager.disconnect(room_id, user_id, websocket)
