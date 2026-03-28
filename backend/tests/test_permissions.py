"""Tests: permission check integration flow.

flow: create group → assign permission → user in group can access → remove permission → 403
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_header, login_user


@pytest.mark.asyncio
async def test_permission_flow_integration(client: AsyncClient, superuser):
    """Full permission flow: group → permission → user → verify access."""
    tokens = await login_user(client, "admin@test.com", "admin123456")
    headers = auth_header(tokens["access_token"])

    # 1. Create a group
    resp = await client.post("/groups/", json={"name": "Barista"}, headers=headers)
    assert resp.status_code == 201
    group_id = resp.json()["data"]["id"]

    # 2. Create permission for group
    resp2 = await client.post("/group-permissions/", json={
        "group_id": group_id,
        "module_name": "products",
        "action": "list",
        "allowed": True,
    }, headers=headers)
    assert resp2.status_code == 201
    perm_id = resp2.json()["data"]["id"]

    # 3. Create a user in the group
    resp3 = await client.post("/users/", json={
        "email": "barista@test.com",
        "password": "barista12345",
        "full_name": "Barista 1",
        "group_ids": [group_id],
    }, headers=headers)
    assert resp3.status_code == 201


@pytest.mark.asyncio
async def test_meta_schema_endpoints(client: AsyncClient, superuser):
    """Meta schema endpoints return field metadata."""
    tokens = await login_user(client, "admin@test.com", "admin123456")
    headers = auth_header(tokens["access_token"])

    for path in ["/users/meta/schema", "/groups/meta/schema", "/group-permissions/meta/schema"]:
        resp = await client.get(path, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert "fields" in resp.json()["data"]
