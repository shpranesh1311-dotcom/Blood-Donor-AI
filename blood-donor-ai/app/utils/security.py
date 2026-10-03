"""
security.py
============
Minimal demo authentication helpers.

- Passwords are hashed with bcrypt directly - never stored in plaintext.
  (We call the `bcrypt` library directly rather than through passlib to
  avoid a known passlib/bcrypt version-compatibility issue.)
- Sessions are simple signed cookies for demo purposes only. This is NOT a
  production-grade auth system; a real deployment would need proper session
  management, HTTPS, CSRF protection, rate limiting, etc.
"""

import hashlib
import hmac
import time
import bcrypt

from app import config

# bcrypt has a hard 72-byte input limit; truncate defensively (this only
# affects extremely long demo passwords, not normal use).
_MAX_PASSWORD_BYTES = 72


def hash_password(plain_password: str) -> str:
    pw_bytes = plain_password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pw_bytes = plain_password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    try:
        return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))
    except ValueError:
        return False


def _sign(value: str) -> str:
    return hmac.new(config.SECRET_KEY.encode(), value.encode(), hashlib.sha256).hexdigest()


def create_session_token(username: str, ttl_seconds: int = 3600 * 8) -> str:
    expiry = int(time.time()) + ttl_seconds
    payload = f"{username}:{expiry}"
    signature = _sign(payload)
    return f"{payload}:{signature}"


def verify_session_token(token: str):
    """Returns the username if the token is valid and not expired, else None."""
    try:
        username, expiry, signature = token.split(":")
    except (ValueError, AttributeError):
        return None
    payload = f"{username}:{expiry}"
    if not hmac.compare_digest(_sign(payload), signature):
        return None
    if int(expiry) < time.time():
        return None
    return username
