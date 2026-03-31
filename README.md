# Chat Interface

Real-time room-based chat system built with FastAPI, WebSockets, React, and PostgreSQL, with optional Supabase Storage for files.

## Features

### Authentication and User Session
- **JWT authentication**: login and signup return a signed JWT (`Authorization: Bearer <token>`) used on every subsequent request
- **Session persistence**: token and user profile are restored from `localStorage` on page reload; expired tokens force re-login automatically
- **Password security**: bcrypt hashing with salted hash — plaintext passwords are never stored
- **Input validation**: required fields and password minimum checks on signup

---

### Room Access and Membership
- **Role-based room access** (`admin` / `write` / `read`)
- **Join requests** with admin approve/reject flow — users may request `read` or `write` roles only (admin role is assigned by promotion, not self-request)
- **Admin request inbox** with grouped pending requests and role badges
- **Member management**: promote members to admin, remove members, prevent last-admin removal
- **Room management**: users can leave voluntarily; last-admin protection prevents orphaned rooms

---

### Messaging and Realtime Collaboration
- **Real-time messaging** over WebSocket with JWT-authenticated connections (`?token=` query param)
- **Message replies** with quoted preview and scroll-to-original
- **Typing indicators** with 3-second graceful fade
- **Room presence** (`online_users` count)
- **Admin moderation**: soft-delete messages with real-time deletion broadcast
- **Custom toast + confirm UX** instead of native browser alerts
- **Safer send UX**: message input is preserved and a toast is shown if the WebSocket is not open

---

### File and Document Handling
- **File uploads** (images, audio, video, PDFs, docs, archives)
- **Upload guardrails**: 10 MB max with frontend pre-check and backend enforcement
- **Media rendering**: images expand inline; audio and video have native player controls
- **Document center**: room-scoped document listing with secure open/download links
- **Dual storage**: Supabase Storage (signed URLs) with local-disk fallback
- **Authenticated media**: `<img>`, `<audio>`, `<video>` tags load media via `?token=` query param since browser tags cannot send `Authorization` headers

---

### Security
- All API endpoints (except `/users/login`, `/users/signup`, `/health`, `/db_health`) require a valid JWT
- Acting identity (`user_id`, `admin_id`) is always resolved from the token — never trusted from client-supplied parameters
- WebSocket connections are authenticated via `?token=` before any messages are accepted
- 401 responses automatically clear the local session and redirect to login

---

## Role Permissions

| Role | Read | Send | Reply | Upload | Approve/Reject | Delete Messages | Remove Members | Promote Members | Leave Room |
|------|------|------|-------|--------|---------------|-----------------|----------------|-----------------|------------|
| `admin` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (if not last admin) | ✓ | ✓ (if not last admin) |
| `write` | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ |
| `read`  | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |

---

## Tech Stack

- **FastAPI** — API + WebSocket server
- **SQLAlchemy** — ORM
- **PostgreSQL** — persistent storage
- **Supabase Storage (optional)** — document/file storage with signed URLs
- **React + Vite** — frontend client
- **bcrypt** — password hashing
- **python-jose** — JWT signing and verification (HS256)
- **Render** — hosting

---

## Project Structure

```
Chat-Interface/               # repo root (.env, package.json, runtime.txt)
├── backend/
│   ├── app/
│   │   ├── auth.py           # JWT token creation + verification dependencies
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── connection_manager.py
│   │   ├── supabase_storage.py
│   │   ├── models/           # SQLAlchemy models (user, room, message, room_member, document)
│   │   ├── routers/          # API + WebSocket route handlers
│   │   └── schemas/          # Pydantic request/response schemas
│   ├── scripts/              # Migration + seed utilities
│   ├── uploads/              # Local file storage (non-Supabase)
│   └── requirements.txt
└── frontend/                 # React + Vite
    └── src/
        ├── context/          # ChatContext (user session + JWT state)
        ├── hooks/            # useApi (auto-injects Bearer token), useWebSocket
        └── components/       # UI components
```

---

## Setup

```bash
pip install -r backend/requirements.txt
npm install               # root: installs concurrently for `npm run dev`
cd frontend && npm install && cd ..
```

Create a `.env` file at the repo root (see **Environment Variables** below).

**Development (API + Vite together):**

```bash
npm run dev
```

Additional scripts:

```bash
npm run dev:api      # backend only
npm run dev:web      # frontend only
```

Run one-time database migration scripts if needed after pulling new changes:

```bash
python backend/scripts/add_reply_to_column.py
python backend/scripts/add_is_deleted_to_messages.py
```

- Frontend: **http://localhost:3000** (Vite; HTTP requests are proxied, WebSocket connects to `127.0.0.1:8000`)
- API docs: **http://localhost:8000/docs**

**Backend only** (serves built `frontend/dist` if present):

```bash
cd backend && python -m uvicorn app.main:app --reload --no-access-log
```

---

## Environment Variables

Create a `.env` file at the repo root:

```env
# JWT — change this to a long random string before deploying
JWT_SECRET_KEY=change-this-to-a-long-random-secret-before-deploying

# PostgreSQL (direct connection)
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=6543
DB_NAME=postgres
DB_SSLMODE=require

# Supabase Storage (optional — omit to use local disk fallback)
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_STORAGE_BUCKET=
SUPABASE_STORAGE_PUBLIC_URLS=true
```

> `JWT_SECRET_KEY` must be set to a strong random value in production. The default in `auth.py` is a placeholder that will reject tokens signed with a different key after a redeploy.

---

## API Overview

All endpoints except `/users/login`, `/users/signup`, `/health`, and `/db_health` require:

```
Authorization: Bearer <token>
```

The token is returned by `/users/login` and `/users/signup`.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/users/signup` | — | Register (returns `{ token, user }`) |
| POST | `/users/login` | — | Authenticate (returns `{ token, user }`) |
| GET | `/users/` | Bearer | List users |
| GET | `/users/{user_id}` | Bearer | Get user by ID |
| POST | `/rooms/` | Bearer | Create room (creator from token) |
| GET | `/rooms/` | Bearer | List all rooms |
| GET | `/rooms/{id}` | Bearer | Get room by ID |
| POST | `/rooms/{id}/join` | Bearer | Request to join with role (`read` or `write`) |
| POST | `/rooms/{id}/approve` | Bearer (admin) | Approve a pending member |
| POST | `/rooms/{id}/reject` | Bearer (admin) | Reject a pending member |
| POST | `/rooms/{id}/promote` | Bearer (admin) | Promote member to admin |
| POST | `/rooms/{id}/leave` | Bearer | Leave room (user from token) |
| DELETE | `/rooms/{id}/members/{user_id}` | Bearer (admin) | Remove a member |
| GET | `/rooms/{id}/members` | Bearer | List all members |
| GET | `/rooms/{id}/pending` | Bearer | List pending join requests |
| GET | `/rooms/{id}/messages/` | Bearer | Paginated message history |
| DELETE | `/rooms/{id}/messages/{message_id}` | Bearer (admin) | Soft-delete a message |
| POST | `/rooms/{id}/upload` | Bearer | Upload file (creates message + document record) |
| GET | `/rooms/{id}/documents` | Bearer | List room documents |
| GET | `/documents/{file_id}` | Bearer or `?token=` | Open document (signed URL redirect or local stream) |
| GET | `/files/{filename}` | Bearer | Legacy local file endpoint |
| WS | `/ws/{room_id}?token=` | `?token=` JWT | WebSocket (messages, typing, presence) |

> `/documents/{file_id}` accepts both `Authorization: Bearer` and `?token=` query param. The `?token=` fallback is required because browser `<img>`, `<audio>`, and `<video>` tags cannot attach custom headers.

---

## Authentication Flow

```
1. POST /users/login  →  { token: "eyJ...", user: { id, name, ... } }
2. Store token in localStorage
3. All REST calls:  Authorization: Bearer <token>
4. WebSocket:       ws://.../ws/{room_id}?token=<token>
5. Media URLs:      /documents/{file_id}?token=<token>
6. Token expires after 7 days → 401 response → auto-logout + redirect to login
```

---

## WebSocket Events

**Client → Server**
```json
{ "type": "message",     "content": "hello", "reply_to": 42 }
{ "type": "typing" }
{ "type": "stop_typing" }
{ "type": "file", "message_id": 5, "file_url": "/documents/<file_id>", "filename": "photo.png" }
```

**Server → Client**
```json
{ "type": "message",      "id": 1, "sender_id": 3, "sender_name": "Alice", "content": "hello", "created_at": "...", "reply_to": 42, "reply_snippet": { ... } }
{ "type": "typing",       "user_id": 3, "user_name": "Alice" }
{ "type": "stop_typing",  "user_id": 3, "user_name": "Alice" }
{ "type": "file",         "id": 5, "sender_id": 3, "sender_name": "Alice", "file_url": "...", "filename": "..." }
{ "type": "online_users", "users": [1, 2, 3] }
{ "type": "error",        "content": "You don't have write permission in this room" }
{ "type": "message_deleted", "message_id": 100 }
{ "type": "member_removed",  "user_id": 5 }
{ "type": "kicked",          "content": "You were removed from 'general' by Alice" }
```

---

## File Storage

- Allowed extensions: images, audio, video, PDF, txt, doc/docx, csv, zip
- Max size: **10 MB** (enforced frontend and backend)
- Primary: Supabase Storage — files served via time-limited signed URLs (default 1 hour)
- Fallback: local `backend/uploads/` directory
- File access is always membership-checked — non-members cannot open documents
