"""Tests: CRUD groups + group permissions."""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_header, login_user


@pytest.mark.asyncio
async def test_create_group(client: AsyncClient, superuser):
    """Superuser can create a group."""
    tokens = await login_user(client, "admin@test.com", "admin123456")
    resp = await client.post("/groups/", json={
        "name": "Thu ngân",
        "description": "Nhóm thu ngân",
    }, headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 201
    assert resp.json()["data"]["name"] == "Thu ngân"


@pytest.mark.asyncio
async def test_list_groups(client: AsyncClient, superuser):
    """Superuser can list groups."""
    tokens = await login_user(client, "admin@test.com", "admin123456")
    resp = await client.get("/groups/", headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_update_group(client: AsyncClient, superuser):
    """Superuser can update a group."""
    tokens = await login_user(client, "admin@test.com", "admin123456")

    # Create group first
    resp = await client.post("/groups/", json={
        "name": "Quản lý",
    }, headers=auth_header(tokens["access_token"]))
    group_id = resp.json()["data"]["id"]

    # Update
    resp2 = await client.put(f"/groups/{group_id}", json={
        "description": "Nhóm quản lý cửa hàng",
    }, headers=auth_header(tokens["access_token"]))
    assert resp2.status_code == 200
    assert resp2.json()["data"]["description"] == "Nhóm quản lý cửa hàng"


@pytest.mark.asyncio
async def test_delete_group(client: AsyncClient, superuser):
    """Superuser can delete a group."""
    tokens = await login_user(client, "admin@test.com", "admin123456")

    resp = await client.post("/groups/", json={"name": "ToDelete"}, headers=auth_header(tokens["access_token"]))
    group_id = resp.json()["data"]["id"]

    resp2 = await client.delete(f"/groups/{group_id}", headers=auth_header(tokens["access_token"]))
    assert resp2.status_code == 200


@pytest.mark.asyncio
async def test_create_group_permission(client: AsyncClient, superuser):
    """Superuser can create a group permission."""
    tokens = await login_user(client, "admin@test.com", "admin123456")

    # Create group
    resp = await client.post("/groups/", json={"name": "Staff"}, headers=auth_header(tokens["access_token"]))
    group_id = resp.json()["data"]["id"]

    # Create permission
    resp2 = await client.post("/group-permissions/", json={
        "group_id": group_id,
        "module_name": "products",
        "action": "list",
        "allowed": True,
    }, headers=auth_header(tokens["access_token"]))
    assert resp2.status_code == 201
    assert resp2.json()["data"]["module_name"] == "products"


@pytest.mark.asyncio
async def test_list_permissions_with_filter(client: AsyncClient, superuser):
    """Superuser can filter permissions by group_id."""
    tokens = await login_user(client, "admin@test.com", "admin123456")

    resp = await client.get("/group-permissions/?group_id=999", headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 200
    assert resp.json()["data"] == []
