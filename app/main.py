import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import users, rooms, members, ws, messages, files


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (only when DB is reachable)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Chat Backend", version="1.0.0", lifespan=lifespan)

# CORS — allow all in dev, restrict in production via env var
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(rooms.router)
app.include_router(members.router)
app.include_router(ws.router)
app.include_router(messages.router)
app.include_router(files.router)


@app.get("/")
def root():
    return {"message": "Chat Backend API is running"}
