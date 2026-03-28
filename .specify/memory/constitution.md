<!--
Sync Impact Report
- Version change: 1.0 → 2.0
- Modified principles:
  - I: "Soft delete" → "Archive (Odoo-style active field)" + removed hooks mention
  - III: Added SQL injection prevention, reset token SHA-256 hash, ALLOW_PUBLIC_REGISTER
  - IV: Removed "lifecycle hooks PHẢI là async" (hooks removed)
- Added sections:
  - Principle VIII: Module Đăng Ký Tường Minh (explicit registration, no auto-discovery)
  - Principle IX: Menu & Settings System
- Removed sections: none
- Templates requiring updates:
  - .specify/templates/spec-template.md ⚠ pending (manual review)
  - .specify/templates/plan-template.md ⚠ pending (manual review)
- Follow-up TODOs: none
-->

# CoffeeTree POS Constitution

## Core Principles

### I. CRUD Base Thuần — Khai Báo, Không Lặp Lại

Mọi module nghiệp vụ kế thừa `TRCFBaseModule` và CHỈ khai báo fields + class attributes.
Hệ thống tự sinh:
- SQLAlchemy model + Pydantic schemas
- 8 REST endpoints + `/meta/schema`
- Permission check + Audit trail + Archive (`active` field)
- Menu sidebar + Settings page
- **Developer viết < 10 dòng code** cho 1 module hoàn chỉnh

Cấm viết router/schema/query thủ công cho business modules.

**Không có lifecycle hooks.** TRCFBaseModule là CRUD base thuần.
Validation dùng Pydantic field options (`min_value`, `unique`, `required`) + DB constraints.
Business logic phức tạp → override handler method ở module kế thừa.

### II. CMS Core Tách Biệt

User, Group, GroupPermission, RefreshToken, MenuGroup, SystemSetting
là SQLAlchemy thuần — cố định, viết tay, **KHÔNG** kế thừa TRCFBaseModule.
- Tránh circular dependency (module system phụ thuộc auth, auth không phụ thuộc module system)
- CMS Core endpoints chỉ superuser truy cập
- JWT middleware inject state (`user_id`, `user_groups`, `user_is_superuser`) vào mọi request

### III. Security First

- Password: **bcrypt** hash, KHÔNG BAO GIỜ lưu plaintext
- Reset token: lưu **SHA-256 hash** trong DB (không lưu UUID plaintext)
- Auth: JWT HS256 với PyJWT, dual-token:
  - Access token (30 phút): `sub`, `exp`, `iat`, `jti`, `type`, `email`, `is_superuser`, `group_ids`
  - Refresh token (30 ngày): lưu DB, revoke khi logout
- JWTMiddleware PHẢI check `type="access"` — reject refresh token làm access token
- Permission: Group-based, query `group_permissions` table mỗi request
- Superuser bypass tất cả — nhưng phải có superuser, không có anonymous admin
- Auto-seed superuser từ `.env` khi khởi động lần đầu
- Register: `ALLOW_PUBLIC_REGISTER=false` — mặc định chỉ superuser tạo user
- **SQL injection:** Filter prefix PHẢI dùng parameterized queries (SQLAlchemy column operators).
  KHÔNG BAO GIỜ string concat SQL.

### IV. Async First

- Tất cả database operations dùng SQLAlchemy AsyncSession
- Tất cả endpoint handlers PHẢI là `async`
- Không dùng sync DB calls trong async context

### V. Không Cross-Module Inheritance

TRCFBaseModule **KHÔNG** thiết kế cho cross-module inheritance (kiểu Odoo `_inherit`):
- Mỗi module là 1 class độc lập, khai báo đầy đủ fields riêng
- Chia sẻ logic → dùng Python mixin thông thường
- Muốn thêm field → sửa trực tiếp class
- Giữ hệ thống đơn giản cho sử dụng nội bộ

### VI. Response Format Nhất Quán

Mọi endpoint (CMS Core + TRCFBaseModule) PHẢI trả cùng format:
```
Success: {success: true, data: ..., message: null}
Error:   {success: false, data: null, message: "...", errors: [...]}
```
Không có ngoại lệ. Frontend chỉ cần 1 wrapper để xử lý response.

### VII. Test Per Phase

- Mỗi phase implementation có test file riêng
- Test dùng SQLite in-memory (không phụ thuộc PostgreSQL khi test)
- pytest + pytest-asyncio + httpx async client
- Test CRUD cơ bản + edge cases + permission checks

### VIII. Module Đăng Ký Tường Minh

**Không dùng auto-discovery, không dùng Module Registry.**
Modules được import và đăng ký **tường minh** trong `main.py`:
```python
from modules.products import Product
app.include_router(Product.router())
```
- Giữ code sạch sẽ, rõ ràng, biết rõ app có những module nào
- Không có magic scanning, không metaclass registry
- Seed data + Settings seed cũng dùng danh sách tường minh

### IX. Archive Thay Vì Xóa (Odoo-Style)

Mặc định `_archive = True` — DELETE soft = `active = False`, không xóa khỏi DB:
- Mọi query tự lọc `WHERE active = TRUE`
- Partial unique index: `WHERE active = TRUE` → record lưu trữ không chiếm unique
- Restore endpoint: `POST /{name}/{id}/restore`
- Hard delete: `DELETE /{name}/{id}?hard=true` (cần permission `hard_delete`)
- `with_archived=true` chỉ hoạt động khi user đã đăng nhập

## Technology Stack

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.13 | Latest stable, async native |
| Web Framework | FastAPI 0.115 | Async, auto-docs, Pydantic integration |
| ORM | SQLAlchemy 2.0 Async | Mature, typed, async sessions |
| Validation | Pydantic v2 | Fast, native FastAPI support |
| DB (prod) | PostgreSQL + asyncpg | Reliable, JSONB, partial unique index |
| DB (test) | SQLite + aiosqlite | Fast, no setup needed |
| JWT | PyJWT 2.x | Lightweight, HS256 native |
| Password | bcrypt | Industry standard, simple API |
| Excel Import | openpyxl | .xlsx support |
| Testing | pytest + pytest-asyncio + httpx | Async testing ecosystem |

## Development Workflow

1. **Spec trước, code sau**: Mọi feature phải có spec.md + plan.md trước khi implement
2. **Phase-by-phase**: Implement theo đúng dependency graph:
   - Phase 0: JWT + CMS Core (`jwt_spec.md`)
   - Phase 1: TRCFBaseModule Core (`basemodule_spec.md`)
   - Phase 2+: Business Modules + Advanced Features
3. **Test mỗi phase**: Không chuyển phase mới khi phase hiện tại chưa pass tests
4. **Demo module canary**: `modules/product.py` luôn là test case đầu tiên cho mọi tính năng base mới

## Governance

- Constitution này là tài liệu governing chính — mọi design decision phải align
- Thay đổi constitution cần ghi rõ lý do và impact
- Khi có conflict giữa simplicity và feature → ưu tiên simplicity
- Spec references:
  - [1.jwt_spec.md](./../specs/001-trcf-base-module/1.jwt_spec.md)
  - [2.basemodule_spec.md](./../specs/001-trcf-base-module/2.basemodule_spec.md)

**Version**: 2.0 | **Ratified**: 2026-03-23 | **Last Amended**: 2026-03-24
