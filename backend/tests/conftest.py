import os
import sys
import asyncio
import pytest

# Ensure test environment variables are established before app imports
os.environ["APP_ENV"] = "test"
os.environ["REPOSITORY_BACKEND"] = "in_memory"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_talentra.db"

import app.db.models  # Ensure all models are registered with Base.metadata
from app.core.database import engine, Base


@pytest.fixture(scope="session", autouse=True)
def init_test_sqlite_schema():
    """Initializes tables for compatibility testing when PostgreSQL is not running."""
    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        from app.scripts.seed_dev import seed_development_data
        await seed_development_data()

    asyncio.run(_setup())
    yield
    # Cleanup test db file after session if desired
