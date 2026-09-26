import asyncio
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.app.core.database import Base
from backend.app.core.rate_limiter import DatabaseRateLimiter
from backend.app.repositories.upload_intent import BlobUploadIntentRepository


import tempfile
import os

@pytest.fixture
async def isolated_session_factory():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    yield session_factory
    await engine.dispose()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.mark.asyncio
async def test_database_rate_limiter_atomic_concurrency(isolated_session_factory):
    limiter = DatabaseRateLimiter(session_factory=isolated_session_factory)
    identifier = "student-123"
    scope = "login"
    max_requests = 5

    # Concurrently fire 8 requests
    tasks = [
        limiter.is_rate_limited_and_record(
            identifier=identifier,
            scope=scope,
            max_requests=max_requests,
            window_seconds=60,
        )
        for _ in range(8)
    ]
    results = await asyncio.gather(*tasks)

    # 5 allowed (False), 3 blocked (True)
    allowed_count = results.count(False)
    blocked_count = results.count(True)
    assert allowed_count == 5
    assert blocked_count == 3


@pytest.mark.asyncio
async def test_database_rate_limiter_cleanup_expired(isolated_session_factory):
    limiter = DatabaseRateLimiter(session_factory=isolated_session_factory)
    # Record some attempt
    await limiter.is_rate_limited_and_record("test-id", "test-scope", 5, 1)

    # Fast forward cutoff
    future_cutoff = datetime.now(timezone.utc) + timedelta(minutes=10)
    cleaned = await limiter.cleanup_expired(before=future_cutoff)
    assert cleaned >= 1


@pytest.mark.asyncio
async def test_blob_upload_intent_atomic_single_use(isolated_session_factory):
    repo = BlobUploadIntentRepository(session_factory=isolated_session_factory)
    intent, raw_token = await repo.create_intent(
        school_id="sch-1",
        student_id="stu-1",
        portfolio_id="port-1",
        pathname="evidence/doc.pdf",
        expected_content_type="application/pdf",
        max_bytes=1024 * 1024,
    )

    # Concurrently attempt to consume the same token 10 times
    tasks = [repo.consume_intent(raw_token) for _ in range(10)]
    results = await asyncio.gather(*tasks)

    # Exactly one consumer must succeed, 9 must return None
    consumed_intents = [r for r in results if r is not None]
    failed_attempts = [r for r in results if r is None]

    assert len(consumed_intents) == 1
    assert len(failed_attempts) == 9
    assert consumed_intents[0].status == "consumed"

    # Subsequent replay attempt must return None
    replay = await repo.consume_intent(raw_token)
    assert replay is None
