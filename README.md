# Chat Backend

Real-time chat backend built with FastAPI, WebSockets, and PostgreSQL (AWS RDS). Deployed on Render.

## Features

- Rooms with role-based access (admin / write / read)
- Join requests and admin approval flow
- Real-time messaging via WebSocket
- Typing indicators
- File uploads (images, PDFs, docs)
- Message history via REST

## Tech Stack

- **FastAPI** — API + WebSocket server
- **SQLAlchemy** — ORM
- **PostgreSQL (AWS RDS)** — persistent storage
- **Render** — hosting

## Project Structure

```
app/
├── main.py               # App entry point, middleware
├── database.py           # SQLAlchemy engine + session
├── connection_manager.py # In-memory WebSocket manager
├── models/               # DB models: User, Room, RoomMember, Message
├── schemas/              # Pydantic schemas
└── routers/
    ├── users.py          # User CRUD
    ├── rooms.py          # Room CRUD
    ├── members.py        # Join / approve / reject
    ├── messages.py       # Message history
    ├── files.py          # File upload + serve
    └── ws.py             # WebSocket endpoint
```

## Setup

```bash
pip install -r requirements.txt
npm install               # root: installs concurrently for `npm run dev`
cd frontend && npm install && cd ..
cp .env.example .env      # if present; otherwise create .env (see below)
```

**Development (API + Vite together):**

```bash
npm run dev
```

- Open the app at **http://localhost:3000** (Vite proxies API/WebSocket to port 8000).
- API docs: http://localhost:8000/docs

**Backend only** (serves built `frontend/dist` if present):

```bash
python -m uvicorn app.main:app --reload
```

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/` | Create user |
| POST | `/rooms/` | Create room |
| POST | `/rooms/{id}/join` | Request to join |
| POST | `/rooms/{id}/approve` | Admin approves member |
| POST | `/rooms/{id}/reject` | Admin rejects member |
| GET | `/rooms/{id}/members` | List members |
| GET | `/rooms/{id}/pending` | List pending requests |
| GET | `/rooms/{id}/messages/` | Message history |
| POST | `/rooms/{id}/upload` | Upload a file |
| GET | `/files/{filename}` | Serve a file |
| WS | `/ws/{room_id}?user_id=` | WebSocket connection |

## WebSocket Events

**Client → Server**
```json
{ "type": "message",     "content": "hello" }
{ "type": "typing" }
{ "type": "stop_typing" }
{ "type": "file",        "message_id": 5, "file_url": "/files/abc.png", "filename": "photo.png" }
```

**Server → Client**
```json
{ "type": "message",     "id": 1, "sender_id": 3, "sender_name": "Alice", "content": "hello", "created_at": "..." }
{ "type": "typing",      "user_id": 3, "user_name": "Alice" }
{ "type": "stop_typing", "user_id": 3, "user_name": "Alice" }
{ "type": "file",        "id": 5, "sender_id": 3, "sender_name": "Alice", "file_url": "...", "filename": "..." }
{ "type": "system",      "content": "User 3 joined the room" }
{ "type": "online_users","users": [1, 2, 3] }
{ "type": "error",       "content": "You don't have write permission in this room" }
```

