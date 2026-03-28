# Tasks: TRCFBaseModule CRUD Framework

**Input**: Design documents from `/specs/002-trcf-base-module/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create `base/` package structure and install dependencies

- [x] T001 Create base package structure: `backend/base/__init__.py`
- [x] T002 [P] Create modules package: `backend/modules/__init__.py`
- [x] T003 [P] Create uploads directory: `backend/uploads/.gitkeep`
- [x] T004 [P] Add dependencies to `backend/requirements.txt`: openpyxl

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Field types and model factory — ALL user stories depend on this

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Implement 14 field type classes in `backend/base/fields.py` — CharField, TextField, IntField, FloatField, BooleanField, DateTimeField, DateField, JSONField, ForeignKeyField, ManyToManyField, DecimalField, SelectionField, FileField, ImageField
- [x] T006 Implement model factory in `backend/base/model_factory.py` — convert field definitions → SQLAlchemy model with auto-columns (id, created_at, updated_at, created_by, updated_by, active, version)
- [x] T007 Implement schema factory in `backend/base/schema_factory.py` — fields → Pydantic Create/Update/Response models via `create_model()`
- [x] T008 [P] Implement filter prefix parser in `backend/base/filters.py` — 10 operators (=, >, >=, <, <=, !=, IN, NOT IN, LIKE, BETWEEN)
- [x] T009 [P] Implement permission check helper in `backend/base/permissions.py` — query group_permissions, superuser bypass, public_actions check
- [x] T010 Implement TRCFBaseModule base class (partial) in `backend/base/module.py` — `_name`, class attributes, `__init_subclass__` hook to process fields

**Checkpoint**: Field types → SQLAlchemy model → Pydantic schema pipeline works

---

## Phase 3: User Story 1 - Khai báo module và tự sinh CRUD (Priority: P1) 🎯 MVP

**Goal**: Developer declares a class → gets 9 working CRUD endpoints + /meta/schema

**Independent Test**: Declare `Category(TRCFBaseModule)` with 2 fields → verify DB table created, 9 endpoints work, `/meta/schema` returns correct JSON

### Implementation for User Story 1

- [x] T011 [US1] Implement generic async CRUD handlers in `backend/base/handlers.py` — list (with search, filter, sort, pagination), get, create, update, delete
- [x] T012 [US1] Implement router factory in `backend/base/router_factory.py` — auto-generate FastAPI APIRouter with all 9 endpoints
- [x] T013 [US1] Complete TRCFBaseModule in `backend/base/module.py` — `.router()` classmethod, `_meta_schema()` method returning unified schema format
- [x] T014 [US1] Create canary module `backend/modules/categories.py` — `class Category(TRCFBaseModule)` with name, icon fields
- [x] T015 [US1] Register Category module in `backend/app/main.py` — `app.include_router(Category.router())`
- [ ] T016 [US1] Run Alembic migration: `alembic revision --autogenerate -m "add categories table"`
- [x] T017 [US1] Verify all 9 endpoints via manual API test (list, get, create, update, delete, meta/schema)

**Checkpoint**: Category module fully functional — MVP complete

---

## Phase 4: User Story 2 - Archive, Restore, Delete (Priority: P1)

**Goal**: Archive (soft delete), restore, and permanent delete working

**Independent Test**: Create record → archive → not in list → restore → back in list → delete → gone from DB

### Implementation for User Story 2

- [x] T018 [US2] Add archive handler in `backend/base/handlers.py` — `POST /{name}/{id}/archive` sets `active=False`
- [x] T019 [US2] Add restore handler in `backend/base/handlers.py` — `POST /{name}/{id}/restore` sets `active=True`
- [x] T020 [US2] Update list handler in `backend/base/handlers.py` — filter `WHERE active=TRUE` by default, support `?with_archived=true`
- [x] T021 [US2] Update get handler in `backend/base/handlers.py` — 404 if `active=False` (unless with_archived)
- [x] T022 [US2] Update router factory in `backend/base/router_factory.py` — conditionally add archive/restore endpoints based on `_archive` attribute
- [x] T023 [US2] Add `archive` flag to `/meta/schema` response in `backend/base/module.py`

**Checkpoint**: Archive/restore/delete cycle works for Category module

---

## Phase 5: User Story 3 - Permission Check tự động (Priority: P1)

**Goal**: Every endpoint auto-checks permissions via group_permissions table

**Independent Test**: User without `create` permission → POST → 403. Superuser → bypass all.

### Implementation for User Story 3

- [x] T024 [US3] Integrate permission check into CRUD handlers in `backend/base/handlers.py` — call `permissions.check_permission()` before each action
- [x] T025 [US3] Handle `_require_auth` and `_public_actions` in `backend/base/handlers.py` — skip auth for public actions
- [x] T026 [US3] Add superuser bypass logic in `backend/base/permissions.py`
- [x] T027 [US3] Inject `created_by`/`updated_by` from JWT state in `backend/base/handlers.py`
- [ ] T028 [US3] Test permission flow: create group → assign permission → verify access/deny

**Checkpoint**: Permission system fully integrated with CRUD handlers

---

## Phase 6: User Story 4 - List với search, filter, sort, pagination (Priority: P2)

**Goal**: Full query capabilities on list endpoint

**Independent Test**: Seed 20 products → test pagination, search, filter prefix, sort

### Implementation for User Story 4

- [x] T029 [US4] Implement ILIKE search across `_search_fields` in `backend/base/handlers.py` — OR logic
- [x] T030 [US4] Integrate filter prefix parser into list handler in `backend/base/handlers.py` — parse query params against `_filter_fields`
- [x] T031 [US4] Implement sort in list handler in `backend/base/handlers.py` — `sort_by` + `sort_desc` params, default from class attributes
- [x] T032 [US4] Implement pagination cap in `backend/base/handlers.py` — limit capped by `_max_page_size`
- [ ] T033 [US4] Auto-filterable columns (created_at, updated_at, created_by, updated_by) in `backend/base/handlers.py`

**Checkpoint**: List endpoint handles search + 10 filter operators + sort + pagination

---

## Phase 7: User Story 5 - Field Types đầy đủ (Priority: P2)

**Goal**: All 14 field types work correctly with DB, validation, and schema

**Independent Test**: Create Product module with all field types → verify DB columns, schema response, validation

### Implementation for User Story 5

- [x] T034 [P] [US5] Create canary module `backend/modules/products.py` — Product with all 14 field types (CharField, DecimalField, ForeignKeyField, M2M, SelectionField, ImageField, etc.)
- [ ] T035 [US5] Implement ForeignKey validation in `backend/base/handlers.py` — check FK exists in DB before create/update, return 422
- [x] T036 [US5] Implement ManyToMany handling in `backend/base/model_factory.py` — auto-generate junction table `{source}_{target}`
- [x] T037 [US5] Implement ManyToMany CRUD in `backend/base/handlers.py` — accept `[1,2,3]` array, manage junction rows
- [ ] T038 [US5] Implement SelectionField validation in `backend/base/handlers.py` — check value in `options` list, return 422
- [x] T039 [US5] Implement `_readonly_fields` stripping in `backend/base/handlers.py` — remove from update payload
- [x] T040 [US5] Register Product module in `backend/app/main.py` + run Alembic migration
- [ ] T041 [US5] Implement auto FK JOIN in list/get handlers in `backend/base/handlers.py` — eager load related records

**Checkpoint**: Products module with all field types works end-to-end

---

## Phase 8: User Story 6 - Audit Trail tự động (Priority: P2)

**Goal**: `created_by`/`updated_by` auto-injected at handler layer

**Independent Test**: Create record as user 5 → verify `created_by=5`. Update as user 8 → verify `updated_by=8`.

### Implementation for User Story 6

- [x] T042 [US6] Verify audit trail injection in `backend/base/handlers.py` — `created_by=user_id` on create, `updated_by=user_id` on update
- [x] T043 [US6] Handle null audit for public modules in `backend/base/handlers.py` — `created_by=null` when no auth
- [x] T044 [US6] Verify `created_at`/`updated_at` auto-set via SQLAlchemy server defaults in `backend/base/model_factory.py`

**Checkpoint**: Audit trail works for all modules

---

## Phase 9: User Story 7 - Computed Fields (Priority: P3)

**Goal**: Non-stored and stored computed fields working

**Independent Test**: Define `total = computed(qty * price)` → create record → verify total in response

### Implementation for User Story 7

- [x] T045 [US7] Implement computed field engine in `backend/base/computed.py` — `computed(fn, depends, store)` decorator/class
- [ ] T046 [US7] Integrate non-stored computed in list/get handlers in `backend/base/handlers.py` — calculate at runtime
- [ ] T047 [US7] Integrate stored computed in create/update handlers in `backend/base/handlers.py` — calculate and save to DB column
- [x] T048 [US7] Add `computed_fields` to `/meta/schema` response in `backend/base/module.py`

**Checkpoint**: Computed fields work in Product module (e.g., total_amount)

---

## Phase 10: User Story 8 - Bulk Import (Priority: P3)

**Goal**: `POST /bulk` with atomic rollback on failure

**Independent Test**: Bulk 10 records → success. Bulk with 1 invalid → rollback all.

### Implementation for User Story 8

- [x] T049 [US8] Implement bulk create handler in `backend/base/handlers.py` — accept JSON array, create all in single transaction
- [ ] T050 [US8] Implement bulk upsert logic in `backend/base/handlers.py` — if unique field matches, update instead of create
- [x] T051 [US8] Implement atomic rollback in `backend/base/handlers.py` — on any validation error, rollback all, return error list with row numbers
- [x] T052 [US8] Add `_bulk_fields` filtering in `backend/base/handlers.py` — only allow specified fields in bulk payload

**Checkpoint**: Bulk import works with rollback guarantee

---

## Phase 11: User Story 9 - Menu System (Priority: P3)

**Goal**: `/modules/menu` endpoint returns sidebar metadata

**Independent Test**: 3 modules with `_menu_*` → GET /modules/menu returns 3 items

### Implementation for User Story 9

- [ ] T053 [US9] Create MenuGroup model in `backend/system/models.py` — key, label, icon, sequence
- [ ] T054 [US9] Add MenuGroup CRUD endpoints in `backend/system/router.py` — superuser-only
- [ ] T055 [US9] Implement `GET /modules/menu` endpoint in `backend/system/router.py` — aggregate `_menu_*` attributes from all registered modules + `has_settings` flag
- [ ] T056 [US9] Add module registry list in `backend/app/main.py` — maintain list of registered TRCFBaseModule classes for menu endpoint
- [ ] T057 [US9] Run Alembic migration for menu_groups table

**Checkpoint**: Frontend can fetch sidebar menu data from API

---

## Phase 12: User Story 10 - Settings System (Priority: P3)

**Goal**: Module settings auto-seeded and manageable via API

**Independent Test**: Module with `_settings` → seed on startup → GET/PUT settings works

### Implementation for User Story 10

- [ ] T058 [US10] Create SystemSetting model in `backend/system/models.py` — module_name, key, value, value_type, label
- [ ] T059 [US10] Add `GET /system-settings/?module_name=` endpoint in `backend/system/router.py`
- [ ] T060 [US10] Add `PUT /system-settings/{module_name}/{key}` endpoint in `backend/system/router.py`
- [ ] T061 [US10] Implement settings auto-seed in `backend/app/main.py` — on startup, seed `_settings` into `system_settings` table
- [ ] T062 [US10] Implement `get_setting(module, key)` helper function in `backend/base/module.py`
- [ ] T063 [US10] Run Alembic migration for system_settings table + add `has_settings` to `/meta/schema`

**Checkpoint**: Settings read/write works for all modules

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Improvements across all user stories

- [x] T064 [P] Implement optimistic lock (version check) in PUT handler in `backend/base/handlers.py`
- [ ] T065 [P] Implement file/image upload handler in `backend/base/upload.py` — save to `uploads/`, return path
- [x] T066 [P] Mount static files in `backend/app/main.py` — serve `uploads/` via FastAPI StaticFiles
- [ ] T067 [P] Implement seed data loader in `backend/app/main.py` — `_seed_data` JSON loading on startup
- [ ] T068 Add `_module_seeds` tracking table + Alembic migration
- [ ] T069 [P] Write integration tests in `backend/tests/test_base_module.py` — CRUD cycle, permissions, archive/restore
- [ ] T070 [P] Write filter tests in `backend/tests/test_filters.py` — all 10 prefix operators
- [ ] T071 Update constitution.md `Principle IX` — align archive endpoint naming (remove `?hard=true` reference)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — core CRUD
- **US2 (Phase 4)**: Depends on US1 — archive extends CRUD handlers
- **US3 (Phase 5)**: Depends on US1 — permission integrates into handlers
- **US4 (Phase 6)**: Can start after US1 — search/filter extends list handler
- **US5 (Phase 7)**: Can start after US1 — field types are additive
- **US6 (Phase 8)**: Can start after US3 — audit depends on auth injection
- **US7-US10 (Phase 9-12)**: Can start after US1 — independent features
- **Polish (Phase 13)**: After all desired user stories complete

### User Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundation)
                        │
                        ├── US1 (CRUD Core) ← MVP
                        │       │
                        │       ├── US2 (Archive) ← extends handlers
                        │       ├── US3 (Permissions) ← integrates into handlers  
                        │       │       │
                        │       │       └── US6 (Audit Trail) ← depends on auth
                        │       │
                        │       ├── US4 (Search/Filter) ← extends list [P]
                        │       ├── US5 (Field Types) ← additive [P]
                        │       ├── US7 (Computed Fields) [P]
                        │       ├── US8 (Bulk Import) [P]
                        │       ├── US9 (Menu System) [P]
                        │       └── US10 (Settings) [P]
                        │
                        └── Phase 13 (Polish)
```

### Parallel Opportunities

After US1 completes, these can run in parallel:
- US4 (Search/Filter) + US5 (Field Types) + US7-US10

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (fields + model factory)
3. Complete Phase 3: US1 (CRUD Core)
4. **STOP and VALIDATE**: Category module works end-to-end
5. Demo: declare class → 9 endpoints + /meta/schema

### Incremental Delivery

1. Setup + Foundation → Field pipeline works
2. US1 → CRUD Core MVP ✅
3. US2 + US3 → Archive + Permissions ✅
4. US4 + US5 → Search/Filter + All Field Types ✅
5. US6-US10 → Advanced features ✅
6. Polish → Tests, optimistic lock, file upload

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Total tasks: **71**
