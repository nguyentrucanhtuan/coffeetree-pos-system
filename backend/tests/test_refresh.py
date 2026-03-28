"""Tests: refresh token flow — refresh, revoke, logout."""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_header, login_user


@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient, superuser):
    """Refresh with valid token returns new access_token."""
    tokens = await login_user(client, "admin@test.com", "admin123456")

    resp = await client.post("/auth/refresh", json={
        "refresh_token": tokens["refresh_token"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "access_token" in data["data"]


@pytest.mark.asyncio
async def test_refresh_after_logout_fails(client: AsyncClient, superuser):
    """After logout, refresh token should be revoked."""
    tokens = await login_user(client, "admin@test.com", "admin123456")

    # Logout
    resp = await client.post("/auth/logout", json={
        "refresh_token": tokens["refresh_token"],
    }, headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 200

    # Try to refresh with revoked token
    resp2 = await client.post("/auth/refresh", json={
        "refresh_token": tokens["refresh_token"],
    })
    assert resp2.status_code == 401


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    """Invalid refresh token returns 401."""
    resp = await client.post("/auth/refresh", json={
        "refresh_token": "invalid-token-string",
    })
    assert resp.status_code == 401
