import os
import uuid
import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


@pytest.mark.skipif(
    not os.getenv("NEON_TEST_DATABASE_URL"),
    reason="NEON_TEST_DATABASE_URL not configured. Skipping real Neon PostgreSQL cloud test.",
)
@pytest.mark.asyncio
async def test_real_neon_cloud_integration():
    """
    Validates real Neon PostgreSQL connection, dialect, version,
    and schema tables when NEON_TEST_DATABASE_URL is provided.
    """
    neon_url = os.getenv("NEON_TEST_DATABASE_URL")
    engine = create_async_engine(neon_url)

    assert engine.dialect.name == "postgresql", f"Expected postgresql dialect, got: {engine.dialect.name}"

    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT version();"))
        version_row = res.fetchone()
        assert version_row is not None
        assert "PostgreSQL" in version_row[0]

        # Verify alembic migration tables exist
        tbl_res = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        )
        tables = {r[0] for r in tbl_res.fetchall()}
        required = [
            "schools",
            "users",
            "portfolio_items",
            "portfolio_revisions",
            "evidence_tag_snapshots",
            "recommendation_snapshots",
            "cv_content_snapshots",
            "blob_upload_intents",
            "rate_limit_buckets",
            "verification_records",
        ]
        for tbl in required:
            assert tbl in tables, f"Expected table '{tbl}' in Neon database."

    await engine.dispose()


@pytest.mark.skipif(
    os.getenv("VERCEL_BLOB_INTEGRATION", "false").lower() != "true"
    or not (os.getenv("VERCEL_OIDC_TOKEN") or os.getenv("BLOB_READ_WRITE_TOKEN")),
    reason="VERCEL_BLOB_INTEGRATION=true or Blob token not set. Skipping live Vercel Blob cloud test.",
)
def test_real_vercel_blob_cloud_integration():
    """
    Validates live Vercel Blob operations with isolated synthetic test key.
    Never touches student files.
    """
    from backend.app.storage.vercel_blob import VercelBlobStorage

    storage = VercelBlobStorage()
    test_key = f"tests/{uuid.uuid4()}.txt"
    test_data = b"TALENTRA Vercel Blob integration test marker"

    try:
        # PUT
        url = storage.upload_object(test_key, test_data, content_type="text/plain")
        assert url is not None

        # HEAD
        head_meta = storage.head_object(test_key)
        assert head_meta is not None
        assert head_meta["size_bytes"] == len(test_data)

        # Range Read
        chunk = storage.read_range(test_key, offset=0, length=8)
        assert chunk == test_data[:8]

        # Signed GET URL verification
        dl_url = storage.create_download_url(test_key, expires_in=30)
        assert "/api/v1/storage/download" in dl_url

    finally:
        # DELETE
        storage.delete_object(test_key)
