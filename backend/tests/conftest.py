"""Test fixtures for async FastAPI testing with SQLite in-memory."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from auth.models import User
from auth.utils import hash_password

# SQLite async in-memory for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create tables and yield a test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client with DB override."""
    from app.main import app

    app.dependency_overrides[get_db] = override_get_db

    # Create tables fresh for each test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def superuser(db_session: AsyncSession) -> User:
    """Create a test superuser."""
    user = User(
        email="admin@test.com",
        password_hash=hash_password("admin123456"),
        full_name="Admin Test",
        is_active=True,
        is_superuser=True,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def normal_user(db_session: AsyncSession) -> User:
    """Create a test normal user."""
    user = User(
        email="user@test.com",
        password_hash=hash_password("user123456"),
        full_name="Normal User",
        is_active=True,
        is_superuser=False,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def login_user(client: AsyncClient, email: str, password: str) -> dict:
    """Helper: login and return token data."""
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["data"]


def auth_header(token: str) -> dict:
    """Helper: create Authorization header."""
    return {"Authorization": f"Bearer {token}"}
