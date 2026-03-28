"""FastAPI dependencies for auth checks."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status


async def require_auth(request: Request) -> int:
    """Require authenticated user. Returns user_id."""
    if not request.state.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yêu cầu đăng nhập",
        )
    return request.state.user_id


async def require_superuser(request: Request) -> int:
    """Require superuser. Returns user_id."""
    user_id = await require_auth(request)
    if not request.state.user_is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ superuser mới có quyền truy cập",
        )
    return user_id


# Type aliases for Annotated dependencies
CurrentUserId = Annotated[int, Depends(require_auth)]
SuperUserId = Annotated[int, Depends(require_superuser)]
