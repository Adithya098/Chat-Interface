def test_create_room_success(client, seed_users):
    res = client.post(
        "/rooms/",
        json={"name": "Project Room", "created_by": seed_users["alice"].id},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Project Room"
    assert body["created_by"] == seed_users["alice"].id


def test_create_room_missing_creator_fails(client):
    res = client.post("/rooms/", json={"name": "Broken", "created_by": 99999})
    assert res.status_code == 404
    assert "Creator user not found" in res.json()["detail"]


def test_list_rooms_returns_created_room(client, seed_users):
    create = client.post(
        "/rooms/",
        json={"name": "Listable Room", "created_by": seed_users["alice"].id},
    )
    assert create.status_code == 201
    res = client.get("/rooms/")
    assert res.status_code == 200
    names = [room["name"] for room in res.json()]
    assert "Listable Room" in names


def test_get_room_not_found(client):
    res = client.get("/rooms/404404")
    assert res.status_code == 404
    assert "Room not found" in res.json()["detail"]
