import hashlib
import os
from fastapi import Request, Response, HTTPException
from sqlalchemy.orm import Session
from database.models import User

COOKIE_NAME = "local_dashboard_session"

def hash_password(password: str) -> str:
    """Hashes a password using SHA-256 with a static local salt helper."""
    salt = b"local_tracker_salt_6839"
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return pwd_hash.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def set_auth_cookie(response: Response, username: str):
    """Sets a secure tracking session handle cookie on the browser client."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=username,
        httponly=True,   # Shield cookie from JavaScript access vectors
        max_age=86400,   # Session expires in 1 day
        samesite="lax"
    )

def clear_auth_cookie(response: Response):
    response.delete_cookie(COOKIE_NAME)

def get_current_user(request: Request, db: Session) -> User:
    """Dependency validator confirming active session cookies match valid DB users."""
    username = request.cookies.get(COOKIE_NAME)
    if not username:
        raise HTTPException(status_code=401, detail="Session missing or expired.")
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session user context.")
    return user