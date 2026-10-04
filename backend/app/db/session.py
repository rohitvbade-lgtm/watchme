from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import get_settings
from typing import AsyncGenerator

settings = get_settings()

db_url = settings.async_database_url
is_sqlite = db_url.startswith("sqlite")

connect_args = {}
# Supabase pooler (Supavisor/PgBouncer, ports 6543/5432) requires disabling prepared statement cache in asyncpg
if not is_sqlite and ("6543" in db_url or "pooler" in db_url or "supabase" in db_url):
    connect_args["statement_cache_size"] = 0
    connect_args["prepared_statement_cache_size"] = 0

engine_kwargs = {
    "echo": settings.debug,
    "connect_args": connect_args,
}

if not is_sqlite:
    engine_kwargs.update({
        "pool_pre_ping": True,  # Automatically detect dropped connections from Supabase idle timeouts
        "pool_recycle": 1800,   # Recycle connections every 30 minutes
        "pool_size": 10,        # Respect Supabase free tier connection limits
        "max_overflow": 5,
    })

engine = create_async_engine(db_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    from app.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
