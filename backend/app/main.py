import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine, Base
import app.models  # noqa: F401 — register all models (including Document) for metadata.create_all
from app.routers import users, rooms, members, ws, messages, files

# In production, serve the React build output; in dev, use Vite dev server with proxy
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (only when DB is reachable)
    Base.metadata.create_all(bind=engine)
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
        return FileResponse(str(FRONTEND_DIST / "index.html"))
else:
    @app.get("/")
    def root():
        return {"message": "Chat Backend API is running. Start React dev server on port 3000."}
