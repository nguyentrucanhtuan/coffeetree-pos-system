"""Tests: register, verify-email, forgot-password, reset-password flows."""

import pytest
from httpx import AsyncClient
from unittest.mock import patch

from tests.conftest import auth_header, login_user


@pytest.mark.asyncio
async def test_register_disabled_by_default(client: AsyncClient):
    """POST /auth/register returns 403 when ALLOW_PUBLIC_REGISTER=false."""
    resp = await client.post("/auth/register", json={
        "email": "new@test.com",
        "password": "password123",
    })
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Register works when enabled."""
    with patch("app.config.settings.ALLOW_PUBLIC_REGISTER", True):
        with patch("auth.router.settings.ALLOW_PUBLIC_REGISTER", True):
            resp = await client.post("/auth/register", json={
                "email": "newuser@test.com",
                "password": "password12345",
                "full_name": "New User",
            })
            assert resp.status_code == 201
            assert resp.json()["data"]["email"] == "newuser@test.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, superuser):
    """Duplicate email on register returns 409."""
    with patch("app.config.settings.ALLOW_PUBLIC_REGISTER", True):
        with patch("auth.router.settings.ALLOW_PUBLIC_REGISTER", True):
            resp = await client.post("/auth/register", json={
                "email": "admin@test.com",
                "password": "password123",
            })
            assert resp.status_code == 409


@pytest.mark.asyncio
async def test_forgot_password_always_200(client: AsyncClient):
    """POST /auth/forgot-password always returns 200 (no email leak)."""
    resp = await client.post("/auth/forgot-password", json={
        "email": "nonexistent@test.com",
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_forgot_and_reset_flow(client: AsyncClient, superuser, db_session):
    """End-to-end forgot → reset → login with new password."""
    # Trigger forgot password
    resp = await client.post("/auth/forgot-password", json={
        "email": "admin@test.com",
    })
    assert resp.status_code == 200

    # Get token from DB (in real flow, user gets it from email)
    from sqlalchemy import select
    from auth.models import User

    result = await db_session.execute(select(User).where(User.email == "admin@test.com"))
    user = result.scalar_one()

    # We need the plaintext token — in real flow it goes via email
    # For testing, generate a known token and set its hash
    from auth.utils import hash_token
    test_token = "test-reset-token-12345"
    user.password_reset_token = hash_token(test_token)
    from datetime import datetime, timezone
    user.password_reset_at = datetime.now(timezone.utc)
    await db_session.commit()

    # Reset password
    resp2 = await client.post("/auth/reset-password", json={
        "token": test_token,
        "new_password": "brandnewpassword",
    })
    assert resp2.status_code == 200

    # Login with new password
    resp3 = await client.post("/auth/login", json={
        "email": "admin@test.com",
        "password": "brandnewpassword",
    })
    assert resp3.status_code == 200


@pytest.mark.asyncio
async def test_reset_invalid_token(client: AsyncClient):
    """Invalid reset token returns 400."""
    resp = await client.post("/auth/reset-password", json={
        "token": "invalid-token",
        "new_password": "newpassword123",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_verify_email_invalid_token(client: AsyncClient):
    """Invalid verify token returns 400."""
    resp = await client.post("/auth/verify-email", json={
        "token": "invalid-jwt-token",
    })
    assert resp.status_code == 400
