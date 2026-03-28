# API Contracts: Auth Endpoints

## Auth Router (`/auth/*`)

### POST /auth/login
- **Request**: `{"email": "string", "password": "string"}`
- **200**: `{"success": true, "data": {"access_token": "jwt", "refresh_token": "jwt", "token_type": "bearer", "expires_in": 1800, "user": {"id": 1, "email": "...", "full_name": "...", "is_superuser": false, "email_verified": true}}, "message": null}`
- **401**: `{"success": false, "data": null, "message": "Email hoặc mật khẩu không đúng"}`
- **403**: `{"success": false, "data": null, "message": "Tài khoản đã bị vô hiệu hoá"}`

### POST /auth/logout
- **Auth**: Bearer access_token
- **Request**: `{"refresh_token": "jwt"}`
- **200**: `{"success": true, "data": null, "message": "Đã đăng xuất"}`

### POST /auth/refresh
- **Request**: `{"refresh_token": "jwt"}`
- **200**: `{"success": true, "data": {"access_token": "jwt", "token_type": "bearer", "expires_in": 1800}, "message": null}`
- **401**: `{"success": false, "data": null, "message": "Refresh token không hợp lệ hoặc đã bị thu hồi"}`

### GET /auth/me
- **Auth**: Bearer access_token
- **200**: `{"success": true, "data": {"id": 1, "email": "...", "full_name": "...", "is_superuser": false, "email_verified": true}, "message": null}`
- **401**: `{"success": false, "data": null, "message": "Yêu cầu đăng nhập"}`

### POST /auth/set-password
- **Auth**: Bearer access_token
- **Request**: `{"current_password": "string", "new_password": "string (min 8)"}`
- **200**: `{"success": true, "data": null, "message": "Đổi mật khẩu thành công"}`
- **400**: `{"success": false, "data": null, "message": "Mật khẩu hiện tại không đúng"}`

### POST /auth/register
- **Condition**: `ALLOW_PUBLIC_REGISTER=true`
- **Request**: `{"email": "string", "password": "string (min 8)", "full_name": "string|null"}`
- **201**: `{"success": true, "data": {"id": 1, "email": "..."}, "message": "Đăng ký thành công. Kiểm tra email để xác minh."}`
- **403**: `{"success": false, "data": null, "message": "Đăng ký bị vô hiệu"}`
- **409**: `{"success": false, "data": null, "message": "Email đã được sử dụng"}`

### POST /auth/verify-email
- **Request**: `{"token": "jwt (24h, type=verify-email)"}`
- **200**: `{"success": true, "data": null, "message": "Email đã được xác minh"}`
- **400**: `{"success": false, "data": null, "message": "Token không hợp lệ hoặc đã hết hạn"}`

### POST /auth/forgot-password
- **Request**: `{"email": "string"}`
- **200**: `{"success": true, "data": null, "message": "Nếu email tồn tại, link reset đã được gửi"}`
- (Always 200 — never leak email existence)

### POST /auth/reset-password
- **Request**: `{"token": "uuid-string", "new_password": "string (min 8)"}`
- **200**: `{"success": true, "data": null, "message": "Đặt lại mật khẩu thành công"}`
- **400**: `{"success": false, "data": null, "message": "Token không hợp lệ hoặc đã hết hạn"}`

---

## System Router (`/users/*`, `/groups/*`, `/group-permissions/*`)

> All endpoints require superuser. Non-superuser → 403.

### CRUD /users/
- **GET /users/**: List users + group info
- **POST /users/**: Create user (email, password, full_name, is_active, is_superuser, group_ids)
- **GET /users/{id}**: User detail + groups
- **PUT /users/{id}**: Update user info, change groups
- **DELETE /users/{id}**: Deactivate user (is_active=False)

### CRUD /groups/
- **GET /groups/**: List groups
- **POST /groups/**: Create group (name, description)
- **GET /groups/{id}**: Group detail
- **PUT /groups/{id}**: Update group
- **DELETE /groups/{id}**: Delete group

### CRUD /group-permissions/
- **GET /group-permissions/**: List permissions (filter: group_id, module_name, action)
- **POST /group-permissions/**: Create permission
- **PUT /group-permissions/{id}**: Toggle allowed
- **DELETE /group-permissions/{id}**: Delete permission

### Meta Schema
- **GET /users/meta/schema**: Field metadata for frontend
- **GET /groups/meta/schema**: Field metadata for frontend
- **GET /group-permissions/meta/schema**: Field metadata for frontend
