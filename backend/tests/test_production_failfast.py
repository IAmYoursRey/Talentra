"""
Tests for production fail-fast configuration, security constraints,
cookie security, demo authentication enforcement, and admin bootstrap.
"""

import pytest
import os
from unittest.mock import patch

from app.core.config import Settings
from app.scripts.bootstrap_school_admin import bootstrap_school_admin
from app.core.security import verify_password
from app.core.database import AsyncSessionLocal
from app.db.models import UserModel, AuthIdentityModel
from sqlalchemy import select


def test_production_failfast_default_jwt_secret():
    """Verify production startup fails when JWT_SECRET_KEY is default or insecure."""
    settings = Settings(
        app_env="production",
        jwt_secret_key="talentra-dev-secret-key-32-bytes-minimum-length-req",
        cookie_secure=True,
        enable_demo_auth=False,
        repository_backend="postgres",
        database_url="postgresql+asyncpg://user:pass@host:5432/db",
        mongodb_url="mongodb://host:27017",
        object_storage_provider="s3",
        s3_access_key_id="prod_s3_key_id",
        s3_secret_access_key="prod_s3_secret_key_12345",
        identifier_lookup_pepper="unique-prod-pepper-64-character-hex-string-for-talentra",
        cv_verification_token_pepper="unique-prod-cv-pepper-64-char-hex-string-talentra",
        public_app_url="https://talentra.id",
        allowed_origins=["https://talentra.id"],
    )
    with pytest.raises(RuntimeError, match="CRITICAL: Production cannot use default, empty, or short JWT_SECRET_KEY!"):
        settings.validate_production_safety()


def test_production_failfast_sqlite_database_url():
    """Verify production startup fails when database_url is SQLite."""
    settings = Settings(
        app_env="production",
        jwt_secret_key="secure-high-entropy-jwt-secret-key-for-prod-32bytes",
        cookie_secure=True,
        enable_demo_auth=False,
        repository_backend="postgres",
        database_url="sqlite+aiosqlite:///test.db",
        mongodb_url="mongodb://host:27017",
        object_storage_provider="s3",
        s3_access_key_id="prod_s3_key_id",
        s3_secret_access_key="prod_s3_secret_key_12345",
        identifier_lookup_pepper="unique-prod-pepper-64-character-hex-string-for-talentra",
        cv_verification_token_pepper="unique-prod-cv-pepper-64-char-hex-string-talentra",
        public_app_url="https://talentra.id",
        allowed_origins=["https://talentra.id"],
    )
    with pytest.raises(RuntimeError, match="CRITICAL: Production requires a real PostgreSQL DATABASE_URL!"):
        settings.validate_production_safety()


def test_production_failfast_local_storage():
    """Verify production startup fails when object storage is local."""
    settings = Settings(
        app_env="production",
        jwt_secret_key="secure-high-entropy-jwt-secret-key-for-prod-32bytes",
        cookie_secure=True,
        enable_demo_auth=False,
        repository_backend="postgres",
        database_url="postgresql+asyncpg://user:pass@host:5432/db",
        mongodb_url="mongodb://host:27017",
        object_storage_provider="local",
        identifier_lookup_pepper="unique-prod-pepper-64-character-hex-string-for-talentra",
        cv_verification_token_pepper="unique-prod-cv-pepper-64-char-hex-string-talentra",
        public_app_url="https://talentra.id",
        allowed_origins=["https://talentra.id"],
    )
    with pytest.raises(RuntimeError, match="CRITICAL: Production must use S3-compatible object storage provider, not local!"):
        settings.validate_production_safety()


def test_production_failfast_demo_auth_enabled():
    """Verify production startup fails if demo authentication is enabled."""
    settings = Settings(
        app_env="production",
        jwt_secret_key="secure-high-entropy-jwt-secret-key-for-prod-32bytes",
        cookie_secure=True,
        enable_demo_auth=True,
        repository_backend="postgres",
        database_url="postgresql+asyncpg://user:pass@host:5432/db",
        mongodb_url="mongodb://host:27017",
        object_storage_provider="s3",
        s3_access_key_id="prod_s3_key_id",
        s3_secret_access_key="prod_s3_secret_key_12345",
        identifier_lookup_pepper="unique-prod-pepper-64-character-hex-string-for-talentra",
        cv_verification_token_pepper="unique-prod-cv-pepper-64-char-hex-string-talentra",
        public_app_url="https://talentra.id",
        allowed_origins=["https://talentra.id"],
    )
    with pytest.raises(RuntimeError, match="CRITICAL: Production cannot have ENABLE_DEMO_AUTH enabled!"):
        settings.validate_production_safety()


def test_production_failfast_cors_wildcard():
    """Verify production startup fails if CORS origin has wildcard *."""
    settings = Settings(
        app_env="production",
        jwt_secret_key="secure-high-entropy-jwt-secret-key-for-prod-32bytes",
        cookie_secure=True,
        enable_demo_auth=False,
        repository_backend="postgres",
        database_url="postgresql+asyncpg://user:pass@host:5432/db",
        mongodb_url="mongodb://host:27017",
        object_storage_provider="s3",
        s3_access_key_id="prod_s3_key_id",
        s3_secret_access_key="prod_s3_secret_key_12345",
        identifier_lookup_pepper="unique-prod-pepper-64-character-hex-string-for-talentra",
        cv_verification_token_pepper="unique-prod-cv-pepper-64-char-hex-string-talentra",
        public_app_url="https://talentra.id",
        allowed_origins=["*"],
    )
    with pytest.raises(RuntimeError, match="CRITICAL: Production CORS cannot allow wildcard origins"):
        settings.validate_production_safety()


def test_production_failfast_blob_broker_secret():
    """Verify production startup fails when vercel_blob is used without a dedicated non-default BLOB_BROKER_HMAC_SECRET."""
    settings = Settings(
        app_env="production",
        jwt_secret_key="secure-high-entropy-jwt-secret-key-for-prod-32bytes",
        cookie_secure=True,
        enable_demo_auth=False,
        repository_backend="postgres",
        database_url="postgresql+asyncpg://user:pass@host:5432/db",
        object_storage_provider="vercel_blob",
        blob_read_write_token="vercel_blob_rw_token_prod_12345",
        blob_broker_hmac_secret="talentra-blob-broker-dev-secret-32-bytes-min",
        identifier_lookup_pepper="unique-prod-pepper-64-character-hex-string-for-talentra",
        cv_verification_token_pepper="unique-prod-cv-pepper-64-char-hex-string-talentra",
        public_app_url="https://talentra.id",
        allowed_origins=["https://talentra.id"],
    )
    with pytest.raises(RuntimeError, match="CRITICAL: Production requires a dedicated, non-default BLOB_BROKER_HMAC_SECRET"):
        settings.validate_production_safety()

    # Fails if same as jwt_secret_key
    settings.blob_broker_hmac_secret = "secure-high-entropy-jwt-secret-key-for-prod-32bytes"
    with pytest.raises(RuntimeError, match="CRITICAL: Production requires a dedicated, non-default BLOB_BROKER_HMAC_SECRET"):
        settings.validate_production_safety()

    # Passes when separate, dedicated 32-byte secret is provided
    settings.blob_broker_hmac_secret = "unique-dedicated-blob-broker-secret-32bytes!"
    settings.validate_production_safety()


def test_production_valid_configuration_passes():
    """Verify a properly configured production settings object validates successfully."""
    settings = Settings(
        app_env="production",
        jwt_secret_key="secure-high-entropy-jwt-secret-key-for-prod-32bytes",
        cookie_secure=True,
        enable_demo_auth=False,
        repository_backend="postgres",
        database_url="postgresql+asyncpg://user:pass@host:5432/db",
        mongodb_url="mongodb://host:27017",
        object_storage_provider="s3",
        s3_access_key_id="prod_s3_key_id",
        s3_secret_access_key="prod_s3_secret_key_12345",
        identifier_lookup_pepper="unique-prod-pepper-64-character-hex-string-for-talentra",
        cv_verification_token_pepper="unique-prod-cv-pepper-64-char-hex-string-talentra",
        public_app_url="https://talentra.id",
        allowed_origins=["https://talentra.id"],
    )
    # Should not raise
    settings.validate_production_safety()


@pytest.mark.asyncio
async def test_bootstrap_school_admin_script():
    """Verify initial admin bootstrap CLI creates admin with temporary password and must_change_password."""
    result = await bootstrap_school_admin(
        school_name="SMK Negeri 1 Jakarta Staging",
        admin_name="Operator Admin",
        admin_identifier="admin@staging.smkn1jkt.sch.id",
        identifier_type="email",
    )

    assert result["school_id"] is not None
    assert result["admin_user_id"] is not None
    assert result["admin_identifier"] == "admin@staging.smkn1jkt.sch.id"
    assert result["must_change_password"] is True
    assert len(result["temporary_password"]) >= 16

    # Verify database persistence and password verification
    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(UserModel).where(UserModel.id == result["admin_user_id"])
        )).scalar_one_or_none()
        assert user is not None
        assert user.role == "admin"
        assert user.status == "active"

        identity = (await session.execute(
            select(AuthIdentityModel).where(AuthIdentityModel.user_id == user.id)
        )).scalar_one_or_none()
        assert identity is not None
        assert identity.must_change_password is True
        assert verify_password(result["temporary_password"], identity.password_hash) is True
