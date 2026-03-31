"""JWT authentication utilities for token creation and request identity verification.

This module provides token generation, a standard Bearer-header dependency,
and a flexible header-or-query-param dependency for media endpoints where
browser img/audio/video tags cannot send Authorization headers."""

import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE-ME-IN-PRODUCTION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

_bearer = HTTPBearer(auto_error=False)


def create_access_token(user_id: int) -> str:
    """Creates a signed JWT encoding the user ID with a fixed expiry."""
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> int | None:
    """Returns the user_id integer from a valid token, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except (JWTError, ValueError):
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency: validates Authorization: Bearer <token> and returns the user."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise exc
    user_id = _decode_token(credentials.credentials)
    if user_id is None:
        raise exc
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise exc
    return user


def get_current_user_flexible(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Accepts Bearer header OR ?token= query param.

    Used for document/media endpoints where <img src> and <audio src> tags
    cannot attach an Authorization header — the token is embedded in the URL instead."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    raw = (credentials.credentials if credentials else None) or token
    if not raw:
        raise exc
    user_id = _decode_token(raw)
    if user_id is None:
        raise exc
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise exc
    return user
