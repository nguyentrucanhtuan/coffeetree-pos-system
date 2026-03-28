"""JWT, password hashing, and token utilities."""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings


# ─── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(
    user_id: int,
    email: str,
    is_superuser: bool,
    group_ids: list[int],
) -> str:
    """Create a short-lived access token (30 min default)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "is_superuser": is_superuser,
        "group_ids": group_ids,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    """Create a long-lived refresh token. Returns (token_str, jti, expires_at)."""
    now = datetime.now(timezone.utc)
    jti = uuid.uuid4().hex
    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": expires_at,
        "jti": jti,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expires_at


def create_verify_email_token(user_id: int) -> str:
    """Create a JWT for email verification (24h)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "verify-email",
        "iat": now,
        "exp": now + timedelta(hours=24),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises jwt.PyJWTError on failure."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "exp", "iat", "type"]},
    )


# ─── Password Hashing ─────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ─── Reset Token ──────────────────────────────────────────────────────────────

def generate_reset_token() -> tuple[str, str]:
    """Generate a UUID reset token. Returns (plaintext_token, sha256_hash)."""
    token = uuid.uuid4().hex
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return token, token_hash


def hash_token(token: str) -> str:
    """Hash a token with SHA-256."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
