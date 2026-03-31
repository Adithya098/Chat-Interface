"""FastAPI application bootstrap and runtime wiring for the chat backend.

This module initializes logging filters, configures startup lifecycle tasks, 
creates database tables and lightweight migrations, 
applies CORS policy based on environment, registers all HTTP/WebSocket routers, 
and serves either the built frontend SPA or a development health message."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text
from app.database import engine, SessionLocal, Base
import app.models  # noqa: F401 — register all models (including Document) for metadata.create_all
from app.routers import users, rooms, members, ws, messages, files

# Tracks whether the database was reachable at startup
_db_healthy = False


class SuppressWebSocketLifecycleLogs(logging.Filter):
    """Filters noisy websocket lifecycle records while keeping real error logs visible."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Returns False for routine websocket connect/disconnect logs that should be suppressed."""
        message = record.getMessage()
        return not (
            ('"WebSocket ' in message and "[accepted]" in message)
            or message == "connection open"
            or message == "connection closed"
        )


# Suppress noisy websocket lifecycle logs without hiding real backend errors.
logging.getLogger("uvicorn.error").addFilter(SuppressWebSocketLifecycleLogs())
logging.getLogger("websockets.server").setLevel(logging.WARNING)

# In production, serve the React build output; in dev, use Vite dev server with proxy
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


def _run_migrations():
    """Applies lightweight startup migrations for missing columns on existing tables."""
    from sqlalchemy import text, inspect
    inspector = inspect(engine)
    if "users" in inspector.get_table_names():
        existing = {col["name"] for col in inspector.get_columns("users")}
        with engine.begin() as conn:
            if "password_hash" not in existing:
                conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
            if "mobile" not in existing:
                conn.execute(text("ALTER TABLE users ADD COLUMN mobile VARCHAR(20)"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database schema and startup migrations before serving requests."""
    global _db_healthy
    try:
        Base.metadata.create_all(bind=engine)
        _run_migrations()
        _db_healthy = True
    except Exception as e:
        _db_healthy = False
        logging.error(f"[DB] Database unreachable at startup: {e}")
        logging.warning("[DB] Server will start but all API requests will return 503 until DB is available.")
    yield


app = FastAPI(title="Chat Backend", version="1.0.0", lifespan=lifespan)

# CORS — dev often uses Vite on localhost:* while the API is on 127.0.0.1:8000 (different origins).
# Set ALLOWED_ORIGINS in production (comma-separated). Use * only if you do not need credentials.
_raw_origins = os.getenv("ALLOWED_ORIGINS", "").strip()
if _raw_origins == "*":
    allowed_origins = ["*"]
elif _raw_origins:
    allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
elif os.getenv("RENDER", "").lower() in ("true", "1", "yes") or os.getenv("DYNO"):
    # Hosted API: allow any origin unless you set ALLOWED_ORIGINS to a stricter list.
    allowed_origins = ["*"]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
    ]
_allow_credentials = "*" not in allowed_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def db_health_check(request: Request, call_next):
    """Returns 503 on all API requests when the database is not reachable."""
    is_websocket = request.headers.get("upgrade", "").lower() == "websocket"
    skip_paths = ("/assets", "/health", "/db_health")
    if not _db_healthy and not is_websocket and not any(request.url.path.startswith(p) for p in skip_paths):
        return JSONResponse(
            status_code=503,
            content={"detail": "Database connection is down. Contact Adithya."},
        )
    return await call_next(request)


@app.get("/health")
def health():
    """Returns DB status. Middleware returns 503 automatically when DB is down."""
    return {"status": "ok"}


@app.get("/db_health")
def db_health():
    """Live database connectivity check — probes the DB and updates the global health flag."""
    global _db_healthy
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            _db_healthy = True
            return {"status": "ok", "db": True}
        finally:
            db.close()
    except Exception as e:
        _db_healthy = False
        logging.warning(f"[DB] Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "db": False, "detail": "Database connection is down. Contact Adithya."},
        )


app.include_router(users.router)
app.include_router(rooms.router)
app.include_router(members.router)
app.include_router(ws.router)
app.include_router(messages.router)
app.include_router(files.router)


# Serve React build in production (after `npm run build`)
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/")
    def serve_spa():
        """Serves the built React single-page application entry HTML."""
        return FileResponse(str(FRONTEND_DIST / "index.html"))
else:
    @app.get("/")
    def root():
        """Returns a simple API health message for local development mode."""
        return {"message": "Chat Backend API is running. Start React dev server on port 3000."}
