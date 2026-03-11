from pathlib import Path
from types import SimpleNamespace

import pytest
import pytest_asyncio
from fakeredis.aioredis import FakeRedis
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from main import app
from auth import auth as auth_module
from auth.models import Base as AuthBase
from core import redis as redis_core
from core.database import get_async_session
from links.dependencies import get_link_cache_service
from models.tables import links, expired_links


TEST_DB_PATH = Path("tests/test.db")
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"


class FakeLinkCacheService:
    def __init__(self):
        self.storage = {}

    async def get_redirect_data(self, short_code: str):
        return self.storage.get(short_code)

    async def set_redirect_data(self, short_code: str, original_url: str, expires_at):
        self.storage[short_code] = {
            "original_url": original_url,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }

    async def delete_redirect_url(self, short_code: str):
        self.storage.pop(short_code, None)


@pytest_asyncio.fixture(scope="session")
async def engine():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    engine = create_async_engine(TEST_DATABASE_URL, future=True)

    yield engine

    await engine.dispose()

    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest_asyncio.fixture(scope="session")
async def session_maker(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def prepare_database(engine):
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: expired_links.drop(sync_conn, checkfirst=True))
        await conn.run_sync(lambda sync_conn: links.drop(sync_conn, checkfirst=True))
        await conn.run_sync(AuthBase.metadata.drop_all)

        await conn.run_sync(AuthBase.metadata.create_all)
        await conn.run_sync(lambda sync_conn: links.create(sync_conn, checkfirst=True))
        await conn.run_sync(lambda sync_conn: expired_links.create(sync_conn, checkfirst=True))

    yield

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: expired_links.drop(sync_conn, checkfirst=True))
        await conn.run_sync(lambda sync_conn: links.drop(sync_conn, checkfirst=True))
        await conn.run_sync(AuthBase.metadata.drop_all)


@pytest.fixture
def fake_cache_service():
    return FakeLinkCacheService()


@pytest.fixture
def client(session_maker, fake_cache_service, monkeypatch):
    async def override_get_async_session():
        async with session_maker() as session:
            yield session

    # Переопределяем БД
    app.dependency_overrides[get_async_session] = override_get_async_session

    # Переопределяем link cache service
    app.dependency_overrides[get_link_cache_service] = lambda: fake_cache_service

    # Для fastapi-cache на /links/top подменяем redis в lifespan
    fake_redis = FakeRedis(decode_responses=True)
    monkeypatch.setattr(redis_core.aioredis, "from_url", lambda *args, **kwargs: fake_redis)

    # Для тестов по HTTP cookie secure нужно отключить
    auth_module.cookie_transport.cookie_secure = False

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_helpers(client):
    def register(email="user@example.com", username="user1", password="strongpassword"):
        return client.post(
            "/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password,
            },
        )

    def login(email="user@example.com", password="strongpassword"):
        return client.post(
            "/auth/jwt/login",
            data={
                "username": email,
                "password": password,
            },
        )

    def logout():
        return client.post("/auth/jwt/logout")

    return SimpleNamespace(
        register=register,
        login=login,
        logout=logout,
    )