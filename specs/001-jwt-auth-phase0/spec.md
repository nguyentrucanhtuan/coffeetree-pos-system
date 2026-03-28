# Feature Specification: JWT Authentication & CMS Core

**Feature Branch**: `001-jwt-auth-phase0`
**Created**: 2026-03-24
**Status**: Draft
**Input**: Implement Phase 0 — JWT authentication system and CMS Core models (User, Group, GroupPermission, RefreshToken) as the foundation layer for TRCFBaseModule.
**Reference**: [1.jwt_spec.md](../../.specify/specs/001-trcf-base-module/1.jwt_spec.md)

## User Scenarios & Testing

### User Story 1 - Đăng Nhập Hệ Thống (Priority: P1)

Nhân viên POS nhập email/password → nhận access token + refresh token → sử dụng hệ thống.

**Why this priority**: Không có đăng nhập thì không có gì hoạt động. Mọi module nghiệp vụ đều phụ thuộc JWT state.

**Independent Test**: Gửi `POST /auth/login` → nhận token → dùng token gọi `GET /auth/me` → nhận thông tin user.

**Acceptance Scenarios**:

1. **Given** user tồn tại và active, **When** POST /auth/login với đúng email/password, **Then** trả access_token + refresh_token + user info (200)
2. **Given** email/password sai, **When** POST /auth/login, **Then** trả 401 "Email hoặc mật khẩu không đúng"
3. **Given** user bị vô hiệu (is_active=False), **When** POST /auth/login đúng password, **Then** trả 403 "Tài khoản đã bị vô hiệu hoá"
4. **Given** user đã đăng nhập, **When** GET /auth/me với Bearer token, **Then** trả thông tin user (id, email, full_name, is_superuser, email_verified)

---

### User Story 2 - Superuser Tự Động Tạo Khi Khởi Động (Priority: P1)

Khi app khởi động lần đầu (DB trống), hệ thống tự tạo superuser từ `.env` config → admin đăng nhập ngay.

**Why this priority**: Không có superuser → không tạo được user nào khác, hệ thống bế tắc.

**Independent Test**: Khởi động app với DB trống → kiểm tra bảng users có đúng 1 superuser với email từ `.env`.

**Acceptance Scenarios**:

1. **Given** bảng users trống, **When** app khởi động, **Then** tự tạo superuser với email/password từ .env
2. **Given** bảng users đã có user, **When** app khởi động, **Then** KHÔNG tạo thêm user nào

---

### User Story 3 - Quản Lý Users, Groups, Permissions (Priority: P1)

Superuser quản lý toàn bộ hệ thống qua CMS Core API: tạo/sửa/xóa users, groups, và phân quyền cho mỗi module/action.

**Why this priority**: TRCFBaseModule cần group_permissions để check quyền → phải có CRUD cho permissions trước.

**Independent Test**: Superuser tạo Group "Nhân viên" → tạo GroupPermission cho products.list/read → user trong group đó chỉ xem được products.

**Acceptance Scenarios**:

1. **Given** superuser đăng nhập, **When** POST /users/ với email + password, **Then** tạo user mới thành công
2. **Given** superuser đăng nhập, **When** POST /groups/ với name "Thu ngân", **Then** tạo group thành công
3. **Given** superuser đăng nhập, **When** POST /group-permissions/ với group_id + module_name + action, **Then** tạo permission thành công
4. **Given** user thường đăng nhập, **When** truy cập /users/ hoặc /groups/, **Then** trả 403
5. **Given** superuser xóa group đang có users, **When** DELETE /groups/{id}, **Then** hệ thống xử lý đúng (xóa hoặc báo conflict)

---

### User Story 4 - Refresh Token & Logout (Priority: P2)

Khi access token hết hạn (30 phút), frontend dùng refresh token đổi access token mới mà không cần đăng nhập lại. Khi logout, revoke refresh token.

**Why this priority**: Trải nghiệm liên tục — user không bị mất session khi làm việc.

**Independent Test**: Login → nhận refresh_token → POST /auth/refresh → nhận access_token mới → POST /auth/logout → POST /auth/refresh lại → 401.

**Acceptance Scenarios**:

1. **Given** có refresh_token hợp lệ, **When** POST /auth/refresh, **Then** trả access_token mới
2. **Given** refresh_token đã revoke, **When** POST /auth/refresh, **Then** trả 401
3. **Given** refresh_token hết hạn (>30 ngày), **When** POST /auth/refresh, **Then** trả 401
4. **Given** đã đăng nhập, **When** POST /auth/logout, **Then** revoke refresh_token trong DB

---

### User Story 5 - Đổi Mật Khẩu (Priority: P2)

User đã đăng nhập muốn đổi mật khẩu: nhập password cũ + password mới → password được update.

**Why this priority**: Bảo mật — superuser tạo user với password tạm, user cần đổi sau khi login lần đầu.

**Independent Test**: Login → POST /auth/set-password với current_password + new_password → login lại bằng password mới.

**Acceptance Scenarios**:

1. **Given** đã đăng nhập, **When** POST /auth/set-password với đúng current_password, **Then** đổi password thành công
2. **Given** đã đăng nhập, **When** POST /auth/set-password với sai current_password, **Then** trả 400
3. **Given** new_password < 8 ký tự, **When** POST /auth/set-password, **Then** trả 422 validation error

---

### User Story 6 - Quên Mật Khẩu & Reset (Priority: P3)

User quên password → nhập email → nhận link reset qua email → click link → nhập password mới.

**Why this priority**: Cần thiết nhưng không blocking cho Phase 1. SMTP có thể chạy console log mode khi dev.

**Independent Test**: POST /auth/forgot-password → check email (hoặc console log) → POST /auth/reset-password với token → login bằng password mới.

**Acceptance Scenarios**:

1. **Given** email tồn tại, **When** POST /auth/forgot-password, **Then** tạo reset token (SHA-256 hash lưu DB) + gửi email
2. **Given** email không tồn tại, **When** POST /auth/forgot-password, **Then** vẫn trả 200 (không leak thông tin)
3. **Given** có reset token hợp lệ (<1h), **When** POST /auth/reset-password, **Then** đổi password + xóa token
4. **Given** reset token hết hạn (>1h), **When** POST /auth/reset-password, **Then** trả 400

---

### User Story 7 - Đăng Ký & Xác Minh Email (Priority: P3)

Nếu `ALLOW_PUBLIC_REGISTER=true`, user tự đăng ký tài khoản → nhận email xác minh → xác minh.

**Why this priority**: POS F&B thường không cho khách đăng ký. Feature này mặc định tắt.

**Independent Test**: Bật flag → POST /auth/register → check console log email → POST /auth/verify-email → user.email_verified=True.

**Acceptance Scenarios**:

1. **Given** ALLOW_PUBLIC_REGISTER=true, **When** POST /auth/register với email hợp lệ, **Then** tạo user (email_verified=False) + gửi verify email
2. **Given** ALLOW_PUBLIC_REGISTER=false, **When** POST /auth/register, **Then** trả 403 "Đăng ký bị vô hiệu"
3. **Given** có verify token hợp lệ (JWT 24h), **When** POST /auth/verify-email, **Then** set email_verified=True
4. **Given** verify token hết hạn, **When** POST /auth/verify-email, **Then** trả 400

---

### Edge Cases

- JWTMiddleware nhận refresh token thay access token → reject (check `type` claim)
- Access token thiếu required claims (`sub`, `exp`, `iat`, `jti`) → 401
- Multiple concurrent logins → mỗi login tạo refresh token riêng, tất cả hoạt động
- User bị vô hiệu giữa chừng (is_active=False) → access token hiện tại vẫn work đến hết hạn (30 phút)
- Password reset 2 lần liên tiếp → token đầu tiên bị invalidate khi token mới tạo

## Requirements

### Functional Requirements

- **FR-001**: Hệ thống PHẢI hash password bằng bcrypt, KHÔNG BAO GIỜ lưu plaintext
- **FR-002**: Hệ thống PHẢI tạo access token (JWT HS256, 30 phút) chứa claims: `sub`, `exp`, `iat`, `jti`, `type`, `email`, `is_superuser`, `group_ids`
- **FR-003**: Hệ thống PHẢI tạo refresh token (JWT HS256, 30 ngày) lưu trong DB với khả năng revoke
- **FR-004**: JWTMiddleware PHẢI inject `user_id`, `user_groups`, `user_is_superuser` vào `request.state` cho mọi request
- **FR-005**: JWTMiddleware PHẢI check `type="access"` và reject refresh token dùng làm access token
- **FR-006**: Hệ thống PHẢI cung cấp 9 auth endpoints: login, logout, refresh, register, verify-email, forgot-password, reset-password, set-password, me
- **FR-007**: Hệ thống PHẢI cung cấp CMS Core endpoints (superuser-only): CRUD users, groups, group-permissions
- **FR-008**: Hệ thống PHẢI tự tạo superuser từ `.env` khi khởi động lần đầu (bảng users trống)
- **FR-009**: Reset token PHẢI lưu SHA-256 hash trong DB, hết hạn sau 1h
- **FR-010**: Register PHẢI bị block mặc định (ALLOW_PUBLIC_REGISTER=false)
- **FR-011**: Verify-email token PHẢI có `exp` (24h) và `type="verify-email"`
- **FR-012**: Mọi response PHẢI theo format: `{success, data, message}`
- **FR-013**: SMTP email PHẢI support dev mode (console log khi SMTP_HOST trống)
- **FR-014**: `/meta/schema` endpoint cho users, groups, group-permissions (superuser-only)

### Key Entities

- **User**: Tài khoản đăng nhập (email, password_hash, is_active, is_superuser, email_verified, password_reset_token, password_reset_at)
- **Group**: Nhóm quyền (name, description). Quan hệ M2M với User qua bảng user_groups
- **GroupPermission**: Phân quyền chi tiết (group_id, module_name, action, allowed). Quyết định user thuộc group nào được làm gì trên module nào
- **RefreshToken**: Lưu refresh token đã cấp (user_id, jti, expires_at, revoked). Dùng để revoke khi logout

## Success Criteria

### Measurable Outcomes

- **SC-001**: Superuser có thể đăng nhập và quản lý users/groups/permissions trong 2 phút đầu tiên sau khi khởi động
- **SC-002**: Mọi request có JWT hợp lệ đều nhận được `request.state.user_id` đúng — 100% requests
- **SC-003**: User không có quyền truy cập module bị chặn (403) — 100% trường hợp, không có bypass ngoài superuser
- **SC-004**: Refresh token flow hoạt động liền mạch — user không cần đăng nhập lại trong 30 ngày (trừ khi logout)
- **SC-005**: Reset password flow hoàn thành end-to-end: quên → nhận email → reset → login bằng password mới
- **SC-006**: Tất cả test cases pass: CRUD users, CRUD groups, permission check, JWT lifecycle, edge cases

## Clarifications

### Session 2026-03-24

- Q: Có cần brute-force protection (rate limit / lock account) cho login endpoint không? → A: Không cần ở Phase 0 — mạng nội bộ tin cậy. Có thể thêm ở phase sau nếu cần.
- Q: Có giới hạn số concurrent sessions (refresh tokens) cho mỗi user không? → A: Không giới hạn — mỗi thiết bị có refresh_token riêng, tất cả hoạt động song song.
