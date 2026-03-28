"""Pydantic schemas for authentication and CMS Core."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


# ─── Standard Response Wrapper ─────────────────────────────────────────────────

class APIResponse(BaseModel):
    """Standard response format: {success, data, message}."""
    success: bool
    data: dict | list | None = None
    message: str | None = None


# ─── Auth Request Schemas ──────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            msg = "Mật khẩu phải có ít nhất 8 ký tự"
            raise ValueError(msg)
        return v


class SetPasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            msg = "Mật khẩu mới phải có ít nhất 8 ký tự"
            raise ValueError(msg)
        return v


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            msg = "Mật khẩu mới phải có ít nhất 8 ký tự"
            raise ValueError(msg)
        return v


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    token: str


# ─── Auth Response Schemas ─────────────────────────────────────────────────────

class UserInfo(BaseModel):
    id: int
    email: str
    full_name: str | None = None
    is_superuser: bool = False
    email_verified: bool = False

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo


# ─── CMS Core Schemas ─────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False
    group_ids: list[int] = []

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            msg = "Mật khẩu phải có ít nhất 8 ký tự"
            raise ValueError(msg)
        return v


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    group_ids: list[int] | None = None


class UserDetail(BaseModel):
    id: int
    email: str
    full_name: str | None = None
    is_active: bool
    is_superuser: bool
    email_verified: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    groups: list["GroupOut"] = []

    model_config = {"from_attributes": True}


class GroupCreate(BaseModel):
    name: str
    description: str | None = None


class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class GroupOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class GroupPermissionCreate(BaseModel):
    group_id: int
    module_name: str
    action: str
    allowed: bool = True


class GroupPermissionUpdate(BaseModel):
    allowed: bool


class GroupPermissionOut(BaseModel):
    id: int
    group_id: int
    module_name: str
    action: str
    allowed: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
