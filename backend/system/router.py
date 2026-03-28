"""System router — CMS Core CRUD endpoints (superuser-only).

CRUD /users/, /groups/, /group-permissions/
Meta schema endpoints for frontend dynamic rendering.
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import DBSession
from auth.dependencies import SuperUserId
from auth.models import Group, GroupPermission, User, user_groups
from auth.schemas import (
    APIResponse,
    GroupCreate,
    GroupOut,
    GroupPermissionCreate,
    GroupPermissionOut,
    GroupPermissionUpdate,
    GroupUpdate,
    UserCreate,
    UserDetail,
    UserUpdate,
)
from auth.utils import hash_password

router = APIRouter(tags=["system"])


def _success(data: dict | list | None = None, message: str | None = None) -> dict:
    return {"success": True, "data": data, "message": message}


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD /users/
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/users/")
async def list_users(db: DBSession, _su: SuperUserId) -> dict:
    """List all users with their groups."""
    result = await db.execute(select(User).options(selectinload(User.groups)))
    users = result.scalars().all()
    return _success(data=[UserDetail.model_validate(u).model_dump() for u in users])


@router.post("/users/", status_code=status.HTTP_201_CREATED)
async def create_user(body: UserCreate, db: DBSession, _su: SuperUserId) -> dict:
    """Create a new user."""
    # Check duplicate email
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email đã được sử dụng",
        )

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        is_active=body.is_active,
        is_superuser=body.is_superuser,
    )

    # Assign groups if provided
    if body.group_ids:
        result = await db.execute(
            select(Group).where(Group.id.in_(body.group_ids))
        )
        groups = result.scalars().all()
        user.groups = list(groups)

    db.add(user)
    await db.commit()
    await db.refresh(user, attribute_names=["groups"])

    return _success(data=UserDetail.model_validate(user).model_dump())


@router.get("/users/{user_id}")
async def get_user(user_id: int, db: DBSession, _su: SuperUserId) -> dict:
    """Get a single user."""
    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.groups))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User không tồn tại")
    return _success(data=UserDetail.model_validate(user).model_dump())


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: DBSession,
    _su: SuperUserId,
) -> dict:
    """Update user fields and group assignments."""
    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.groups))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User không tồn tại")

    update_data = body.model_dump(exclude_unset=True)

    # Handle group assignment separately
    if "group_ids" in update_data:
        group_ids = update_data.pop("group_ids")
        if group_ids is not None:
            result = await db.execute(
                select(Group).where(Group.id.in_(group_ids))
            )
            user.groups = list(result.scalars().all())

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()

    # Re-query to get all fields eagerly loaded (avoids greenlet error on updated_at)
    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.groups))
    )
    user = result.scalar_one()

    return _success(data=UserDetail.model_validate(user).model_dump())


@router.post("/users/{user_id}/archive")
async def archive_user(user_id: int, db: DBSession, _su: SuperUserId) -> dict:
    """Archive a user (set is_active=False). Consistent with TRCFBaseModule archive."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User không tồn tại")

    user.is_active = False
    await db.commit()

    return _success(message="User đã được lưu trữ")


@router.post("/users/{user_id}/restore")
async def restore_user(user_id: int, db: DBSession, _su: SuperUserId) -> dict:
    """Restore an archived user (set is_active=True)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User không tồn tại")

    user.is_active = True
    await db.commit()

    return _success(message="User đã được khôi phục")


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: DBSession, _su: SuperUserId) -> dict:
    """Permanently delete a user. Consistent with TRCFBaseModule delete."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User không tồn tại")

    await db.delete(user)
    await db.commit()

    return _success(message="User đã được xóa vĩnh viễn")


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD /groups/
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/groups/")
async def list_groups(db: DBSession, _su: SuperUserId) -> dict:
    """List all groups."""
    result = await db.execute(select(Group))
    groups = result.scalars().all()
    return _success(data=[GroupOut.model_validate(g).model_dump() for g in groups])


@router.post("/groups/", status_code=status.HTTP_201_CREATED)
async def create_group(body: GroupCreate, db: DBSession, _su: SuperUserId) -> dict:
    """Create a new group."""
    result = await db.execute(select(Group).where(Group.name == body.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tên group đã tồn tại",
        )

    group = Group(name=body.name, description=body.description)
    db.add(group)
    await db.commit()
    await db.refresh(group)

    return _success(data=GroupOut.model_validate(group).model_dump())


@router.get("/groups/{group_id}")
async def get_group(group_id: int, db: DBSession, _su: SuperUserId) -> dict:
    """Get a single group."""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group không tồn tại")
    return _success(data=GroupOut.model_validate(group).model_dump())


@router.put("/groups/{group_id}")
async def update_group(
    group_id: int,
    body: GroupUpdate,
    db: DBSession,
    _su: SuperUserId,
) -> dict:
    """Update a group."""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group không tồn tại")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(group, field, value)

    await db.commit()
    await db.refresh(group)

    return _success(data=GroupOut.model_validate(group).model_dump())


@router.delete("/groups/{group_id}")
async def delete_group(group_id: int, db: DBSession, _su: SuperUserId) -> dict:
    """Delete a group."""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group không tồn tại")

    await db.delete(group)
    await db.commit()

    return _success(message="Đã xóa group")


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD /group-permissions/
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/group-permissions/")
async def list_group_permissions(
    db: DBSession,
    _su: SuperUserId,
    group_id: int | None = None,
    module_name: str | None = None,
    action: str | None = None,
) -> dict:
    """List permissions with optional filters."""
    query = select(GroupPermission)
    if group_id is not None:
        query = query.where(GroupPermission.group_id == group_id)
    if module_name is not None:
        query = query.where(GroupPermission.module_name == module_name)
    if action is not None:
        query = query.where(GroupPermission.action == action)

    result = await db.execute(query)
    perms = result.scalars().all()
    return _success(data=[GroupPermissionOut.model_validate(p).model_dump() for p in perms])


@router.post("/group-permissions/", status_code=status.HTTP_201_CREATED)
async def create_group_permission(
    body: GroupPermissionCreate,
    db: DBSession,
    _su: SuperUserId,
) -> dict:
    """Create a new group permission."""
    perm = GroupPermission(
        group_id=body.group_id,
        module_name=body.module_name,
        action=body.action,
        allowed=body.allowed,
    )
    db.add(perm)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Permission đã tồn tại cho group/module/action này",
        )
    await db.refresh(perm)

    return _success(data=GroupPermissionOut.model_validate(perm).model_dump())


@router.put("/group-permissions/{perm_id}")
async def update_group_permission(
    perm_id: int,
    body: GroupPermissionUpdate,
    db: DBSession,
    _su: SuperUserId,
) -> dict:
    """Toggle permission allowed status."""
    result = await db.execute(select(GroupPermission).where(GroupPermission.id == perm_id))
    perm = result.scalar_one_or_none()
    if not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission không tồn tại")

    perm.allowed = body.allowed
    await db.commit()
    await db.refresh(perm)

    return _success(data=GroupPermissionOut.model_validate(perm).model_dump())


@router.delete("/group-permissions/{perm_id}")
async def delete_group_permission(perm_id: int, db: DBSession, _su: SuperUserId) -> dict:
    """Delete a permission."""
    result = await db.execute(select(GroupPermission).where(GroupPermission.id == perm_id))
    perm = result.scalar_one_or_none()
    if not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission không tồn tại")

    await db.delete(perm)
    await db.commit()

    return _success(message="Đã xóa permission")


# ═══════════════════════════════════════════════════════════════════════════════
# Meta Schema endpoints for frontend dynamic rendering
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/users/meta/schema")
async def users_meta_schema(_su: SuperUserId) -> dict:
    """Return field metadata for Users form."""
    return _success(data={
        "module": "users",
        "description": "Quản lý người dùng",
        "fields": [
            {"name": "email", "type": "string", "label": "Email", "required": True, "ui_type": "email"},
            {"name": "full_name", "type": "string", "label": "Họ tên", "required": False},
            {"name": "is_active", "type": "boolean", "label": "Hoạt động", "default": True},
            {"name": "is_superuser", "type": "boolean", "label": "Superuser", "default": False},
            {"name": "group_ids", "type": "m2m", "label": "Nhóm", "to": "groups"},
        ],
        "search_fields": ["email", "full_name"],
        "filter_fields": ["is_active", "is_superuser"],
        "sort_by": "email",
        "sort_desc": False,
        "archive": True,
        "has_settings": False,
        "computed_fields": [],
    })


@router.get("/groups/meta/schema")
async def groups_meta_schema(_su: SuperUserId) -> dict:
    """Return field metadata for Groups form."""
    return _success(data={
        "module": "groups",
        "description": "Quản lý nhóm quyền",
        "fields": [
            {"name": "name", "type": "string", "label": "Tên nhóm", "required": True},
            {"name": "description", "type": "string", "label": "Mô tả", "required": False, "ui_type": "textarea"},
        ],
        "search_fields": ["name"],
        "filter_fields": [],
        "sort_by": "name",
        "sort_desc": False,
        "archive": False,
        "has_settings": False,
        "computed_fields": [],
    })


@router.get("/group-permissions/meta/schema")
async def group_permissions_meta_schema(_su: SuperUserId) -> dict:
    """Return field metadata for GroupPermissions form."""
    return _success(data={
        "module": "group-permissions",
        "description": "Phân quyền theo nhóm",
        "fields": [
            {"name": "group_id", "type": "foreignkey", "label": "Nhóm", "required": True, "to": "groups"},
            {"name": "module_name", "type": "string", "label": "Module", "required": True},
            {"name": "action", "type": "selection", "label": "Action", "required": True,
             "options": ["list", "read", "create", "update", "archive", "restore", "delete", "bulk"]},
            {"name": "allowed", "type": "boolean", "label": "Cho phép", "default": True},
        ],
        "search_fields": ["module_name"],
        "filter_fields": ["group_id", "action", "allowed"],
        "sort_by": "module_name",
        "sort_desc": False,
        "archive": False,
        "has_settings": False,
        "computed_fields": [],
    })


# ═══════════════════════════════════════════════════════════════════════════════
# GET /modules/menu — Sidebar menu for frontend (T055, T056)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/modules/menu")
async def modules_menu() -> dict:
    """Return sidebar menu items from all registered TRCFBaseModule classes.

    No auth required — menu structure is public metadata.
    Modules import lazily to avoid circular imports at router declaration time.
    """
    from app.main import REGISTERED_MODULES

    items = []
    for module_cls in REGISTERED_MODULES:
        item = module_cls.menu_item()
        if item is not None:
            items.append(item)

    # Sort by sequence then name
    items.sort(key=lambda x: (x.get("menu_sequence", 100), x.get("name", "")))

    return _success(data=items)


# ═══════════════════════════════════════════════════════════════════════════════
# System Settings (T058-T063)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/system-settings/")
async def list_settings(db: DBSession, _su: SuperUserId) -> dict:
    """List all system settings, optionally filtered by module_name query param."""
    from sqlalchemy import select as sa_select
    from system.models import SystemSetting
    from fastapi import Request
    result = await db.execute(sa_select(SystemSetting).order_by(SystemSetting.module_name, SystemSetting.key))
    settings = result.scalars().all()
    return _success(data=[
        {
            "id": s.id,
            "module_name": s.module_name,
            "key": s.key,
            "label": s.label,
            "value": s.value,
            "value_type": s.value_type,
        }
        for s in settings
    ])


@router.put("/system-settings/{module_name}/{key}")
async def update_setting(
    module_name: str,
    key: str,
    db: DBSession,
    _su: SuperUserId,
    body: dict,
) -> dict:
    """Update a system setting value."""
    from sqlalchemy import select as sa_select
    from system.models import SystemSetting

    result = await db.execute(
        sa_select(SystemSetting).where(
            SystemSetting.module_name == module_name,
            SystemSetting.key == key,
        )
    )
    setting = result.scalar_one_or_none()

    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting {module_name}.{key} không tồn tại",
        )

    new_value = body.get("value")
    if new_value is not None:
        setting.value = str(new_value)
        await db.commit()

    return _success(message="Đã cập nhật setting")
