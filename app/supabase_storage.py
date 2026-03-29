"""Supabase Storage client (service role) for server-side uploads and signed URLs."""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client

logger = logging.getLogger(__name__)

# Ensure .env is loaded before reading Supabase vars (covers import orders without app.database)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

_client: Optional[Client] = None

_PLACEHOLDER_KEYS = frozenset(
    {
        "",
        "paste_service_role_key_here",
        "your_service_role_key_here",
        "your_database_password_here",
    }
)


def _strip_value(raw: str) -> str:
    v = (raw or "").strip().lstrip("\ufeff")
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        v = v[1:-1].strip()
    return v


def _supabase_url() -> str:
    return _strip_value(os.getenv("SUPABASE_URL", ""))


def _service_role_key() -> str:
    key = _strip_value(
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_SECRET_KEY", "")
    )
    if key.lower() in _PLACEHOLDER_KEYS:
        return ""
    return key


def get_supabase() -> Optional[Client]:
    global _client
    url = _supabase_url()
    key = _service_role_key()
    if not url or not key:
        return None
    if _client is None:
        try:
            _client = create_client(url, key)
        except Exception as e:
            logger.exception("Supabase create_client failed: %s", e)
            return None
    return _client


def reset_supabase_client() -> None:
    """Clear cached client (e.g. after env change in tests)."""
    global _client
    _client = None


def storage_bucket_name() -> str:
    # If SUPABASE_STORAGE_BUCKET exists but is empty, getenv returns "" — still use default
    raw = os.getenv("SUPABASE_STORAGE_BUCKET")
    name = _strip_value(raw) if raw is not None else ""
    return name or "chat-documents"


def storage_env_ready() -> bool:
    """True when URL + service key are set (client may still fail to connect)."""
    return bool(_supabase_url() and _service_role_key())


def storage_configured() -> bool:
    """True when we can obtain a Storage client and have a non-empty bucket name."""
    if not storage_env_ready():
        return False
    bucket = storage_bucket_name()
    if not bucket:
        return False
    return get_supabase() is not None


def why_storage_disabled() -> str:
    if not _supabase_url():
        return "SUPABASE_URL is missing or empty"
    if not _service_role_key():
        return "SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_SECRET_KEY) is missing, empty, or still a placeholder"
    if not storage_bucket_name():
        return "SUPABASE_STORAGE_BUCKET is empty"
    if get_supabase() is None:
        return "Supabase client failed to initialize (check URL/key and logs)"
    return "unknown"


def upload_bytes(
    bucket: str,
    object_path: str,
    data: bytes,
    content_type: Optional[str],
) -> None:
    client = get_supabase()
    if not client:
        raise RuntimeError("Supabase client not configured")
    opts = {
        "content-type": content_type or "application/octet-stream",
        "upsert": "true",
    }
    client.storage.from_(bucket).upload(object_path, data, file_options=opts)


def signed_download_url(bucket: str, object_path: str, expires_in: int) -> str:
    client = get_supabase()
    if not client:
        raise RuntimeError("Supabase client not configured")
    out = client.storage.from_(bucket).create_signed_url(object_path, expires_in)
    return out.get("signedURL") or out.get("signedUrl") or ""


def public_object_url(bucket: str, object_path: str) -> str:
    client = get_supabase()
    if not client:
        raise RuntimeError("Supabase client not configured")
    return client.storage.from_(bucket).get_public_url(object_path)
