# Implementation Plan: TRCFBaseModule CRUD Framework

**Branch**: `002-trcf-base-module` | **Date**: 2026-03-26 | **Spec**: [spec.md](file:///Users/tuan/coffeetree-fastapi/specs/002-trcf-base-module/spec.md)
**Input**: Feature specification from `/specs/002-trcf-base-module/spec.md`

## Summary

Build the `TRCFBaseModule` metaclass/base class that auto-generates SQLAlchemy models, Pydantic schemas, and 9 async CRUD endpoints from Python class field definitions. Includes auto permission check, audit trail, archive/restore, filter prefix syntax, computed fields, bulk import, menu system, and settings system. Developer declares a class → gets a complete REST module.

## Technical Context

**Language/Version**: Python 3.13  
**Primary Dependencies**: FastAPI 0.115, SQLAlchemy 2.0 Async, Pydantic v2, PyJWT 2.x, bcrypt, openpyxl  
**Storage**: PostgreSQL + asyncpg (prod), SQLite + aiosqlite (test/dev)  
**Testing**: pytest + pytest-asyncio + httpx  
**Target Platform**: Linux server (Docker)  
**Project Type**: Web service (backend API)  
**Performance Goals**: Permission check < 5ms overhead, List endpoint handles 10k+ records  
**Constraints**: All SQL via parameterized queries, async-only DB operations  
**Scale/Scope**: Internal F&B POS system, ~20 modules expected

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. CRUD Base Thuần | ✅ PASS | Core of this feature — auto-generate everything from class definition |
| II. CMS Core Tách Biệt | ✅ PASS | TRCFBaseModule does NOT inherit CMS Core models. CMS Core is prerequisite |
| III. Security First | ✅ PASS | Parameterized queries for filters, JWT permission check, bcrypt |
| IV. Async First | ✅ PASS | All handlers async, AsyncSession throughout |
| V. Không Cross-Module Inheritance | ✅ PASS | Each module is independent class, share via Python mixin |
| VI. Response Format Nhất Quán | ✅ PASS | `{success, data, message}` format for all endpoints |
| VII. Test Per Phase | ✅ PASS | Test plan includes per-phase test files |
| VIII. Module Đăng Ký Tường Minh | ✅ PASS | `app.include_router(Product.router())` — explicit registration |
| IX. Archive Thay Vì Xóa | ⚠️ NOTE | Constitution says `DELETE /{id}?hard=true` but spec updated to `DELETE /{id}` = physical delete (simpler). Constitution should be updated |

## Project Structure

### Documentation (this feature)

```text
specs/002-trcf-base-module/
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
│   ├── main.py               # App entry + module registration
│   ├── config.py              # Settings
│   └── database.py            # AsyncSession factory
├── auth/                      # CMS Core (already exists)
│   ├── models.py              # User, Group, GroupPermission, RefreshToken
│   ├── middleware.py           # JWTMiddleware
│   ├── router.py              # Auth endpoints
│   └── ...
├── system/
│   ├── router.py              # CMS Core CRUD (already exists)
│   └── models.py              # MenuGroup, SystemSetting (NEW)
├── base/                      # ← TRCFBaseModule (NEW)
│   ├── __init__.py
│   ├── fields.py              # Field type classes (14 types)
│   ├── module.py              # TRCFBaseModule metaclass + base class
│   ├── handlers.py            # Generic async CRUD handler functions
│   ├── router_factory.py      # Auto-generate FastAPI router from module
│   ├── schema_factory.py      # Auto-generate Pydantic schemas from fields
│   ├── model_factory.py       # Auto-generate SQLAlchemy model from fields
│   ├── permissions.py         # Permission check helper
│   ├── filters.py             # Filter prefix parser
│   ├── computed.py            # Computed field engine
│   └── upload.py              # File/Image upload handler
├── modules/                   # ← Business modules (NEW)
│   ├── __init__.py
│   ├── categories.py          # Test module: Category
│   ├── products.py            # Canary module: Product (all field types)
│   └── data/
│       ├── categories.json    # Seed data
│       └── products.json      # Seed data
├── uploads/                   # ← File storage (NEW)
├── alembic/                   # Already exists
├── tests/
│   ├── test_base_module.py    # Phase 1 tests (NEW)
│   ├── test_fields.py         # Field type tests (NEW)
│   ├── test_permissions.py    # Permission integration tests (NEW)
│   ├── test_filters.py        # Filter prefix syntax tests (NEW)
│   └── ...
└── requirements.txt
```

**Structure Decision**: Web application pattern. `base/` is the new core package containing TRCFBaseModule framework. `modules/` contains business modules. Existing `auth/` and `system/` remain unchanged (CMS Core).

## Implementation Phases

### Phase 1: Field Types + Model Factory (Foundation)

**Goal**: Define all 14 field types and auto-generate SQLAlchemy models.

| # | File | Description |
|---|---|---|
| 1 | `base/fields.py` | 14 field type classes with metadata (label, type, required, etc.) |
| 2 | `base/model_factory.py` | Convert field definitions → SQLAlchemy Table + Model class |
| 3 | `base/module.py` (partial) | TRCFBaseModule base class with `_name`, `_archive`, auto-columns |
| 4 | `tests/test_fields.py` | Unit tests for each field type → correct DB column mapping |

**Exit criteria**: `Category(TRCFBaseModule)` → SQLAlchemy model with correct columns.

### Phase 2: Schema Factory + CRUD Handlers

**Goal**: Auto-generate Pydantic schemas and async CRUD functions.

| # | File | Description |
|---|---|---|
| 1 | `base/schema_factory.py` | Fields → Create/Update/Response Pydantic models |
| 2 | `base/handlers.py` | Generic async: list, get, create, update, archive, restore, delete |
| 3 | `base/permissions.py` | Permission check against `group_permissions` table |
| 4 | `base/filters.py` | Filter prefix parser (=, >, >=, <, <=, !=, IN, NOT IN, LIKE, BETWEEN) |
| 5 | `tests/test_base_module.py` | CRUD integration tests with Category module |

**Exit criteria**: All 7 CRUD endpoints work for Category module with permission checks.

### Phase 3: Router Factory + Meta Schema

**Goal**: Auto-generate FastAPI router and `/meta/schema` endpoint.

| # | File | Description |
|---|---|---|
| 1 | `base/router_factory.py` | Generate APIRouter with all 9 endpoints from module class |
| 2 | `base/module.py` (complete) | `.router()` class method, `_meta_schema()` |
| 3 | Canary: `modules/categories.py` | First real module with seed data |
| 4 | Canary: `modules/products.py` | All field types: FK, M2M, Decimal, Selection, Image |
| 5 | `app/main.py` update | Register canary modules + seed data startup |

**Exit criteria**: `GET /products/meta/schema` returns full JSON. All 9 endpoints work end-to-end.

### Phase 4: Advanced Features

**Goal**: Computed fields, bulk import, file upload, optimistic lock.

| # | File | Description |
|---|---|---|
| 1 | `base/computed.py` | Non-stored + stored computed field engine |
| 2 | `base/upload.py` | File/Image upload to `uploads/` + serve via static |
| 3 | Bulk handler in `handlers.py` | `POST /bulk` with atomic rollback |
| 4 | Optimistic lock in `handlers.py` | Version field check on PUT |
| 5 | `tests/test_filters.py` | Filter prefix syntax exhaustive tests |

**Exit criteria**: Products module with computed field + image upload works.

### Phase 5: Menu System + Settings System

**Goal**: `/modules/menu` endpoint, MenuGroup CRUD, Settings CRUD.

| # | File | Description |
|---|---|---|
| 1 | `system/models.py` | MenuGroup + SystemSetting SQLAlchemy models |
| 2 | Menu endpoint in `system/router.py` | `GET /modules/menu` aggregating all `_menu_*` attributes |
| 3 | MenuGroup CRUD in `system/router.py` | CRUD for MenuGroup (superuser-only) |
| 4 | Settings CRUD in `system/router.py` | `GET/PUT /system-settings/` |
| 5 | Settings seed in startup | Auto-seed `_settings` into `system_settings` table |

**Exit criteria**: Sidebar menu data from API. Settings read/write works.

## Testing Strategy

| Phase | Test Type | Tool |
|---|---|---|
| 1 | Unit | pytest — field → column mapping |
| 2 | Integration | httpx — CRUD endpoints + permission checks |
| 3 | E2E | httpx — full workflow: register module → CRUD → schema |
| 4 | Unit + Integration | pytest — computed fields, bulk rollback, filters |
| 5 | Integration | httpx — menu + settings endpoints |

**DB for tests**: SQLite in-memory (`sqlite+aiosqlite://`)

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Metaclass for TRCFBaseModule | Auto-generate model + schema + router from class definition | Simple base class without metaclass cannot intercept field definitions at class creation time |
| Filter prefix parser | Support 10 filter operators (>, >=, <, BETWEEN, IN...) | Simple equality filter insufficient for ERP data querying needs |
