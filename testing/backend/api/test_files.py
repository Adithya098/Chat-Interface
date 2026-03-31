import io
from app.models.document import Document


def test_upload_rejects_disallowed_extension(client, seed_room, seed_users):
    files = {"file": ("bad.exe", io.BytesIO(b"abc"), "application/octet-stream")}
    data = {"user_id": str(seed_users["bob"].id)}
    res = client.post(f"/rooms/{seed_room.id}/upload", data=data, files=files)
    assert res.status_code == 400
    assert "not allowed" in res.json()["detail"]


def test_upload_requires_write_permission(client, seed_room, seed_users):
    files = {"file": ("ok.txt", io.BytesIO(b"abc"), "text/plain")}
    data = {"user_id": str(seed_users["carol"].id)}  # read-only member
    res = client.post(f"/rooms/{seed_room.id}/upload", data=data, files=files)
    assert res.status_code == 403


def test_list_documents_requires_membership(client, seed_room):
    res = client.get(f"/rooms/{seed_room.id}/documents", params={"user_id": 99999})
    assert res.status_code == 403


def test_open_document_forbidden_for_non_member(client, db_session, seed_room, seed_users):
    doc = Document(
        file_id="doc-forbidden",
        room_id=seed_room.id,
        sender_id=seed_users["alice"].id,
        original_filename="note.txt",
    )
    db_session.add(doc)
    db_session.commit()

    res = client.get("/documents/doc-forbidden", params={"user_id": 99999})
    assert res.status_code == 403
