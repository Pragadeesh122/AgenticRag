import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.auth.manager import current_active_user
import api.rate_limit as _rl
from api.rate_limit import _RATE_LIMIT_FALLBACK
from api.server import app
from database.core import get_db
from database.models import Base, User


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest.fixture
async def test_user(session_factory):
    async with session_factory() as session:
        user = User(
            id=uuid.uuid4(),
            email="owner@example.com",
            hashed_password="hashed-password",
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture
async def async_client(session_factory, test_user):
    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[current_active_user] = lambda: test_user
    _RATE_LIMIT_FALLBACK.clear()
    _rl._lua_script = None  # reset cached Lua script between tests

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
    _RATE_LIMIT_FALLBACK.clear()
    _rl._lua_script = None
