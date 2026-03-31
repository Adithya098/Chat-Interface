"""One-time migration: add is_deleted column to messages table."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'messages' AND column_name = 'is_deleted'"
    ))
    if result.fetchone():
        print("Column is_deleted already exists, skipping.")
    else:
        conn.execute(text(
            "ALTER TABLE messages "
            "ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        conn.commit()
        print("Added is_deleted column to messages table.")
