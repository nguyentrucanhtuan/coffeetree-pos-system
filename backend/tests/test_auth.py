"""Tests: login, /me, set-password flows."""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_header, login_user


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, superuser):
    """Login with correct credentials returns tokens + user info."""
    resp = await client.post("/auth/login", json={
        "email": "admin@test.com",
        "password": "admin123456",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["user"]["email"] == "admin@test.com"
    assert data["data"]["user"]["is_superuser"] is True


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, superuser):
    """Wrong password returns 401."""
    resp = await client.post("/auth/login", json={
        "email": "admin@test.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, db_session):
    """Inactive user returns 403."""
    from auth.models import User
    from auth.utils import hash_password

    user = User(
        email="inactive@test.com",
        password_hash=hash_password("password123"),
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post("/auth/login", json={
        "email": "inactive@test.com",
        "password": "password123",
    })
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient, superuser):
    """GET /auth/me returns user info when authenticated."""
    tokens = await login_user(client, "admin@test.com", "admin123456")
    resp = await client.get("/auth/me", headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["email"] == "admin@test.com"


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    """GET /auth/me without token returns 401."""
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_set_password_success(client: AsyncClient, superuser):
    """Change password with correct current password."""
    tokens = await login_user(client, "admin@test.com", "admin123456")

    resp = await client.post("/auth/set-password", json={
        "current_password": "admin123456",
        "new_password": "newpassword123",
    }, headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 200

    # Login with new password
    resp2 = await client.post("/auth/login", json={
        "email": "admin@test.com",
        "password": "newpassword123",
    })
    assert resp2.status_code == 200


@pytest.mark.asyncio
async def test_set_password_wrong_current(client: AsyncClient, superuser):
    """Wrong current password returns 400."""
    tokens = await login_user(client, "admin@test.com", "admin123456")

    resp = await client.post("/auth/set-password", json={
        "current_password": "wrongpassword",
        "new_password": "newpassword123",
    }, headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 400
