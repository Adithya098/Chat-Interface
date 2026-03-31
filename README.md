# Chat Interface

Real-time room-based chat system built with FastAPI, WebSockets, React, and PostgreSQL, with optional Supabase Storage for files.

## Features

### Implemented Features

#### Authentication and User Session
- **Authentication**: Secure signup/login with bcrypt password hashing, mobile number field
- **Session persistence**: signed-in user is restored from local storage
- **Input validation**: required fields and password minimum checks on signup

---

#### Room Access and Membership
- **Role-based room access** (`admin` / `write` / `read`)
- **Join requests** with admin approve/reject flow (request any role: read, write, or admin)
- **Admin request inbox** with grouped pending requests and badges
- **Member management**: promote members, remove members, and prevent last-admin removal
- **Real-time messaging** over WebSocket with message replies (quoted preview + scroll-to-original)
- **Room management**: users can leave voluntarily, last admin protection

---

#### Messaging and Realtime Collaboration
- **Typing indicators** with 3-second graceful fade (real-time updates)
- **Room presence** (`online_users` count)
- **Admin moderation**: soft-delete messages with real-time deletion broadcast
- **Custom toast + confirm UX** instead of native browser alerts/confirms
- **Safer send UX**: message input is preserved and a toast is shown if websocket is not open

---

#### File and Document Handling
- **File uploads** (images, PDFs, docs)
- **Upload guardrails**: hard `10 MB` max with frontend pre-check and backend enforcement
- **Oversize feedback**: toast includes selected file size (for example, `12.7MB > 10MB`)
- **Document center**: room-scoped document listing + secure open/download links
- **Dual storage support**: Supabase Storage (signed URLs) with local-disk fallback

---

#### API and Data Flow
- **Message history** via REST API (sender names, reply snippets, file metadata)
- **Role-aware authorization** enforced on REST and WebSocket endpoints
- **Auto-refresh UX**: room/member/admin-request state refresh on focus, visibility change, and intervals


---



### Enhanced Authentication
- Replaced old auto-create user flow with separate **Signup** and **Login** flows
- Signup now requires `name`, `email`, `mobile`, and `password`
- Login now uses `email` + `password` only
- Passwords are securely hashed with **bcrypt** before storing
- Added startup auto-migration for `users.password_hash` and `users.mobile` columns

---

### Leave Room
- Users can voluntarily leave any room they're a member of
- Non-destructive: can rejoin later if invited
- Safety: last admin cannot leave (prevents orphaned rooms)
- Button location: Room header (top-right, red button)

---

### Admin Promotion
- Room admins can promote existing non-admin members to admin role
- Requires confirmation dialog
- New admin gains full room management permissions
- Broadcast notification sent to room

---

### Join Request Roles
- Users can now request to join as any role: `read`, `write`, or `admin`
- Admin role requests require admin approval (same as other roles)
- Clear labeling in join modal (admin option highlighted in orange)
- Admins approve/reject in Members panel

---

### Admin Join Request Inbox
- Admins see pending join requests grouped by room in a dedicated modal
- Sidebar shows total pending request count plus per-room pending badges
- New incoming requests can auto-open moderation modal for faster approvals

---

### Message and Moderation Improvements
- Reply-to support with quoted preview and scroll-to-original behavior
- File replies now render friendly previews:
  - image replies show a thumbnail in the quote block
  - non-image file replies show filename instead of raw `/documents/...` path
- Admin message deletion uses **soft delete**:
  - deleted messages are hidden from normal room history
  - replies keep `reply_to` references, so quoted reply preview still works after deletion
  - clicking a quote whose original message is hidden/deleted shows **"Message not found"**
- Real-time deletion broadcast (`message_deleted`) updates clients immediately
- Safer member removal flow with kick notice and room-wide update broadcast

---

### File and Document Flow
- Upload creates both a `Document` record and a corresponding chat file message
- Room members can list room documents via REST and open by stable `file_id`
- Storage backend supports Supabase signed URLs with local-disk fallback

---

## Role Permissions

| Role | Read | Send | Reply | Upload | Approve/Reject Requests | Delete Messages | Remove Members | Promote Members | Leave Room |
|------|------|------|-------|--------|------------------------|-----------------|----------------|-----------------|------------|
| `admin` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (if not last admin) | ✓ | ✓ (if not last admin) |
| `write` | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ |
| `read` | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |

---

## Tech Stack

- **FastAPI** — API + WebSocket server
- **SQLAlchemy** — ORM
- **PostgreSQL** — persistent storage
- **Supabase Storage (optional)** — document/file storage with signed URLs
- **React + Vite** — frontend client
- **bcrypt** — password hashing
- **Render** — hosting

---

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

---

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

Run one-time backend migration scripts (if needed after pulling new changes):

```bash
python backend/scripts/add_reply_to_column.py
python backend/scripts/add_is_deleted_to_messages.py
```

- Open the URL Vite prints (default **http://localhost:3000**). In dev, HTTP requests are proxied and WebSocket connects to **127.0.0.1:8000**.
- API docs: http://localhost:8000/docs

**Backend only** (serves built `frontend/dist` if present):

```bash
cd backend && python -m uvicorn app.main:app --reload --no-access-log
```

---

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/signup` | Register a new user (name, email, mobile, password) |
| POST | `/users/login` | Authenticate existing user (email, password) |
| GET | `/users/` | List users |
| GET | `/users/{user_id}` | Get user by ID |
| POST | `/rooms/` | Create room |
| POST | `/rooms/{id}/join` | Request to join (role: read, write, or admin) |
| POST | `/rooms/{id}/approve` | Admin approves member request |
| POST | `/rooms/{id}/reject` | Admin rejects member request |
| POST | `/rooms/{id}/promote` | Admin promotes member to admin |
| POST | `/rooms/{id}/leave` | User leaves room |
| DELETE | `/rooms/{id}/members/{user_id}?admin_id={id}` | Admin removes member |
| GET | `/rooms/{id}/members` | List all members |
| GET | `/rooms/{id}/pending` | List pending join requests |
| GET | `/rooms/{id}/messages/` | Message history |
| DELETE | `/rooms/{id}/messages/{message_id}?admin_id={id}` | Admin soft-deletes message (hidden from history) |
| POST | `/rooms/{id}/upload` | Upload file (creates message + document record) |
| GET | `/rooms/{id}/documents?user_id={id}` | List room documents |
| GET | `/documents/{file_id}?user_id={id}` | Open document (signed URL redirect or local file) |
| GET | `/files/{filename}` | Legacy local file endpoint |
| WS | `/ws/{room_id}?user_id=` | WebSocket (messages, typing, presence) |

---

## Authentication Notes

- Passwords are hashed with `bcrypt` (salted hash) and never stored as plaintext
- Email is normalized before lookup/creation to prevent duplicate variants
- Login returns `401` for invalid credentials
- Signup returns `400` when email is already registered

---

## File Storage Notes

- Upload limits: allowed extensions are enforced and max size is `10 MB`
- Primary backend: Supabase Storage when `SUPABASE_URL` + service key + bucket are configured
- Fallback backend: local `backend/uploads` storage when Supabase is unavailable
- Document opens use signed URLs for protected Supabase objects
- Optional public URL mode is supported via `SUPABASE_STORAGE_PUBLIC_URLS`

---

## WebSocket Events

**Client → Server**
```json
{ "type": "message",     "content": "hello", "reply_to": 42 }
{ "type": "typing" }
{ "type": "stop_typing" }
{ "type": "file",        "message_id": 5, "file_url": "/documents/<file_id>", "filename": "photo.png" }
```

**Server → Client**
```json
{ "type": "message",     "id": 1, "sender_id": 3, "sender_name": "Alice", "content": "hello", "created_at": "...", "reply_to": 42, "reply_snippet": { "id": 42, "sender_name": "Bob", "content": "photo.png", "type": "file", "filename": "photo.png", "file_url": "/documents/<file_id>", "is_image": true } }
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

