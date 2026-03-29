"""One-time migration: add reply_to column to messages table."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check if column already exists
    result = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'messages' AND column_name = 'reply_to'"
    ))
    if result.fetchone():
        print("Column reply_to already exists, skipping.")
    else:
        conn.execute(text(
            "ALTER TABLE messages ADD COLUMN reply_to INTEGER REFERENCES messages(id) DEFAULT NULL"
        ))
        conn.commit()
        print("Added reply_to column to messages table.")
