# Quickstart: JWT Authentication & CMS Core

## Prerequisites

- Python 3.13+
- PostgreSQL (or SQLite for dev/test)

## Setup

```bash
# 1. Install dependencies
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg aiosqlite
pip install pyjwt bcrypt pydantic[email] python-dotenv alembic httpx pytest pytest-asyncio

# 2. Create .env
cp .env.example .env
# Edit: SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD

# 3. Run migrations
alembic upgrade head

# 4. Start server
uvicorn app.main:app --reload
# → Auto-seeds superuser on first run

# 5. Test login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@coffeetree.vn", "password": "admin123"}'
```

## Run Tests

```bash
pytest tests/ -v --asyncio-mode=auto
```
