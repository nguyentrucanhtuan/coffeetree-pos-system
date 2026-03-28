"""Auth router — 9 authentication endpoints.

POST /auth/login
POST /auth/logout
POST /auth/refresh
GET  /auth/me
POST /auth/set-password
POST /auth/register
POST /auth/verify-email
POST /auth/forgot-password
POST /auth/reset-password
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.config import settings
from app.database import DBSession
from auth.dependencies import CurrentUserId
from auth.email import send_reset_email, send_verify_email
from auth.models import RefreshToken, User
from auth.schemas import (
    APIResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SetPasswordRequest,
    TokenResponse,
    UserInfo,
    VerifyEmailRequest,
)
from auth.utils import (
    create_access_token,
    create_refresh_token,
    create_verify_email_token,
    decode_token,
    generate_reset_token,
    hash_password,
    hash_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _success(data: dict | list | None = None, message: str | None = None) -> dict:
    return {"success": True, "data": data, "message": message}


def _error(message: str) -> dict:
    return {"success": False, "data": None, "message": message}


# ─── POST /auth/login ──────────────────────────────────────────────────────────

@router.post("/login")
async def login(body: LoginRequest, db: DBSession) -> dict:
    """Authenticate user, return dual tokens."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hoá",
        )

    group_ids = [g.id for g in user.groups]

    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        is_superuser=user.is_superuser,
        group_ids=group_ids,
    )

    refresh_token_str, jti, expires_at = create_refresh_token(user.id)

    # Save refresh token to DB
    db_refresh = RefreshToken(
        user_id=user.id,
        jti=jti,
        expires_at=expires_at,
    )
    db.add(db_refresh)
    await db.commit()

    login_data = LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserInfo.model_validate(user),
    )

    return _success(data=login_data.model_dump())


# ─── POST /auth/logout ─────────────────────────────────────────────────────────

@router.post("/logout")
async def logout(
    body: RefreshTokenRequest,
    db: DBSession,
    _user_id: CurrentUserId,
) -> dict:
    """Revoke refresh token."""
    try:
        payload = decode_token(body.refresh_token)
        jti = payload.get("jti")
    except Exception:
        return _success(message="Đã đăng xuất")

    if jti:
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        db_token = result.scalar_one_or_none()
        if db_token:
            db_token.revoked = True
            await db.commit()

    return _success(message="Đã đăng xuất")


# ─── POST /auth/refresh ────────────────────────────────────────────────────────

@router.post("/refresh")
async def refresh(body: RefreshTokenRequest, db: DBSession) -> dict:
    """Exchange refresh token for new access token."""
    try:
        payload = decode_token(body.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ hoặc đã hết hạn",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ hoặc đã hết hạn",
        )

    jti = payload.get("jti")
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.jti == jti)
    )
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ hoặc đã bị thu hồi",
        )

    # Get user with groups
    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản không tồn tại hoặc đã bị vô hiệu hoá",
        )

    group_ids = [g.id for g in user.groups]
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        is_superuser=user.is_superuser,
        group_ids=group_ids,
    )

    token_data = TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return _success(data=token_data.model_dump())


# ─── GET /auth/me ───────────────────────────────────────────────────────────────

@router.get("/me")
async def me(
    request: Request,
    db: DBSession,
    _user_id: CurrentUserId,
) -> dict:
    """Return current user info."""
    result = await db.execute(select(User).where(User.id == request.state.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User không tồn tại",
        )

    return _success(data=UserInfo.model_validate(user).model_dump())


# ─── POST /auth/set-password ───────────────────────────────────────────────────

@router.post("/set-password")
async def set_password(
    body: SetPasswordRequest,
    db: DBSession,
    _user_id: CurrentUserId,
    request: Request,
) -> dict:
    """Change password for authenticated user."""
    result = await db.execute(select(User).where(User.id == request.state.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu hiện tại không đúng",
        )

    user.password_hash = hash_password(body.new_password)
    await db.commit()

    return _success(message="Đổi mật khẩu thành công")


# ─── POST /auth/register ───────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: DBSession) -> dict:
    """Public registration (controlled by ALLOW_PUBLIC_REGISTER flag)."""
    if not settings.ALLOW_PUBLIC_REGISTER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Đăng ký bị vô hiệu",
        )

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
        email_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Send verify email
    verify_token = create_verify_email_token(user.id)
    send_verify_email(user.email, verify_token)

    return _success(
        data={"id": user.id, "email": user.email},
        message="Đăng ký thành công. Kiểm tra email để xác minh.",
    )


# ─── POST /auth/verify-email ───────────────────────────────────────────────────

@router.post("/verify-email")
async def verify_email(body: VerifyEmailRequest, db: DBSession) -> dict:
    """Verify email using JWT token."""
    try:
        payload = decode_token(body.token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token không hợp lệ hoặc đã hết hạn",
        )

    if payload.get("type") != "verify-email":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token không hợp lệ hoặc đã hết hạn",
        )

    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token không hợp lệ hoặc đã hết hạn",
        )

    user.email_verified = True
    await db.commit()

    return _success(message="Email đã được xác minh")


# ─── POST /auth/forgot-password ────────────────────────────────────────────────

@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: DBSession) -> dict:
    """Send password reset email. Always returns 200 (no email leak)."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user:
        plaintext_token, token_hash = generate_reset_token()
        user.password_reset_token = token_hash
        user.password_reset_at = datetime.now(timezone.utc)
        await db.commit()

        send_reset_email(user.email, plaintext_token)

    # Always 200 — never leak email existence
    return _success(message="Nếu email tồn tại, link reset đã được gửi")


# ─── POST /auth/reset-password ─────────────────────────────────────────────────

@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: DBSession) -> dict:
    """Reset password using token from forgot-password email."""
    token_hash = hash_token(body.token)

    result = await db.execute(
        select(User).where(User.password_reset_token == token_hash)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token không hợp lệ hoặc đã hết hạn",
        )

    # Check TTL (1 hour)
    if user.password_reset_at:
        elapsed = datetime.now(timezone.utc) - user.password_reset_at.replace(
            tzinfo=timezone.utc
        )
        if elapsed > timedelta(hours=1):
            user.password_reset_token = None
            user.password_reset_at = None
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token không hợp lệ hoặc đã hết hạn",
            )

    # Update password and clear token
    user.password_hash = hash_password(body.new_password)
    user.password_reset_token = None
    user.password_reset_at = None
    await db.commit()

    return _success(message="Đặt lại mật khẩu thành công")
