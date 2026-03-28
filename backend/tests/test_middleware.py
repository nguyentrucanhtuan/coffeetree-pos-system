"""Tests: JWT middleware — type check, expired token, no token."""

import pytest
from httpx import AsyncClient

from auth.utils import create_access_token, create_refresh_token
from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_refresh_token_rejected_as_access(client: AsyncClient, superuser):
    """Middleware MUST reject refresh token used as access token."""
    _, jti, _ = create_refresh_token(superuser.id)
    # Build a refresh token manually
    import jwt as pyjwt
    from app.config import settings
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    refresh_payload = {
        "sub": str(superuser.id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=30),
        "jti": jti,
    }
    refresh_token = pyjwt.encode(
        refresh_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    # Try to use refresh token as access token for /auth/me
    resp = await client.get("/auth/me", headers=auth_header(refresh_token))
    assert resp.status_code == 401  # Should be rejected


@pytest.mark.asyncio
async def test_expired_token_rejected(client: AsyncClient):
    """Expired access token is rejected."""
    import jwt as pyjwt
    from app.config import settings
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    expired_payload = {
        "sub": "1",
        "type": "access",
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),  # Already expired
        "jti": "test-expired",
        "email": "test@test.com",
        "is_superuser": False,
        "group_ids": [],
    }
    expired_token = pyjwt.encode(
        expired_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    resp = await client.get("/auth/me", headers=auth_header(expired_token))
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_no_token_public_path(client: AsyncClient):
    """Public paths work without token."""
    resp = await client.get("/docs")
    # docs redirect or 200
    assert resp.status_code in (200, 307)


@pytest.mark.asyncio
async def test_valid_access_token_works(client: AsyncClient, superuser):
    """Valid access token properly injects request.state."""
    token = create_access_token(
        user_id=superuser.id,
        email=superuser.email,
        is_superuser=superuser.is_superuser,
        group_ids=[],
    )

    resp = await client.get("/auth/me", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == "admin@test.com"
