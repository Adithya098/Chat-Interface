from app.routers.files import _approved_room_member
from app.routers.messages import _file_id_from_message_content as msg_file_id
from app.routers.messages import _is_image_filename as msg_is_image
from app.routers.ws import _file_id_from_message_content as ws_file_id
from app.routers.ws import _is_image_filename as ws_is_image


def test_message_file_id_helper_extracts_id():
    assert msg_file_id("/documents/abc-123") == "abc-123"
    assert msg_file_id("/documents/abc-123?x=1") == "abc-123"
    assert msg_file_id("not-a-document") is None


def test_ws_file_id_helper_extracts_id():
    assert ws_file_id("/documents/xyz") == "xyz"
    assert ws_file_id("/foo/xyz") is None


def test_image_filename_helpers():
    assert msg_is_image("photo.png") is True
    assert msg_is_image("report.pdf") is False
    assert ws_is_image("avatar.webp") is True
    assert ws_is_image("file_without_ext") is False


def test_approved_room_member_helper(db_session, seed_room, seed_users):
    writer = _approved_room_member(db_session, seed_room.id, seed_users["bob"].id, need_write=True)
    assert writer is not None

    reader = _approved_room_member(db_session, seed_room.id, seed_users["carol"].id, need_write=True)
    assert reader is None
