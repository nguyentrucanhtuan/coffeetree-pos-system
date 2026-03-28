"""Tests: CRUD users (superuser-only access)."""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_header, login_user


@pytest.mark.asyncio
async def test_list_users_superuser(client: AsyncClient, superuser):
    """Superuser can list users."""
    tokens = await login_user(client, "admin@test.com", "admin123456")
    resp = await client.get("/users/", headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert isinstance(resp.json()["data"], list)


@pytest.mark.asyncio
async def test_list_users_non_superuser(client: AsyncClient, normal_user):
    """Non-superuser gets 403."""
    tokens = await login_user(client, "user@test.com", "user123456")
    resp = await client.get("/users/", headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, superuser):
    """Superuser can create a new user."""
    tokens = await login_user(client, "admin@test.com", "admin123456")
    resp = await client.post("/users/", json={
        "email": "newuser@test.com",
        "password": "password123",
        "full_name": "New User",
    }, headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 201
    assert resp.json()["data"]["email"] == "newuser@test.com"


@pytest.mark.asyncio
async def test_create_duplicate_user(client: AsyncClient, superuser):
    """Duplicate email returns 409."""
    tokens = await login_user(client, "admin@test.com", "admin123456")
    resp = await client.post("/users/", json={
        "email": "admin@test.com",
        "password": "password123",
    }, headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_user(client: AsyncClient, superuser):
    """Superuser can get user detail."""
    tokens = await login_user(client, "admin@test.com", "admin123456")
    resp = await client.get(f"/users/{superuser.id}", headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == "admin@test.com"


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, superuser):
    """Superuser can update user."""
    tokens = await login_user(client, "admin@test.com", "admin123456")
    resp = await client.put(f"/users/{superuser.id}", json={
        "full_name": "Updated Admin",
    }, headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 200
    assert resp.json()["data"]["full_name"] == "Updated Admin"


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, superuser):
    """Delete user sets is_active=False."""
    tokens = await login_user(client, "admin@test.com", "admin123456")

    # Create another user to delete
    await client.post("/users/", json={
        "email": "toDelete@test.com",
        "password": "password123",
    }, headers=auth_header(tokens["access_token"]))

    # Get the created user's id
    resp = await client.get("/users/", headers=auth_header(tokens["access_token"]))
    users = resp.json()["data"]
    target = [u for u in users if u["email"] == "toDelete@test.com"][0]

    resp2 = await client.delete(f"/users/{target['id']}", headers=auth_header(tokens["access_token"]))
    assert resp2.status_code == 200
