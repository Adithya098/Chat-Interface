from fastapi import WebSocket


class ConnectionManager:
    """In-memory manager tracking active WebSocket connections per room."""

    def __init__(self):
        # {room_id: {user_id: WebSocket}}
        self.rooms: dict[int, dict[int, WebSocket]] = {}

    async def connect(self, room_id: int, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {}
        self.rooms[room_id][user_id] = websocket

        # Notify room that user joined
        await self.broadcast(room_id, {
            "type": "system",
            "content": f"User {user_id} joined the room",
        }, exclude_user=user_id)

    def disconnect(self, room_id: int, user_id: int):
        if room_id in self.rooms:
            self.rooms[room_id].pop(user_id, None)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast(self, room_id: int, message: dict, exclude_user: int | None = None):
        """Send a message to all connected users in a room."""
        connections = self.rooms.get(room_id, {})
        for uid, ws in list(connections.items()):
            if uid == exclude_user:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                # Connection is dead, clean it up
                self.disconnect(room_id, uid)

    async def send_to_user(self, room_id: int, user_id: int, message: dict):
        """Send a message to a specific user in a room."""
        ws = self.rooms.get(room_id, {}).get(user_id)
        if ws:
            await ws.send_json(message)

    def get_online_users(self, room_id: int) -> list[int]:
        return list(self.rooms.get(room_id, {}).keys())


# Single global instance
manager = ConnectionManager()
