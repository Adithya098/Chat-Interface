from app import supabase_storage


def test_strip_value_normalizes_quotes_and_bom():
    assert supabase_storage._strip_value("  'abc'  ") == "abc"
    assert supabase_storage._strip_value('\ufeff"x"') == "x"


def test_service_role_key_rejects_placeholders(monkeypatch):
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "paste_service_role_key_here")
    assert supabase_storage._service_role_key() == ""


def test_storage_bucket_name_defaults_when_empty(monkeypatch):
    monkeypatch.setenv("SUPABASE_STORAGE_BUCKET", "")
    assert supabase_storage.storage_bucket_name() == "chat-documents"
