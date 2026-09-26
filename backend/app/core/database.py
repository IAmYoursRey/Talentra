import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from sqlalchemy.orm import DeclarativeBase
from .config import settings

class Base(DeclarativeBase):
    pass

def get_engine(url: str | None = None) -> AsyncEngine:
    db_url = url or os.getenv("DATABASE_URL") or settings.database_url
    kwargs = {"echo": False}
    if db_url.startswith("postgresql"):
        pool_mode = os.getenv("DB_POOL_CLASS", "queue").lower()
        if pool_mode == "nullpool":
            # NullPool: Opens connection on demand and releases immediately.
            # Best suited for short-lived ephemeral functions with low frequency.
            kwargs["poolclass"] = NullPool
        else:
            # Conservative serverless pool: max 2 connections per function instance, 0 overflow.
            # Prevents connection explosion across concurrent Vercel serverless instances,
            # allowing Neon's PgBouncer pooler to remain the primary connection authority.
            pool_size = int(os.getenv("DB_POOL_SIZE", "2"))
            max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "0"))
            kwargs.update({
                "poolclass": AsyncAdaptedQueuePool,
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "pool_recycle": 300,
                "pool_pre_ping": True,
            })
    return create_async_engine(db_url, **kwargs)

engine = get_engine()
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency providing a request-scoped AsyncSession."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
