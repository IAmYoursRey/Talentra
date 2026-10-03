import os
import pytest
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from app.core.database import get_engine


def test_serverless_pool_selection_nullpool(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@ep-cool-pooler.neon.tech/neondb")
    monkeypatch.setenv("DB_POOL_CLASS", "nullpool")
    
    engine = get_engine()
    assert isinstance(engine.pool, NullPool)
    engine.sync_engine.dispose()


def test_serverless_pool_selection_queue_default(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@ep-cool-pooler.neon.tech/neondb")
    monkeypatch.delenv("DB_POOL_CLASS", raising=False)
    monkeypatch.setenv("DB_POOL_SIZE", "3")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "1")
    
    engine = get_engine()
    assert isinstance(engine.pool, AsyncAdaptedQueuePool)
    assert engine.pool.size() == 3
    engine.sync_engine.dispose()
