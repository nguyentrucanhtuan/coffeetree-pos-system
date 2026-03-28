# Data Model: JWT Authentication & CMS Core

**Feature**: `001-jwt-auth-phase0` | **Date**: 2026-03-24

## Entity Relationship

```
User ──M2M──> Group ──1:N──> GroupPermission
  │
  └──1:N──> RefreshToken
```

## Entities

### User

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | Integer | PK, auto-increment | |
| email | String(255) | UNIQUE, NOT NULL, indexed | Login identifier |
| password_hash | String(255) | NOT NULL | bcrypt hash, never exposed |
| full_name | String(255) | nullable | Display name |
| is_active | Boolean | NOT NULL, default=True | False = vô hiệu hoá |
| is_superuser | Boolean | NOT NULL, default=False | Bypass all permission checks |
| email_verified | Boolean | NOT NULL, default=False | Email xác minh |
| password_reset_token | String(255) | nullable | SHA-256 hash of UUID |
| password_reset_at | DateTime(tz) | nullable | Token creation time (TTL 1h) |
| created_at | DateTime(tz) | server_default=now() | |
| updated_at | DateTime(tz) | onupdate=now() | |

**Relationships**: M2M → Group (via user_groups)

### Group

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | Integer | PK, auto-increment | |
| name | String(255) | UNIQUE, NOT NULL | "Thu ngân", "Quản lý" |
| description | Text | nullable | |
| created_at | DateTime(tz) | server_default=now() | |

### GroupPermission

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | Integer | PK, auto-increment | |
| group_id | Integer | FK→groups.id, NOT NULL, indexed | |
| module_name | String(255) | NOT NULL | "products", "orders" |
| action | String(50) | NOT NULL | list\|read\|create\|update\|archive\|restore\|delete\|bulk |
| allowed | Boolean | default=True | |
| created_at | DateTime(tz) | server_default=now() | |

**Unique constraint**: (group_id, module_name, action)

### RefreshToken

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | Integer | PK, auto-increment | |
| user_id | Integer | FK→users.id, NOT NULL, indexed | |
| jti | String(255) | UNIQUE, NOT NULL, indexed | JWT ID from token |
| expires_at | DateTime(tz) | NOT NULL | 30 days from creation |
| revoked | Boolean | NOT NULL, default=False | True on logout |
| created_at | DateTime(tz) | server_default=now() | |

### user_groups (M2M junction)

| Field | Type | Constraints |
|-------|------|-------------|
| user_id | Integer | PK, FK→users.id |
| group_id | Integer | PK, FK→groups.id |

## State Transitions

### User Lifecycle

```
Created (is_active=True, email_verified=False)
  → Email verified (email_verified=True)
  → Deactivated (is_active=False) ← superuser action
  → Reactivated (is_active=True) ← superuser action
```

### RefreshToken Lifecycle

```
Created (revoked=False)
  → Revoked (revoked=True) ← on logout
  → Expired (expires_at < now) ← natural expiry
```

### Password Reset Flow

```
No token (password_reset_token=NULL)
  → Token created (password_reset_token=SHA256(uuid), password_reset_at=now)
  → Token used (password changed, token cleared to NULL)
  → Token expired (password_reset_at + 1h < now)
```
