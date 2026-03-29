"""
Insert demo users, rooms, members, messages, and documents.
Idempotent: skips if demo user alice@chat-demo.local already exists.

Run from backend/ (so package app resolves):
  cd backend && python -m scripts.seed_dummy_data
"""
import uuid

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Document, Message, Room, RoomMember, User

DEMO_EMAIL = "alice@chat-demo.local"


def seed():
    db = SessionLocal()
    try:
        if db.execute(select(User).where(User.email == DEMO_EMAIL)).scalar_one_or_none():
            print("Dummy data already present (found %s). Skipping." % DEMO_EMAIL)
            return

        u_alice = User(name="Alice Chen", email=DEMO_EMAIL)
        u_bob = User(name="Bob Martinez", email="bob@chat-demo.local")
        u_carol = User(name="Carol Singh", email="carol@chat-demo.local")
        db.add_all([u_alice, u_bob, u_carol])
        db.flush()

        r_general = Room(name="General", created_by=u_alice.id)
        r_random = Room(name="Random", created_by=u_bob.id)
        r_private = Room(name="Team Alpha", created_by=u_alice.id)
        db.add_all([r_general, r_random, r_private])
        db.flush()

        members = [
            RoomMember(user_id=u_alice.id, room_id=r_general.id, role="admin", status="approved"),
            RoomMember(user_id=u_bob.id, room_id=r_general.id, role="write", status="approved"),
            RoomMember(user_id=u_carol.id, room_id=r_general.id, role="write", status="approved"),
            RoomMember(user_id=u_bob.id, room_id=r_random.id, role="admin", status="approved"),
            RoomMember(user_id=u_carol.id, room_id=r_random.id, role="write", status="approved"),
            RoomMember(user_id=u_alice.id, room_id=r_private.id, role="admin", status="approved"),
            RoomMember(user_id=u_bob.id, room_id=r_private.id, role="write", status="pending"),
        ]
        db.add_all(members)

        messages = [
            Message(
                room_id=r_general.id,
                sender_id=u_alice.id,
                type="text",
                content="Hey everyone — welcome to the demo chat.",
            ),
            Message(
                room_id=r_general.id,
                sender_id=u_bob.id,
                type="text",
                content="Thanks Alice! Excited to try this out.",
            ),
            Message(
                room_id=r_general.id,
                sender_id=u_carol.id,
                type="text",
                content="Same here. Does this support file uploads?",
            ),
            Message(
                room_id=r_random.id,
                sender_id=u_bob.id,
                type="text",
                content="Random thought: coffee > tea for morning deploys.",
            ),
            Message(
                room_id=r_random.id,
                sender_id=u_carol.id,
                type="text",
                content="Bold take. I’ll allow it.",
            ),
        ]
        db.add_all(messages)

        fid1, fid2 = str(uuid.uuid4()), str(uuid.uuid4())
        docs = [
            Document(
                file_id=fid1,
                room_id=r_general.id,
                sender_id=u_alice.id,
                original_filename="spec-notes.txt",
                storage_bucket=None,
                storage_path=None,
                storage_public_url=None,
            ),
            Document(
                file_id=fid2,
                room_id=r_private.id,
                sender_id=u_alice.id,
                original_filename="wireframe-draft.png",
                storage_bucket="chat-documents",
                storage_path="uploads/demo/wireframe-draft.png",
                storage_public_url="https://example.com/dummy/wireframe-draft.png",
            ),
        ]
        db.add_all(docs)

        db.commit()
        print(
            "Seeded: 3 users, 3 rooms, 7 memberships, 5 messages, 2 documents "
            "(demo marker: %s)." % DEMO_EMAIL
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
