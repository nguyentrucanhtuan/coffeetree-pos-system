# Feature Specification: TRCFBaseModule CRUD Framework

**Feature Branch**: `002-trcf-base-module`  
**Created**: 2026-03-26  
**Status**: Draft  
**Input**: User description: "TRCFBaseModule CRUD Framework - Auto-generate DB models, schemas, CRUD endpoints, and dynamic UI from Python class definitions"

## Clarifications

### Session 2026-03-26

- Q: Khi developer thay đổi fields trong module, hệ thống xử lý schema DB thế nào? → A: Alembic auto-generate migrations (dev chạy `alembic revision --autogenerate`)
- Q: Bulk import thất bại giữa chừng thì xử lý thế nào? → A: Rollback toàn bộ — nếu bất kỳ record nào lỗi, rollback all, trả lỗi chi tiết
- Q: File/Image upload lưu ở đâu? → A: Local filesystem (thư mục `uploads/`, serve qua FastAPI static files)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Khai báo module và tự sinh CRUD (Priority: P1)

Developer khai báo một Python class kế thừa `TRCFBaseModule` với các field definitions. Hệ thống tự động sinh ra: bảng DB (SQLAlchemy model), Pydantic schemas, async CRUD handlers, 9 REST endpoints, và `/meta/schema` endpoint trả JSON cho frontend.

**Why this priority**: Đây là core value — toàn bộ framework phụ thuộc vào khả năng auto-generate từ class definition. Không có phần này, không có gì khác hoạt động được.

**Independent Test**: Khai báo 1 class `Category(TRCFBaseModule)` với 2 fields → verify DB table được tạo, 9 endpoints hoạt động, `/meta/schema` trả JSON đúng format.

**Acceptance Scenarios**:

1. **Given** developer khai báo `class Category(TRCFBaseModule)` với `name = fields.CharField(required=True)`, **When** app startup, **Then** bảng DB `categories` được tạo với columns: id, name, created_at, updated_at, created_by, updated_by, active
2. **Given** module Category đã đăng ký, **When** gọi `GET /categories/meta/schema`, **Then** trả JSON với `module: "categories"`, `fields` array, `search_fields`, `filter_fields`, `sort_by`, `sort_desc`, `archive`, `has_settings`, `computed_fields`
3. **Given** module Category đã đăng ký, **When** gọi `POST /categories/` với body `{"name": "Đồ uống"}`, **Then** tạo record mới và trả về record với id + timestamps

---

### User Story 2 - Archive, Restore, Delete (Priority: P1)

Người dùng có thể lưu trữ (archive) bản ghi thay vì xóa, khôi phục bản ghi đã lưu trữ, hoặc xóa vĩnh viễn. Đây là cơ chế giống Odoo `active` field.

**Why this priority**: Archive là tính năng bảo vệ dữ liệu quan trọng cho hệ thống ERP/POS — ngăn xóa nhầm.

**Independent Test**: Tạo 1 record → archive → verify không hiện trong list → restore → verify lại hiện → delete → verify bị xóa khỏi DB.

**Acceptance Scenarios**:

1. **Given** record `Category(id=1)` đang active, **When** gọi `POST /categories/1/archive`, **Then** `active=False`, record không xuất hiện trong `GET /categories/`
2. **Given** record đã archive, **When** gọi `GET /categories/?with_archived=true`, **Then** record xuất hiện trong danh sách (chỉ khi user đã đăng nhập)
3. **Given** record đã archive, **When** gọi `POST /categories/1/restore`, **Then** `active=True`, record xuất hiện lại trong list
4. **Given** record tồn tại, **When** gọi `DELETE /categories/1`, **Then** record bị xóa vật lý khỏi DB
5. **Given** module có `_archive=False`, **When** không có endpoint `/archive` và `/restore`, **Then** chỉ có endpoint `DELETE` (xóa vật lý)

---

### User Story 3 - Permission Check tự động (Priority: P1)

Mọi endpoint tự động kiểm tra quyền dựa trên bảng `group_permissions` (CMS Core). Developer không cần viết code permission trong module. Superuser bypass tất cả.

**Why this priority**: Bảo mật — mọi request phải được kiểm tra quyền tự động mà dev không cần làm gì thêm.

**Independent Test**: Tạo user thuộc group không có quyền `create` cho `products` → gọi `POST /products/` → verify trả 403.

**Acceptance Scenarios**:

1. **Given** user chưa đăng nhập và module có `_require_auth=True`, **When** gọi bất kỳ endpoint, **Then** trả 401
2. **Given** user đăng nhập nhưng group không có permission `create` cho module `products`, **When** gọi `POST /products/`, **Then** trả 403
3. **Given** user là superuser, **When** gọi bất kỳ endpoint của bất kỳ module, **Then** bypass tất cả permission check
4. **Given** module có `_require_auth=False`, **When** request không có token, **Then** cho phép truy cập
5. **Given** module có `_public_actions=["list", "read"]`, **When** request không có token gọi `GET /products/`, **Then** cho phép, nhưng `POST /products/` → 401

---

### User Story 4 - List với search, filter, sort, pagination (Priority: P2)

Endpoint `GET /{name}/` hỗ trợ phân trang, tìm kiếm text trên `_search_fields`, filter với prefix syntax trên `_filter_fields`, và sort tùy chỉnh.

**Why this priority**: List là endpoint được gọi nhiều nhất — phải hỗ trợ đầy đủ query capabilities.

**Independent Test**: Seed 20 products → test phân trang `?skip=0&limit=10` → test search `?search=coffee` → test filter `?price=[>=]25000` → verify kết quả đúng.

**Acceptance Scenarios**:

1. **Given** 25 products trong DB, **When** gọi `GET /products/?skip=0&limit=10`, **Then** trả `{total: 25, items: 10 records, skip: 0, limit: 10}`
2. **Given** products có name chứa "coffee", **When** gọi `GET /products/?search=coffee`, **Then** trả chỉ records có name ILIKE '%coffee%'
3. **Given** products có price khác nhau, **When** gọi `GET /products/?price=[>=]25000`, **Then** trả chỉ records có price >= 25000
4. **Given** module có `_sort_by="name"`, **When** gọi `GET /products/`, **Then** kết quả sort theo name ascending mặc định
5. **Given** query có `sort_by=price&sort_desc=true`, **When** gọi, **Then** sort theo price giảm dần

---

### User Story 5 - Field Types đầy đủ (Priority: P2)

Hệ thống hỗ trợ đầy đủ field types: CharField, TextField, IntField, FloatField, BooleanField, DateTimeField, DateField, JSONField, ForeignKeyField, ManyToManyField, DecimalField, SelectionField, FileField, ImageField. Mỗi type tự sinh đúng DB column, validation, và schema response.

**Why this priority**: Không có field types đa dạng, developer không thể mô tả được data model thực tế.

**Independent Test**: Khai báo module với mỗi loại field → verify DB columns đúng type, schema response chứa đầy đủ metadata, validation hoạt động.

**Acceptance Scenarios**:

1. **Given** field `price = fields.DecimalField(precision=12, scale=2)`, **When** schema generated, **Then** DB column là `NUMERIC(12,2)`, schema trả `{"type": "decimal", "precision": 12, "scale": 2}`
2. **Given** field `category_id = fields.ForeignKeyField(to="categories")`, **When** tạo record với `category_id=999` (không tồn tại), **Then** trả 422 validation error
3. **Given** field `status = fields.SelectionField(options=["draft", "active", "done"])`, **When** tạo record với `status="invalid"`, **Then** trả 422
4. **Given** field `tags = fields.ManyToManyField(to="tags")`, **When** tạo record, **Then** tự sinh bảng trung gian `{module}_tags`

---

### User Story 6 - Audit Trail tự động (Priority: P2)

Mỗi record tự động ghi `created_by`, `updated_by` (user ID) ở handler layer. Developer không cần làm gì.

**Why this priority**: Audit trail là yêu cầu cơ bản cho hệ thống ERP — biết ai tạo/sửa record.

**Independent Test**: Tạo record → verify `created_by` = user ID. Sửa record → verify `updated_by` = user ID.

**Acceptance Scenarios**:

1. **Given** user ID=5 đăng nhập, **When** tạo record mới, **Then** `created_by=5`, `created_at` = thời điểm hiện tại
2. **Given** user ID=8 đăng nhập, **When** sửa record, **Then** `updated_by=8`, `updated_at` = thời điểm hiện tại
3. **Given** request không có auth (public module), **When** tạo record, **Then** `created_by=null`

---

### User Story 7 - Computed Fields (Priority: P3)

Developer khai báo computed fields (non-stored và stored) với function compute + depends. Non-stored tính khi query. Stored tính khi create/update và lưu vào DB.

**Why this priority**: Computed fields (tổng tiền, trạng thái tự động...) cần thiết cho logic nghiệp vụ nhưng không phải MVP.

**Independent Test**: Khai báo `total_amount` computed từ `quantity * unit_price` → tạo record → verify `total_amount` trả đúng giá trị.

**Acceptance Scenarios**:

1. **Given** field `total = computed(fn=lambda r: r.qty * r.price, depends=["qty", "price"])`, **When** tạo record `{qty: 5, price: 10000}`, **Then** response chứa `total: 50000`
2. **Given** stored computed field, **When** create/update, **Then** giá trị được lưu vào DB column
3. **Given** non-stored computed field, **When** list/get, **Then** giá trị được tính runtime, không có column trong DB

---

### User Story 8 - Bulk Import (Priority: P3)

Endpoint `POST /{name}/bulk` hỗ trợ import nhiều records qua JSON hoặc Excel file. Tạo mới nếu chưa có, update nếu trùng unique field.

**Why this priority**: Import hàng loạt cần thiết cho setup ban đầu nhưng không phải MVP.

**Independent Test**: Upload JSON với 10 records → verify 10 records được tạo. Upload lại → verify update không duplicate.

**Acceptance Scenarios**:

1. **Given** body `[{"name": "A"}, {"name": "B"}]`, **When** gọi `POST /products/bulk`, **Then** tạo 2 records mới
2. **Given** record `{name: "A"}` đã tồn tại (unique field), **When** bulk với `{name: "A", price: 99}`, **Then** update record thay vì tạo mới

---

### User Story 9 - Menu System (Priority: P3)

Module khai báo `_menu_*` attributes → endpoint `GET /modules/menu` trả metadata để frontend tự render sidebar. Kết hợp với `GET /menu-groups/` cho nhóm menu.

**Why this priority**: Menu tự động là tiện ích UX, nhưng frontend có thể hardcode menu trong giai đoạn đầu.

**Independent Test**: Khai báo 3 modules với `_menu_*` → gọi `GET /modules/menu` → verify trả đúng 3 items với label, icon, parent, sequence, has_settings.

**Acceptance Scenarios**:

1. **Given** module `Product` có `_menu_label="Thực đơn"`, `_menu_icon="☕"`, `_menu_parent="inventory"`, **When** gọi `GET /modules/menu`, **Then** trả item `{name: "products", menu_label: "Thực đơn", menu_icon: "☕", menu_parent: "inventory", has_settings: false}`
2. **Given** module có `_menu_hidden=True`, **When** gọi `GET /modules/menu`, **Then** module không xuất hiện trong response

---

### User Story 10 - Settings System (Priority: P3)

Module khai báo `_settings` → hệ thống tự seed vào bảng `system_settings`. Superuser chỉnh qua API. Developer đọc qua helper function.

**Why this priority**: Settings cần cho cấu hình runtime nhưng có thể dùng hardcode trong giai đoạn đầu.

**Independent Test**: Khai báo module với 2 settings → verify seed vào DB → GET lấy values → PUT sửa → verify thay đổi.

**Acceptance Scenarios**:

1. **Given** module `Attendance` có `_settings=[{key: "late_min", type: "integer", default: 15}]`, **When** app startup, **Then** bảng `system_settings` có row `{module_name: "attendances", key: "late_min", value: "15"}`
2. **Given** setting đã seed, **When** gọi `PUT /system-settings/attendances/late_min` body `{value: "30"}`, **Then** giá trị cập nhật thành "30"

---

### Edge Cases

- Module khai báo `_name` trùng với module khác → hệ thống báo lỗi khi startup
- Field `ForeignKeyField(to="nonexistent")` → lỗi rõ ràng khi tạo model
- `_max_page_size` vượt quá → limit bị capped, không báo lỗi
- `with_archived=true` khi request không có auth → param bị bỏ qua (chỉ hiện active records)
- Optimistic lock conflict: PUT với `version` cũ → 409 Conflict
- Bulk import với file lớn (>1000 rows) → cần xử lý chunked. Nếu bất kỳ record nào lỗi validation → rollback toàn bộ, trả danh sách lỗi chi tiết (row number + error message)
- ForeignKey field pointing to module chưa đăng ký → lỗi tường minh khi startup

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST auto-generate SQLAlchemy model from class field definitions
- **FR-002**: System MUST auto-generate Pydantic schemas (Create, Update, Response) from fields
- **FR-003**: System MUST auto-generate 9 async CRUD endpoints (list, get, create, update, archive, restore, delete, bulk, meta/schema)
- **FR-004**: System MUST auto-add columns: id, created_at, updated_at, created_by, updated_by, active (if _archive=True), version (if _optimistic_lock=True)
- **FR-005**: System MUST check permissions automatically via group_permissions table before each action
- **FR-006**: System MUST support superuser bypass for all permission checks
- **FR-007**: System MUST support 14 field types: CharField, TextField, IntField, FloatField, BooleanField, DateTimeField, DateField, JSONField, ForeignKeyField, ManyToManyField, DecimalField, SelectionField, FileField, ImageField
- **FR-008**: System MUST validate ForeignKey references exist in DB before create/update
- **FR-009**: System MUST validate SelectionField values against defined options
- **FR-010**: System MUST support filter prefix syntax: =, >, >=, <, <=, !=, IN, NOT IN, LIKE, BETWEEN
- **FR-011**: System MUST support ILIKE search across `_search_fields` (OR logic)
- **FR-012**: System MUST support pagination with skip/limit (capped by _max_page_size)
- **FR-013**: System MUST support archive (set active=False) and restore (set active=True)
- **FR-014**: System MUST return unified schema format from `/meta/schema`: module, description, fields, search_fields, filter_fields, sort_by, sort_desc, archive, has_settings, computed_fields
- **FR-015**: System MUST inject created_by/updated_by automatically at handler layer
- **FR-016**: System MUST support computed fields (non-stored and stored with depends)
- **FR-017**: System MUST support bulk create/update via JSON with atomic transaction (rollback all if any record fails validation)
- **FR-018**: System MUST expose `/modules/menu` endpoint with _menu_* metadata + has_settings
- **FR-019**: System MUST support seed data from JSON file (`_seed_data`)
- **FR-020**: System MUST support module settings via `_settings` → `system_settings` table
- **FR-021**: System MUST use parameterized queries for all filter operations (prevent SQL injection)
- **FR-022**: System MUST support `_readonly_fields` — strip from update payload
- **FR-023**: System MUST support `_public_actions` — bypass auth for specified actions
- **FR-024**: System MUST generate SQLAlchemy models compatible with Alembic auto-generate migrations (`alembic revision --autogenerate`)

### Key Entities

- **TRCFBaseModule**: Python metaclass/base class that developers inherit from. Contains all class attributes for configuration (`_name`, `_archive`, `_search_fields`, etc.)
- **Field Types**: 14 field type classes that map to DB columns, Pydantic types, and frontend schema
- **Computed Field**: Function-based field with `depends` list. Non-stored = calculated at runtime. Stored = persisted in DB column
- **MenuGroup**: CMS Core model for grouping modules in sidebar (key, label, icon, sequence)
- **SystemSetting**: CMS Core model for module-level runtime settings (module_name, key, value, value_type, label)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developer can define a new module in under 20 lines of code and have full CRUD + permissions + schema working
- **SC-002**: Adding a new module requires zero frontend code changes (frontend auto-renders from schema)
- **SC-003**: All 9 endpoints per module respond correctly to CRUD operations with proper HTTP status codes
- **SC-004**: Permission check adds less than 5ms overhead per request
- **SC-005**: List endpoint handles 10,000+ records with pagination without degradation
- **SC-006**: Schema response format is 100% consistent between CMS Core and TRCFBaseModule modules
- **SC-007**: All filter operations use parameterized queries (zero SQL injection vectors)
- **SC-008**: Audit trail (created_by/updated_by) is recorded for 100% of write operations by authenticated users

## Assumptions

- CMS Core (auth, users, groups, group_permissions) is already implemented and running
- PostgreSQL or SQLite is the database (SQLAlchemy async compatible)
- FastAPI + Pydantic v2 + SQLAlchemy 2.0 async is the tech stack
- Frontend (Next.js) consumes `/meta/schema` JSON to auto-render UI
- ForeignKey `display_field` convention: default is `name` unless explicitly specified
- CORS middleware is configured to allow frontend origin
- DB schema changes are managed via Alembic auto-generate migrations
- File/Image uploads stored on local filesystem (`uploads/` directory), served via FastAPI static files
