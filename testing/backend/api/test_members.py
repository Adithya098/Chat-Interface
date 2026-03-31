from app.models.room_member import RoomMember


def test_join_room_creates_pending_membership(client, seed_room, seed_users, db_session):
    res = client.post(
        f"/rooms/{seed_room.id}/join",
        json={"user_id": seed_users["carol"].id, "role": "write"},
    )
    assert res.status_code == 400
    # already seeded as approved member in seed_room fixture

    dave_res = client.post(
        "/users/signup",
        json={
            "name": "Dave",
            "email": "dave@example.com",
            "password": "Passw0rd!",
            "mobile": "4444444444",
        },
    )
    dave_id = dave_res.json()["id"]
    join = client.post(f"/rooms/{seed_room.id}/join", json={"user_id": dave_id, "role": "write"})
    assert join.status_code == 201
    created = db_session.query(RoomMember).filter(RoomMember.user_id == dave_id).first()
    assert created is not None
    assert created.status == "pending"


def test_approve_and_reject_require_admin(client, seed_room, seed_users):
    pending_user = client.post(
        "/users/signup",
        json={
            "name": "Eve",
            "email": "eve@example.com",
            "password": "Passw0rd!",
            "mobile": "5555555555",
        },
    ).json()["id"]
    client.post(f"/rooms/{seed_room.id}/join", json={"user_id": pending_user, "role": "read"})

    no_admin = client.post(
        f"/rooms/{seed_room.id}/approve",
        json={"admin_id": seed_users["carol"].id, "user_id": pending_user},
    )
    assert no_admin.status_code == 403

    approved = client.post(
        f"/rooms/{seed_room.id}/approve",
        json={"admin_id": seed_users["alice"].id, "user_id": pending_user},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    pending_user2 = client.post(
        "/users/signup",
        json={
            "name": "Frank",
            "email": "frank@example.com",
            "password": "Passw0rd!",
            "mobile": "1212121212",
        },
    ).json()["id"]
    client.post(f"/rooms/{seed_room.id}/join", json={"user_id": pending_user2, "role": "read"})
    rejected = client.post(
        f"/rooms/{seed_room.id}/reject",
        json={"admin_id": seed_users["alice"].id, "user_id": pending_user2},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"


def test_last_admin_cannot_leave(client, seed_room, seed_users):
    res = client.post(f"/rooms/{seed_room.id}/leave", params={"user_id": seed_users['alice'].id})
    assert res.status_code == 400
    assert "only admin" in res.json()["detail"]
