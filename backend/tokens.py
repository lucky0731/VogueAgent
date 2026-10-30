"""
Signed login tokens (stdlib only — HMAC-SHA256 over a small JSON payload).

A token looks like ``<payload>.<signature>``, both base64url. The payload holds
the user id, an expiry, and the user's ``token_version``. Bumping a user's
``token_version`` (done on password/email change) instantly invalidates every
token issued before it, so changing your password logs out other devices.
"""
import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from pathlib import Path

from .config import settings

log = logging.getLogger("uvicorn.error")

_SECRET_FILE = Path(__file__).resolve().parent.parent / ".secret_key"


def _load_secret() -> bytes:
    if settings.secret_key:
        return settings.secret_key.encode("utf-8")
    # Local development fallback: generate once, keep it in a git-ignored file
    # so logins survive server restarts.
    try:
        if _SECRET_FILE.exists():
            return _SECRET_FILE.read_text(encoding="utf-8").strip().encode("utf-8")
        key = secrets.token_urlsafe(48)
        _SECRET_FILE.write_text(key, encoding="utf-8")
        log.warning("SECRET_KEY not set; generated one in .secret_key (set SECRET_KEY in production).")
        return key.encode("utf-8")
    except OSError:
        log.warning("SECRET_KEY not set and .secret_key not writable; logins reset on every restart.")
        return secrets.token_bytes(48)


_SECRET = _load_secret()


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(payload: str) -> str:
    return _b64encode(hmac.new(_SECRET, payload.encode("ascii"), hashlib.sha256).digest())


def create_token(user: dict) -> str:
    """Issue a token for a MongoDB user document."""
    payload = _b64encode(json.dumps({
        "sub": str(user["_id"]),
        "ver": int(user.get("token_version", 0)),
        "exp": int(time.time()) + settings.token_ttl_hours * 3600,
    }, separators=(",", ":")).encode("utf-8"))
    return f"{payload}.{_sign(payload)}"


def read_token(token: str) -> dict | None:
    """Return the token's claims if the signature is valid and it hasn't expired, else None."""
    try:
        payload, signature = token.split(".", 1)
    except (AttributeError, ValueError):
        return None
    if not hmac.compare_digest(signature, _sign(payload)):
        return None
    try:
        claims = json.loads(_b64decode(payload))
    except (ValueError, json.JSONDecodeError):
        return None
    if claims.get("exp", 0) < time.time():
        return None
    return claims
