import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker, declarative_base

# Repo root: backend/app -> .. -> backend -> ..
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


def _database_url():
    """
    Prefer DB_* vars so passwords with @, :, [, ] etc. are not parsed as URL delimiters.
    Otherwise use DATABASE_URL (password must be URL-encoded if it contains reserved chars).
    """
    user = os.getenv("DB_USER")
    host = os.getenv("DB_HOST")
    password = os.getenv("DB_PASSWORD")
    if user and host and password is not None:
        port = int(os.getenv("DB_PORT", "5432"))
        database = os.getenv("DB_NAME", "postgres")
        sslmode = os.getenv("DB_SSLMODE", "require")
        query = {"sslmode": sslmode} if sslmode else {}
        return URL.create(
            "postgresql+psycopg2",
            username=user,
            password=password,
            host=host,
            port=port,
            database=database,
            query=query,
        )
    return os.getenv("DATABASE_URL", "postgresql://localhost:5432/chatdb")


engine = create_engine(
    _database_url(),
    pool_pre_ping=True,
    connect_args={"connect_timeout": 15},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
