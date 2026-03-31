"""In-memory websocket connection orchestration for room-based realtime messaging.

This module tracks active sockets by room and user, accepts new websocket connections, 
removes stale/disconnected sockets, supports targeted user notifications and room-wide broadcasts, 
handles forced disconnects (kick events), and reports currently online users per room."""

from fastapi import WebSocket


class ConnectionManager:
    """In-memory manager tracking active WebSocket connections per room."""

    def __init__(self):
        """Initializes the per-room and per-user websocket tracking structure."""
        # {room_id: {user_id: [WebSocket, ...]}}
        self.rooms: dict[int, dict[int, list[WebSocket]]] = {}

    async def connect(self, room_id: int, user_id: int, websocket: WebSocket):
        """Accepts and stores a websocket connection for a user in a room."""
        if room_id not in self.rooms:
            self.rooms[room_id] = {}
        if user_id not in self.rooms[room_id]:
            self.rooms[room_id][user_id] = []
        self.rooms[room_id][user_id].append(websocket)

        # Notify room that user joined (disabled)
        # await self.broadcast(room_id, {
        #     "type": "system",
        #     "content": f"User {user_id} joined the room",
        # }, exclude_user=user_id)

    def disconnect(self, room_id: int, user_id: int, websocket: WebSocket | None = None):
        """Removes one or all sockets for a user and cleans empty room/user buckets."""
        if room_id in self.rooms:
            user_connections = self.rooms[room_id].get(user_id)
            if not user_connections:
                return

            if websocket is not None:
                try:
                    user_connections.remove(websocket)
                except ValueError:
                    return
            else:
                user_connections.clear()

            if not user_connections:
                self.rooms[room_id].pop(user_id, None)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def kick_user(self, room_id: int, user_id: int, reason: str = "You have been removed from this room"):
        """Sends a kick event to all user sockets, closes them, and removes them from tracking."""
        user_connections = list(self.rooms.get(room_id, {}).get(user_id, []))
        for ws in user_connections:
            try:
                await ws.send_json({"type": "kicked", "content": reason})
                await ws.close(code=4000)
            except Exception:
                pass
            self.disconnect(room_id, user_id, ws)

    async def broadcast(
        self,
        room_id: int,
        message: dict,
        exclude_user: int | None = None,
        exclude_websocket: WebSocket | None = None,
    ):
        """Broadcasts a JSON payload to all room sockets with optional exclusions."""
        connections = self.rooms.get(room_id, {})
        for uid, sockets in list(connections.items()):
            if uid == exclude_user:
                continue
            for ws in list(sockets):
                if exclude_websocket is not None and ws is exclude_websocket:
                    continue
                try:
                    await ws.send_json(message)
                except Exception:
                    # Connection is dead, clean it up
                    self.disconnect(room_id, uid, ws)

    async def send_to_user(self, room_id: int, user_id: int, message: dict):
        """Sends a JSON payload to every active websocket for a specific user in a room."""
        sockets = self.rooms.get(room_id, {}).get(user_id, [])
        for ws in list(sockets):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(room_id, user_id, ws)

    def get_online_users(self, room_id: int) -> list[int]:
        """Returns user IDs that currently have at least one active websocket in a room."""
        return list(self.rooms.get(room_id, {}).keys())


# Single global instance
manager = ConnectionManager()
