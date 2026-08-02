from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Aiven Postgres requires SSL -- pass connect_args if not already in the URL
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # avoids stale-connection errors after idle periods
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create pgvector extension + all tables. Call once on startup or via
    a migration. For real production use, prefer Alembic migrations over
    calling this on every boot."""
    from app import models  # noqa: F401  (ensures models are registered)

    async with engine.begin() as conn:
        await conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector;")
        await conn.run_sync(Base.metadata.create_all)
