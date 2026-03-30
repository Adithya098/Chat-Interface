"""User account endpoints for registration, authentication, and lookup operations.

This module hashes and verifies passwords with bcrypt, 
validates uniqueness constraints at signup, authenticates login attempts, 
and exposes user listing/detail routes used by internal room/member UI flows."""

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserSignup, UserLogin, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


def _hash_password(password: str) -> str:
    """Generates a bcrypt hash for a plaintext password before persistence."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    """Compares a plaintext password against a stored bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(req: UserSignup, db: Session = Depends(get_db)):
    """Registers a new user account after email uniqueness and input normalization checks."""
    normalized_email = str(req.email).strip().lower()

    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        name=req.name.strip(),
        email=normalized_email,
        password_hash=_hash_password(req.password),
        mobile=req.mobile.strip(),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=UserResponse)
def login(req: UserLogin, db: Session = Depends(get_db)):
    """Authenticates a user by email and password and returns the matching account."""
    normalized_email = str(req.email).strip().lower()

    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.password_hash:
        raise HTTPException(status_code=401, detail="Account has no password. Please sign up again.")

    if not _verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return user


# Keep these for internal use (members panel name resolution, etc.)
@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    """Returns all user records for internal and administrative consumption."""
    return db.query(User).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Returns a single user by ID or raises not found when absent."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
