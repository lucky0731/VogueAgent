"""
Request authentication.

Every logged-in request carries ``Authorization: Bearer <token>``. The token is
signed by the server (see tokens.py), so the client can't forge or alter it —
unlike the old scheme, which trusted a client-supplied email address.

Admin rights are an ``is_admin`` flag on the user's MongoDB document. Nothing in
the web app can set it; use ``python -m backend.make_admin <email>``.
"""
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, Header, HTTPException

from .database import users_collection
from .tokens import read_token


def _user_from_header(authorization: str | None) -> dict | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    claims = read_token(authorization.split(" ", 1)[1].strip())
    if not claims:
        return None
    try:
        user = users_collection.find_one({"_id": ObjectId(claims["sub"])})
    except (InvalidId, KeyError, TypeError):
        return None
    if not user or int(user.get("token_version", 0)) != claims.get("ver"):
        return None  # account deleted, or password/email changed since the token was issued
    return user


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    """FastAPI dependency: the logged-in user's document, or 401."""
    user = _user_from_header(authorization)
    if user is None:
        raise HTTPException(status_code=401, detail="Please log in to continue.")
    return user


def get_optional_user(authorization: str | None = Header(default=None)) -> dict | None:
    """FastAPI dependency: the logged-in user's document, or None for guests."""
    return _user_from_header(authorization)


def is_admin(user: dict | None) -> bool:
    return bool(user and user.get("is_admin"))


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """FastAPI dependency guarding admin-only routes."""
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
