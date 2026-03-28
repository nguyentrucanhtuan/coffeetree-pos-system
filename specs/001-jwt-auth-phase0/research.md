# Research: JWT Authentication & CMS Core

**Feature**: `001-jwt-auth-phase0` | **Date**: 2026-03-24

## Technology Decisions

### JWT Library: PyJWT 2.x

- **Decision**: PyJWT 2.x (`pip install pyjwt`)
- **Rationale**: Lightweight, HS256 native, simple API, well-maintained
- **Alternatives considered**: python-jose (heavier, more algorithms than needed), authlib (full OAuth2 — overkill for internal POS)

### Password Hashing: bcrypt

- **Decision**: bcrypt via `pip install bcrypt`
- **Rationale**: Industry standard, cost factor for brute-force protection, simple API
- **Alternatives**: argon2id (better but more complex setup), passlib (wrapper — unnecessary)

### Reset Token Storage: SHA-256

- **Decision**: Hash reset tokens with SHA-256 before DB storage
- **Rationale**: UUID tokens have high entropy (128-bit) — slow hash unnecessary. SHA-256 prevents DB leak → token reuse
- **Alternatives**: bcrypt (too slow for already-random tokens), plaintext (DB leak = account takeover)

### Dual-Token Strategy

- **Decision**: Access token (30m, stateless) + Refresh token (30d, stored in DB)
- **Rationale**: Access token fast (no DB lookup). Refresh token revocable (logout, security). Standard pattern.
- **Alternatives**: Single long-lived token (no revocation), session-based (not suitable for API)

### Email: SMTP with Console Fallback

- **Decision**: SMTP when configured, console log when SMTP_HOST empty
- **Rationale**: Dev-friendly — no SMTP setup needed during development. Production uses real SMTP.
- **Alternatives**: SendGrid/Mailgun API (Phase 2+), no email (blocks verify/reset features)

## No Unresolved NEEDS CLARIFICATION

All technical decisions resolved from constitution + jwt_spec.md.
