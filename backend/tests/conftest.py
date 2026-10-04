import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.dialects import postgresql
from sqlalchemy import JSON

# Patch JSONB → JSON before any models are imported (SQLite doesn't support JSONB)
postgresql.JSONB = JSON  # type: ignore[misc]

from app.main import app, scheduler
from app.db.session import get_db
from app.models.base import Base
from app.config import get_settings

get_settings().debug = False
get_settings().api_secret_key = None

# Use SQLite in-memory for tests
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def disable_scheduler():
    """Prevent the APScheduler from running during tests."""
    if scheduler.running:
        scheduler.shutdown(wait=False)

@pytest.fixture(autouse=True)
async def db_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db() -> AsyncSession:
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

