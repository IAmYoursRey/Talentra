from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy.orm import DeclarativeBase
from .config import settings

class Base(DeclarativeBase):
    pass

def get_engine(url: str | None = None) -> AsyncEngine:
    db_url = url or settings.database_url
    # SQLite async compatibility adjustments if used in test/dev
    kwargs = {"echo": False}
    if db_url.startswith("postgresql"):
        kwargs.update({
            "pool_size": 5,
            "max_overflow": 2,
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
