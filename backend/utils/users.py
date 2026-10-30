"""
Shared shaping and validation of user accounts.
"""
import re

from fastapi import HTTPException

from ..tokens import create_token
from .images import to_data_url

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")


def public_user(user: dict) -> dict:
    """Shape a MongoDB user document for API responses (never leak password_hash)."""
    avatar = None
    if user.get("avatar_data") and user.get("avatar_content_type"):
        avatar = to_data_url(user["avatar_data"], user["avatar_content_type"])
    return {
        "username": user["username"],
        "email": user["email"],
        "avatar": avatar,
        "is_admin": bool(user.get("is_admin")),
        "has_password": bool(user.get("password_hash")),
        "auth_provider": user.get("auth_provider", "password"),
    }


def auth_response(user: dict, message: str) -> dict:
    """Public profile plus a fresh login token."""
    return {"message": message, "token": create_token(user), **public_user(user)}


def validate_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email) or len(email) > 254:
        raise HTTPException(status_code=400, detail="Please enter a valid email address")
    return email


def validate_username(username: str) -> str:
    username = (username or "").strip()
    if not USERNAME_RE.match(username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3–30 characters: letters, numbers, dot, dash or underscore",
        )
    return username


def validate_password(password: str, label: str = "Password") -> str:
    if len(password or "") < 6:
        raise HTTPException(status_code=400, detail=f"{label} must be at least 6 characters")
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail=f"{label} must be at most 72 bytes")
    return password
