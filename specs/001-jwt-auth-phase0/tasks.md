# Tasks: JWT Authentication & CMS Core (Phase 0)

**Input**: Design documents from `/specs/001-jwt-auth-phase0/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/api.md, research.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US7)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Project Foundation)

**Purpose**: Project scaffold, dependencies, environment config

- [x] T001 Create project directory structure per plan.md (backend/app/, auth/, system/, tests/)
- [x] T002 Create requirements.txt with all dependencies (fastapi, uvicorn, sqlalchemy, asyncpg, aiosqlite, pyjwt, bcrypt, pydantic[email], python-dotenv, alembic, httpx, pytest, pytest-asyncio)
- [x] T003 [P] Create .env file with all config variables in backend/.env
- [x] T004 [P] Create app/config.py — Pydantic BaseSettings loading .env (SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, ADMIN_EMAIL, ADMIN_PASSWORD, ALLOW_PUBLIC_REGISTER, FRONTEND_URL, SMTP_*, DATABASE_URL)
- [x] T005 [P] Create app/database.py — AsyncEngine, AsyncSessionLocal, Base declarative, get_db dependency
- [x] T006 Install dependencies: `pip install -r requirements.txt`

**Checkpoint**: Project structure ready, config loads from .env

---

## Phase 2: Foundational (Database & Core Models)

**Purpose**: CMS Core models + Alembic migrations — BLOCKS all user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Create auth/models.py — User, Group, GroupPermission, RefreshToken, user_groups M2M (from data-model.md)
- [x] T008 Initialize Alembic: `alembic init alembic` + configure alembic/env.py for async
- [x] T009 Generate initial migration: `alembic revision --autogenerate -m "CMS Core models"`
- [x] T010 Run migration: `alembic upgrade head`
- [x] T011 [P] Create auth/utils.py — create_access_token(), create_refresh_token(), decode_token(), hash_password(), verify_password(), hash_token(), verify_token()
- [x] T012 [P] Create auth/schemas.py — LoginRequest, RegisterRequest, UserInfo, TokenResponse, LoginResponse, SetPasswordRequest, ForgotPasswordRequest, ResetPasswordRequest, RefreshTokenRequest (with field_validator password min 8)

**Checkpoint**: Database tables created, utility functions ready, schemas defined

---

## Phase 3: User Story 1 — Đăng Nhập Hệ Thống (Priority: P1) 🎯 MVP

**Goal**: Nhân viên đăng nhập bằng email/password → nhận access + refresh token → dùng hệ thống

**Independent Test**: `POST /auth/login` → nhận token → `GET /auth/me` → nhận user info

### Implementation

- [x] T013 [US1] Create auth/middleware.py — JWTMiddleware: inject request.state.user_id, user_groups, user_is_superuser. MUST check type="access" and reject refresh tokens
- [x] T014 [US1] Create auth/dependencies.py — require_superuser dependency function
- [x] T015 [US1] Implement POST /auth/login in auth/router.py — validate credentials, check is_active, create dual tokens, save RefreshToken to DB
- [x] T016 [US1] Implement GET /auth/me in auth/router.py — return current user info from request.state
- [x] T017 [US1] Create app/main.py — FastAPI app, add JWTMiddleware, include auth_router. Response format: {success, data, message}

**Checkpoint**: Login + /me works end-to-end. Token → request.state injection functional.

---

## Phase 4: User Story 2 — Auto-Seed Superuser (Priority: P1)

**Goal**: App khởi động lần đầu → tự tạo superuser từ .env → admin đăng nhập ngay

**Independent Test**: Khởi động với DB trống → kiểm tra users table có 1 superuser

### Implementation

- [x] T018 [US2] Add lifespan handler to app/main.py — auto-seed superuser from .env if users table empty
- [x] T019 [US2] Verify: start app → login with ADMIN_EMAIL/ADMIN_PASSWORD → confirm is_superuser=True

**Checkpoint**: First startup creates superuser automatically

---

## Phase 5: User Story 3 — CRUD Users, Groups, Permissions (Priority: P1)

**Goal**: Superuser quản lý users, groups, permissions qua CMS Core API

**Independent Test**: Superuser tạo Group → tạo GroupPermission → tạo User gán group

### Implementation

- [x] T020 [P] [US3] Implement CRUD /users/ in system/router.py — list, create, read, update, delete (superuser-only)
- [x] T021 [P] [US3] Implement CRUD /groups/ in system/router.py — list, create, read, update, delete (superuser-only)
- [x] T022 [P] [US3] Implement CRUD /group-permissions/ in system/router.py — list (with filters), create, update, delete (superuser-only)
- [x] T023 [US3] Implement GET /users/meta/schema, /groups/meta/schema, /group-permissions/meta/schema in system/router.py
- [x] T024 [US3] Register system_router in app/main.py

**Checkpoint**: Superuser can fully manage users, groups, permissions

---

## Phase 6: User Story 4 — Refresh Token & Logout (Priority: P2)

**Goal**: Frontend refresh access token mà không cần re-login. Logout revoke token.

**Independent Test**: Login → refresh → nhận new access_token → logout → refresh lại → 401

### Implementation

- [x] T025 [US4] Implement POST /auth/refresh in auth/router.py — validate refresh token (DB lookup, not revoked, not expired, type="refresh"), issue new access_token
- [x] T026 [US4] Implement POST /auth/logout in auth/router.py — revoke refresh token in DB

**Checkpoint**: Token lifecycle complete — login → refresh → logout all work

---

## Phase 7: User Story 5 — Đổi Mật Khẩu (Priority: P2)

**Goal**: User đăng nhập đổi mật khẩu biết password cũ

**Independent Test**: Login → POST /auth/set-password → login lại bằng password mới

### Implementation

- [x] T027 [US5] Implement POST /auth/set-password in auth/router.py — verify current_password, validate new_password min 8, update password_hash

**Checkpoint**: Password change flow works

---

## Phase 8: User Story 6 — Quên Mật Khẩu & Reset (Priority: P3)

**Goal**: User quên password → nhận email reset → đặt password mới

**Independent Test**: forgot-password → check console log → reset-password → login bằng password mới

### Implementation

- [x] T028 [P] [US6] Create auth/email.py — send_reset_email(), send_verify_email() with SMTP/console fallback
- [x] T029 [US6] Implement POST /auth/forgot-password in auth/router.py — generate UUID token, hash SHA-256, save to user, send email. Always return 200.
- [x] T030 [US6] Implement POST /auth/reset-password in auth/router.py — verify token hash + TTL 1h, update password, clear token

**Checkpoint**: Full forgot → reset → login flow works (at least with console email)

---

## Phase 9: User Story 7 — Đăng Ký & Xác Minh Email (Priority: P3)

**Goal**: Public registration (khi ALLOW_PUBLIC_REGISTER=true) + email verification

**Independent Test**: Register → console log verify email → verify-email → email_verified=True

### Implementation

- [x] T031 [US7] Implement POST /auth/register in auth/router.py — check ALLOW_PUBLIC_REGISTER flag, create user (email_verified=False), send verify email
- [x] T032 [US7] Implement POST /auth/verify-email in auth/router.py — decode JWT verify token (type="verify-email", require exp with 24h, leeway 10s), set email_verified=True

**Checkpoint**: Registration + email verification flow works

---

## Phase 10: Testing

**Purpose**: Comprehensive test suite

- [x] T033 Create tests/conftest.py — SQLite async fixtures, test DB setup/teardown, test user factory, superuser factory, async httpx client
- [x] T034 [P] Create tests/test_auth.py — test login (success, wrong password, inactive user), test /me, test set-password
- [x] T035 [P] Create tests/test_middleware.py — test type="access" check, expired token, no token, refresh token rejected
- [x] T036 [P] Create tests/test_refresh.py — test refresh flow, revoked token, expired token, logout
- [x] T037 [P] Create tests/test_cms_users.py — CRUD users (superuser-only, non-superuser → 403)
- [x] T038 [P] Create tests/test_cms_groups.py — CRUD groups + group-permissions
- [x] T039 Create tests/test_permissions.py — integration: create group → assign permission → user can access module → remove permission → 403
- [x] T040 Create tests/test_register_reset.py — register, verify-email, forgot-password, reset-password flows
- [x] T041 Run full test suite: `pytest tests/ -v --asyncio-mode=auto`

**Checkpoint**: All tests pass ✅

---

## Phase 11: Polish & Cross-Cutting Concerns

- [x] T042 [P] Review all error responses match format: {success: false, data: null, message: "..."}
- [x] T043 [P] Add docstrings to all public functions in auth/utils.py, auth/router.py, system/router.py
- [x] T044 Validate quickstart.md — fresh install + login works end-to-end
- [x] T045 Run final validation: all 9 auth endpoints + CMS CRUD + permission flow

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3-9 (User Stories)**: All depend on Phase 2 completion
  - US1 (Login) → MUST complete first (others need auth)
  - US2 (Auto-seed) → depends on US1 (needs login to verify)
  - US3 (CMS CRUD) → depends on US1 (needs superuser auth)
  - US4 (Refresh/Logout) → depends on US1 (needs login first)
  - US5 (Set Password) → depends on US1 (needs auth)
  - US6 (Reset Password) → depends on US1 (independent otherwise)
  - US7 (Register) → depends on US6 (shares email.py)
- **Phase 10 (Testing)**: After all user stories OR incrementally
- **Phase 11 (Polish)**: After testing complete

### Recommended Execution Order

```
Phase 1 → Phase 2 → US1 (Login) → US2 (Seed) → US3 (CMS CRUD)
                                  → US4 (Refresh) → US5 (Set Password)
                                  → US6 (Reset) → US7 (Register)
                   → Phase 10 (Testing) → Phase 11 (Polish)
```

### Parallel Opportunities

```bash
# Phase 1 — parallel:
T003, T004, T005 (different files)

# Phase 2 — parallel:
T011, T012 (different files)

# Phase 5 (US3) — parallel:
T020, T021, T022 (different files in system/router.py sections)

# Phase 10 — parallel:
T034, T035, T036, T037, T038 (different test files)
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Complete Phase 1 + Phase 2
2. Complete Phase 3 (US1: Login + /me)
3. **STOP and VALIDATE**: Login works, token → request.state works
4. This is the minimum needed for TRCFBaseModule Phase 1

### Full Phase 0

1. Setup → Foundational → US1 → US2 → US3 → US4 → US5 → US6 → US7
2. All tests → Polish
3. Phase 0 complete — ready for TRCFBaseModule

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Commit after each phase checkpoint
- Total tasks: **45** (T001–T045)
- Spec reference: [1.jwt_spec.md](../../.specify/specs/001-trcf-base-module/1.jwt_spec.md)
