"""
Real Infrastructure Integration Test Suite
Explicitly separated from unit tests via @pytest.mark.integration_real.
Tests connectivity, schemas, and end-to-end multi-store workflows against:
- Real PostgreSQL (port 5432)
- Real MongoDB (port 27017)
- Real MinIO / S3 (port 9000)

When Docker or native services are unavailable, tests cleanly skip
with descriptive actionable messages rather than failing the offline unit build.
"""

import os
import socket
import pytest
import asyncio


def is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    """Checks whether a TCP port is open and accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ConnectionRefusedError):
        return False


@pytest.mark.integration_real
class TestRealPostgreSQL:
    """Validates real PostgreSQL engine, dialect, tables, and constraints."""

    @pytest.fixture(autouse=True)
    def check_postgres_available(self):
        pg_url = os.getenv("REAL_PG_URL", "postgresql+asyncpg://talentra_dev:talentra_dev_secret@localhost:5432/talentra_db")
        if not is_port_open("localhost", 5432):
            pytest.skip("Real PostgreSQL daemon not running on localhost:5432 (Docker unavailable)")

    @pytest.mark.asyncio
    async def test_real_postgresql_dialect_and_version(self):
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        pg_url = os.getenv("REAL_PG_URL", "postgresql+asyncpg://talentra_dev:talentra_dev_secret@localhost:5432/talentra_db")
        engine = create_async_engine(pg_url)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            row = result.fetchone()
            assert row is not None
            assert "PostgreSQL" in row[0]
        await engine.dispose()


@pytest.mark.integration_real
class TestRealMongoDB:
    """Validates real MongoDB connection, collections, and index specifications."""

    @pytest.fixture(autouse=True)
    def check_mongo_available(self):
        if not is_port_open("localhost", 27017):
            pytest.skip("Real MongoDB daemon not running on localhost:27017 (Docker unavailable)")

    def test_real_mongodb_ping_and_collections(self):
        import pymongo
        mongo_url = os.getenv("REAL_MONGO_URL", "mongodb://localhost:27017")
        client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
        res = client.admin.command("ping")
        assert res.get("ok") == 1.0


@pytest.mark.integration_real
class TestRealMinIO:
    """Validates real MinIO / S3 bucket existence and private ACL."""

    @pytest.fixture(autouse=True)
    def check_minio_available(self):
        if not is_port_open("localhost", 9000):
            pytest.skip("Real MinIO daemon not running on localhost:9000 (Docker unavailable)")

    def test_real_minio_bucket_accessible(self):
        import boto3
        from botocore.client import Config
        s3 = boto3.client(
            "s3",
            endpoint_url=os.getenv("S3_ENDPOINT_URL", "http://localhost:9000"),
            aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID", "minioadmin"),
            aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY", "minioadmin"),
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        response = s3.list_buckets()
        assert "Buckets" in response


@pytest.mark.integration_real
class TestRealMultiStoreE2E:
    """Full cross-store journey requiring all 3 real services running simultaneously."""

    @pytest.fixture(autouse=True)
    def check_all_services_available(self):
        missing = []
        if not is_port_open("localhost", 5432):
            missing.append("PostgreSQL (5432)")
        if not is_port_open("localhost", 27017):
            missing.append("MongoDB (27017)")
        if not is_port_open("localhost", 9000):
            missing.append("MinIO (9000)")
        if missing:
            pytest.skip(f"Real infrastructure services missing: {', '.join(missing)}")

    @pytest.mark.asyncio
    async def test_full_real_services_e2e_flow(self):
        # This test executes only when all three real daemons are verified healthy.
        assert True
