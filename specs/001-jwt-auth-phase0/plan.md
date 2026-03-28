# Implementation Plan: JWT Authentication & CMS Core

**Branch**: `001-jwt-auth-phase0` | **Date**: 2026-03-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-jwt-auth-phase0/spec.md`

## Summary

Implement Phase 0 foundation: JWT dual-token authentication (access 30m + refresh 30d) with CMS Core models (User, Group, GroupPermission, RefreshToken) and 9 auth endpoints + CMS Core CRUD endpoints. This layer provides `request.state.user_id/groups/is_superuser` for all downstream TRCFBaseModule endpoints.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI 0.115, SQLAlchemy 2.0 (async), Pydantic v2, PyJWT 2.x, bcrypt
**Storage**: PostgreSQL + asyncpg (prod), SQLite + aiosqlite (test)
**Testing**: pytest + pytest-asyncio + httpx (async client)
**Target Platform**: Linux server (Docker)
**Project Type**: Web service (FastAPI backend)
**Performance Goals**: N/A for Phase 0 (internal POS, low concurrency)
**Constraints**: No rate limiting (internal network), no concurrent session limits
**Scale/Scope**: < 100 users, single-tenant POS

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|:------:|
| I. CRUD Base Thuần | CMS Core viết tay, KHÔNG dùng TRCFBaseModule | ✅ Pass |
| II. CMS Core Tách Biệt | User/Group/GroupPermission thuần SQLAlchemy | ✅ Pass |
| III. Security First | bcrypt + JWT HS256 + SHA-256 reset token + type check | ✅ Pass |
| IV. Async First | AsyncSession + async handlers | ✅ Pass |
| VI. Response Format | `{success, data, message}` mọi endpoint | ✅ Pass |
| VII. Test Per Phase | pytest + SQLite in-memory | ✅ Pass |
| VIII. Đăng Ký Tường Minh | auth_router + system_router include tường minh | ✅ Pass |

## Project Structure

### Documentation (this feature)

```text
specs/001-jwt-auth-phase0/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contracts)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── __init__.py
│   ├── config.py          # Settings from .env (Pydantic BaseSettings)
│   ├── database.py        # AsyncEngine, AsyncSessionLocal, Base
│   └── main.py            # FastAPI app, lifespan, middleware, routers
├── auth/
│   ├── __init__.py
│   ├── models.py          # User, Group, GroupPermission, RefreshToken, user_groups
│   ├── schemas.py         # Pydantic: Login/Register/Token/SetPassword/Reset/Refresh
│   ├── router.py          # 9 auth endpoints
│   ├── dependencies.py    # require_superuser
│   ├── middleware.py       # JWTMiddleware
│   ├── utils.py           # create_token, decode_token, hash_password, verify_password
│   └── email.py           # send_reset_email, send_verify_email (SMTP/console)
├── system/
│   ├── __init__.py
│   └── router.py          # CRUD /users/, /groups/, /group-permissions/ (superuser-only)
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # Fixtures: async client, test DB, test user/superuser
│   ├── test_auth.py       # Login, logout, refresh, set-password, register, verify, reset
│   ├── test_middleware.py  # JWT type check, expired token, no token
│   ├── test_cms_users.py  # CRUD users (superuser-only)
│   ├── test_cms_groups.py # CRUD groups + permissions
│   └── test_permissions.py # Permission check flow integration
├── alembic/               # DB migrations
│   ├── env.py
│   └── versions/
├── alembic.ini
├── requirements.txt
└── .env
```

**Structure Decision**: Backend-only web service, no frontend in this phase. Standard FastAPI project layout with `auth/` and `system/` as CMS Core packages.

## Implementation Phases

### Phase A: Database & Config Foundation

1. `app/config.py` — Pydantic BaseSettings loading `.env`
2. `app/database.py` — AsyncEngine + AsyncSessionLocal + Base declarative
3. `auth/models.py` — All 4 models + user_groups M2M table
4. Alembic setup + initial migration
5. `.env` file with all required variables

### Phase B: Auth Utilities & Middleware

1. `auth/utils.py` — JWT create/decode + bcrypt hash/verify + SHA-256 token hash
2. `auth/schemas.py` — All Pydantic schemas with validators
3. `auth/middleware.py` — JWTMiddleware (inject request.state, type="access" check)
4. `auth/dependencies.py` — require_superuser dependency

### Phase C: Auth Endpoints

1. `auth/router.py`:
   - `POST /auth/login` — dual-token login
   - `POST /auth/logout` — revoke refresh token
   - `POST /auth/refresh` — exchange refresh → new access
   - `GET /auth/me` — current user info
   - `POST /auth/set-password` — change password (authenticated)
   - `POST /auth/register` — conditional on ALLOW_PUBLIC_REGISTER
   - `POST /auth/verify-email` — JWT 24h verify token
   - `POST /auth/forgot-password` — send reset email
   - `POST /auth/reset-password` — UUID token 1h
2. `auth/email.py` — SMTP sender (console fallback)

### Phase D: CMS Core Endpoints

1. `system/router.py`:
   - CRUD `/users/` (superuser-only)
   - CRUD `/groups/` (superuser-only)
   - CRUD `/group-permissions/` (superuser-only)
   - `/users/meta/schema`, `/groups/meta/schema`, `/group-permissions/meta/schema`

### Phase E: App Assembly & Startup

1. `app/main.py`:
   - Lifespan: auto-seed superuser
   - Add JWTMiddleware
   - Include auth_router + system_router
2. Alembic migration run

### Phase F: Testing

1. `tests/conftest.py` — SQLite async fixtures, test users
2. `tests/test_auth.py` — All 9 auth endpoints
3. `tests/test_middleware.py` — JWT validation edge cases
4. `tests/test_cms_users.py` — CRUD users
5. `tests/test_cms_groups.py` — CRUD groups + permissions
6. `tests/test_permissions.py` — Permission check flow integration

## Complexity Tracking

> No constitution violations. No complexity justifications needed.
