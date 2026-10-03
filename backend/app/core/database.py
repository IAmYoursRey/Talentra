import os
from typing import AsyncGenerator, Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from sqlalchemy.orm import DeclarativeBase
from .config import settings

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

class Base(DeclarativeBase):
    pass

def normalize_database_url(url: str | None) -> str:
    """
    Normalizes database connection strings for SQLAlchemy + asyncpg compatibility.
    - Leaves sqlite URLs untouched
    - Converts postgres:// and postgresql:// to postgresql+asyncpg://
    - Converts sslmode query param to ssl
    - Strips unsupported libpq query params like channel_binding
    """
    if not url:
        return ""
    if url.startswith("sqlite"):
        return url
    parsed = urlsplit(url)
    scheme = parsed.scheme
    if scheme in ("postgres", "postgresql"):
        scheme = "postgresql+asyncpg"

    # Process query params for asyncpg compatibility
    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    new_params = []
    ssl_present = False
    for k, v in query_params:
        if k == "ssl":
            ssl_present = True
            new_params.append((k, v))
        elif k == "sslmode":
            if not ssl_present:
                new_params.append(("ssl", v))
                ssl_present = True
        elif k in ("channel_binding",):
            continue  # asyncpg does not accept channel_binding
        else:
            new_params.append((k, v))

    new_query = urlencode(new_params)
    return urlunsplit((scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))

def get_engine(url: str | None = None) -> AsyncEngine:
    raw_url = url or os.getenv("DATABASE_URL") or settings.database_url
    db_url = normalize_database_url(raw_url)
    kwargs: dict[str, Any] = {"echo": False}
    if db_url.startswith("postgresql"):
        kwargs["connect_args"] = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
        }
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
