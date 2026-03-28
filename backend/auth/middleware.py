"""JWT authentication middleware.

Injects request.state.user_id, user_groups, user_is_superuser for every request.
MUST check type="access" — rejects refresh tokens used as access tokens.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from auth.utils import decode_token


# Paths that do NOT require authentication
PUBLIC_PATHS: set[str] = {
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
    "/auth/forgot-password",
    "/auth/reset-password",
    "/auth/verify-email",
    "/docs",
    "/redoc",
    "/openapi.json",
}


class JWTMiddleware(BaseHTTPMiddleware):
    """Extract and validate JWT from Authorization header."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Default: no auth
        request.state.user_id = None
        request.state.user_groups = []
        request.state.user_is_superuser = False

        # Skip auth for public paths
        path = request.url.path.rstrip("/")
        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = decode_token(token)

                # CRITICAL: reject refresh tokens used as access
                if payload.get("type") != "access":
                    return await call_next(request)

                request.state.user_id = int(payload["sub"])
                request.state.user_groups = payload.get("group_ids", [])
                request.state.user_is_superuser = payload.get("is_superuser", False)

            except Exception:
                # Invalid token — proceed without auth (endpoints will check)
                pass

        return await call_next(request)
