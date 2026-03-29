# Chat Backend

Real-time chat system built with FastAPI, WebSockets, React, and PostgreSQL (AWS RDS). Deployed on Render.

## Features

- Role-based room access (`admin` / `write` / `read`)
- Join requests with admin approve/reject flow
- Real-time messaging over WebSocket
- Message replies (quoted preview + scroll-to-original)
- Admin moderation: delete messages and remove members
- Typing indicators and room presence (`online_users`)
- File uploads (images, PDFs, docs)
- Message history via REST

## Role Permissions

| Role | Read messages | Send messages | Reply to messages | Upload files | Approve/reject join requests | Delete messages | Remove members |
|------|----------------|---------------|-------------------|--------------|------------------------------|----------------|----------------|
| `admin` | Yes | Yes | Yes | Yes | Yes | Yes | Yes (cannot remove self/other admins) |
| `write` | Yes | Yes | Yes | Yes | No | No | No |
| `read` | Yes | No | No | No | No | No | No |

## Tech Stack

- **FastAPI** — API + WebSocket server
- **SQLAlchemy** — ORM
- **PostgreSQL (AWS RDS)** — persistent storage
- **Render** — hosting

## Project Structure

```
Chat-Interface/               # repo root (.env, package.json, runtime.txt)
├── backend/
│   ├── app/                  # FastAPI package (main, database, models, schemas, routers)
│   ├── scripts/              # e.g. seed_dummy_data
│   ├── uploads/              # Local file storage (non-Supabase)
│   └── requirements.txt
└── frontend/                 # React + Vite
```

## Setup

```bash
pip install -r backend/requirements.txt
npm install               # root: installs concurrently for `npm run dev`
cd frontend && npm install && cd ..
cp .env.example .env      # if present; otherwise create .env at repo root (see below)
```

**Development (API + Vite together):**

```bash
npm run dev
```

Additional local scripts:

```bash
npm run dev:api      # backend only
npm run dev:web      # frontend only
```

- Open the URL Vite prints (default **http://localhost:3000**). In dev, HTTP requests are proxied and WebSocket connects to **127.0.0.1:8000**.
- API docs: http://localhost:8000/docs

**Backend only** (serves built `frontend/dist` if present):

```bash
cd backend && python -m uvicorn app.main:app --reload --no-access-log
```

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/` | Create user |
| POST | `/rooms/` | Create room |
| POST | `/rooms/{id}/join` | Request to join |
| POST | `/rooms/{id}/approve` | Admin approves member |
| POST | `/rooms/{id}/reject` | Admin rejects member |
| DELETE | `/rooms/{id}/members/{user_id}?admin_id={id}` | Admin removes member |
| GET | `/rooms/{id}/members` | List members |
| GET | `/rooms/{id}/pending` | List pending requests |
| GET | `/rooms/{id}/messages/` | Message history |
| DELETE | `/rooms/{id}/messages/{message_id}?admin_id={id}` | Admin deletes message |
| POST | `/rooms/{id}/upload` | Upload a file |
| GET | `/files/{filename}` | Serve a file |
| WS | `/ws/{room_id}?user_id=` | WebSocket connection |

## WebSocket Events

**Client → Server**
```json
{ "type": "message",     "content": "hello", "reply_to": 42 }
{ "type": "typing" }
{ "type": "stop_typing" }
{ "type": "file",        "message_id": 5, "file_url": "/files/abc.png", "filename": "photo.png" }
```

**Server → Client**
```json
{ "type": "message",     "id": 1, "sender_id": 3, "sender_name": "Alice", "content": "hello", "created_at": "...", "reply_to": 42, "reply_snippet": { "id": 42, "sender_name": "Bob", "content": "Original message preview..." } }
{ "type": "typing",      "user_id": 3, "user_name": "Alice" }
{ "type": "stop_typing", "user_id": 3, "user_name": "Alice" }
{ "type": "file",        "id": 5, "sender_id": 3, "sender_name": "Alice", "file_url": "...", "filename": "..." }
{ "type": "system",      "content": "User 3 joined the room" }
{ "type": "online_users","users": [1, 2, 3] }
{ "type": "error",       "content": "You don't have write permission in this room" }
{ "type": "message_deleted", "message_id": 100 }
{ "type": "member_removed",  "user_id": 5 }
{ "type": "kicked",          "content": "You have been removed from this room" }
```

