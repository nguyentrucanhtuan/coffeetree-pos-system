"""Permission check helper for TRCFBaseModule.

Queries group_permissions table for the current user's groups.
Superuser bypasses all checks.
"""

from __future__ import annotations

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import GroupPermission


async def check_permission(
    request: Request,
    db: AsyncSession,
    module_name: str,
    action: str,
    *,
    require_auth: bool = True,
    public_actions: list[str] | None = None,
) -> int | None:
    """Check if the current user has permission for the given action.

    Args:
        request: FastAPI Request (contains state from JWTMiddleware)
        db: AsyncSession
        module_name: Module _name (e.g. "products")
        action: One of "list", "read", "create", "update", "archive", "restore", "delete", "bulk"
        require_auth: Whether this module requires authentication
        public_actions: Actions that bypass auth (e.g. ["list", "read"])

    Returns:
        user_id (int) if authenticated, None if public access

    Raises:
        HTTPException 401: Not authenticated
        HTTPException 403: No permission
    """
    public_actions = public_actions or []

    # Extract auth state from JWTMiddleware
    user_id: int | None = getattr(request.state, "user_id", None)
    is_superuser: bool = getattr(request.state, "user_is_superuser", False)
    group_ids: list[int] = getattr(request.state, "user_groups", [])

    # Superuser bypass — no further checks needed
    if is_superuser and user_id is not None:
        return user_id

    # Public action — allow without auth
    if action in public_actions:
        return user_id  # None if not logged in

    # Require auth but no user
    if require_auth and user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa đăng nhập",
        )

    # Module doesn't require auth and user is not logged in
    if not require_auth and user_id is None:
        return None

    # User is logged in — check group permissions
    if not group_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Không có quyền {action} trên {module_name}",
        )

    result = await db.execute(
        select(GroupPermission).where(
            GroupPermission.group_id.in_(group_ids),
            GroupPermission.module_name == module_name,
            GroupPermission.action == action,
            GroupPermission.allowed == True,  # noqa: E712
        )
    )
    perm = result.scalar_one_or_none()

    if not perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Không có quyền {action} trên {module_name}",
        )

    return user_id
