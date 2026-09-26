import os
import sys
from pydantic import BaseModel, Field

class Settings(BaseModel):
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    api_prefix: str = "/api/v1"
    
    # JWT Configuration
    jwt_secret_key: str = Field(
        default_factory=lambda: os.getenv("JWT_SECRET_KEY", "talentra-dev-secret-key-32-bytes-minimum-length-req")
    )
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "talentra.id"
    jwt_audience: str = "talentra.id"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    
    # Cookie Configuration
    cookie_name: str = "talentra_session"
    refresh_cookie_name: str = "talentra_refresh"
    cookie_secure: bool = Field(default_factory=lambda: os.getenv("APP_ENV", "development") == "production")
    cookie_samesite: str = "lax"
    cookie_domain: str | None = None
    
    # CSRF Configuration
    csrf_cookie_name: str = "talentra_csrf"
    csrf_header_name: str = "X-CSRF-Token"
    
    # Demo Auth Configuration
    enable_demo_auth: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_DEMO_AUTH", "true").lower() in ("true", "1", "yes")
    )

    # Identifier Lookup Privacy Pepper
    identifier_lookup_pepper: str = Field(
        default_factory=lambda: os.getenv("IDENTIFIER_LOOKUP_PEPPER", "talentra-identifier-lookup-pepper-v1")
    )

    # Relational Database (PostgreSQL)
    database_url: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "sqlite+aiosqlite:///./test_talentra.db"
            if (os.getenv("APP_ENV") == "test" or "pytest" in sys.modules)
            else "postgresql+asyncpg://talentra_dev:talentra_dev_secret@localhost:5432/talentra_db",
        )
    )
    repository_backend: str = Field(
        default_factory=lambda: os.getenv(
            "REPOSITORY_BACKEND",
            "postgres" if os.getenv("APP_ENV") == "production" else "in_memory",
        )
    )

    # Free Tier Quota Configuration
    free_tier_mode: bool = Field(
        default_factory=lambda: os.getenv("FREE_TIER_MODE", "true").lower() in ("true", "1", "yes")
    )
    storage_soft_limit_bytes: int = Field(
        default_factory=lambda: int(os.getenv("STORAGE_SOFT_LIMIT_BYTES", str(200 * 1024 * 1024)))  # 200 MB default soft limit
    )
    blob_read_write_token: str | None = Field(
        default_factory=lambda: os.getenv("BLOB_READ_WRITE_TOKEN")
    )

    # Document Database (MongoDB — Optional / Legacy Compatibility only)
    mongodb_url: str | None = Field(
        default_factory=lambda: os.getenv("MONGODB_URL")
    )
    mongodb_database: str = Field(
        default_factory=lambda: os.getenv("MONGODB_DATABASE", "talentra_docs")
    )

    # Object Storage (Vercel Blob / Local / S3)
    object_storage_provider: str = Field(
        default_factory=lambda: os.getenv("OBJECT_STORAGE_PROVIDER", "local")
    )
    local_storage_path: str = Field(
        default_factory=lambda: os.getenv("LOCAL_STORAGE_PATH", "backend/storage_data")
    )
    s3_endpoint_url: str | None = Field(
        default_factory=lambda: os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
    )
    s3_region: str = Field(
        default_factory=lambda: os.getenv("S3_REGION", "us-east-1")
    )
    s3_bucket: str = Field(
        default_factory=lambda: os.getenv("S3_BUCKET", "talentra-evidence")
    )
    s3_access_key_id: str = Field(
        default_factory=lambda: os.getenv("S3_ACCESS_KEY_ID", "minioadmin")
    )
    s3_secret_access_key: str = Field(
        default_factory=lambda: os.getenv("S3_SECRET_ACCESS_KEY", "minioadmin")
    )
    presigned_url_ttl_seconds: int = Field(
        default_factory=lambda: int(os.getenv("PRESIGNED_URL_TTL", "900"))  # 15 minutes default
    )

    # File Upload Limits (in bytes)
    max_image_upload_bytes: int = 5 * 1024 * 1024       # 5 MB
    max_pdf_upload_bytes: int = 15 * 1024 * 1024        # 15 MB
    max_video_upload_bytes: int = 50 * 1024 * 1024      # 50 MB
    cv_pdf_max_bytes: int = Field(
        default_factory=lambda: int(os.getenv("CV_PDF_MAX_BYTES", str(4 * 1024 * 1024)))  # 4 MB max for CV PDF
    )
    
    # Phase 8 CV & Public Verification Configuration
    public_app_url: str = Field(
        default_factory=lambda: (
            os.getenv("PUBLIC_APP_URL")
            or (f"https://{os.getenv('VERCEL_URL')}" if os.getenv("VERCEL_URL") else None)
            or "http://localhost:3000"
        )
    )
    cv_verification_token_pepper: str = Field(
        default_factory=lambda: os.getenv("CV_VERIFICATION_TOKEN_PEPPER", "talentra-cv-token-pepper-v1")
    )
    cv_verification_ttl_days: int | None = Field(
        default_factory=lambda: int(os.getenv("CV_VERIFICATION_TTL_DAYS", "365")) if os.getenv("CV_VERIFICATION_TTL_DAYS") else 365
    )
    cv_pdf_renderer: str = Field(
        default_factory=lambda: os.getenv("CV_PDF_RENDERER", "reportlab")
    )
    cv_min_selected_portfolios: int = 1
    cv_max_selected_portfolios: int = 8
    public_verify_rate_limit: int = Field(
        default_factory=lambda: int(os.getenv("PUBLIC_VERIFY_RATE_LIMIT", "60"))
    )

    # CORS
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    def validate_production_safety(self) -> None:
        """Fail-fast validation for production security constraints on Vercel."""
        if self.app_env == "production":
            insecure_keys = (
                "secret123",
                "development-secret",
                "changeme",
                "talentra-dev-secret-key-32-bytes-minimum-length-req",
            )
            if not self.jwt_secret_key or self.jwt_secret_key in insecure_keys or len(self.jwt_secret_key) < 32:
                raise RuntimeError("CRITICAL: Production cannot use default, empty, or short JWT_SECRET_KEY!")
            if not self.cookie_secure:
                raise RuntimeError("CRITICAL: Production must enforce cookie_secure=True!")
            if self.enable_demo_auth:
                raise RuntimeError("CRITICAL: Production cannot have ENABLE_DEMO_AUTH enabled!")
            if self.repository_backend == "in_memory":
                raise RuntimeError("CRITICAL: Production cannot use in-memory repositories! PostgreSQL required.")
            if not self.database_url or "sqlite" in self.database_url:
                raise RuntimeError("CRITICAL: Production requires a real PostgreSQL DATABASE_URL!")
            if self.object_storage_provider == "local":
                raise RuntimeError("CRITICAL: Production must use S3-compatible object storage provider, not local!")
            if self.object_storage_provider == "vercel_blob":
                has_token = bool(self.blob_read_write_token or os.getenv("BLOB_READ_WRITE_TOKEN"))
                has_oidc = bool(os.getenv("VERCEL_OIDC_TOKEN") or os.getenv("VERCEL"))
                if not (has_token or has_oidc):
                    raise RuntimeError("CRITICAL: Production with OBJECT_STORAGE_PROVIDER=vercel_blob requires Vercel Blob OIDC or BLOB_READ_WRITE_TOKEN!")
            if self.object_storage_provider == "s3":
                if self.s3_access_key_id in ("minioadmin", "admin") or self.s3_secret_access_key in ("minioadmin", "admin"):
                    raise RuntimeError("CRITICAL: Production cannot use default S3 credentials!")
            if not self.identifier_lookup_pepper or self.identifier_lookup_pepper == "talentra-identifier-lookup-pepper-v1":
                raise RuntimeError("CRITICAL: Production must supply a unique, non-default IDENTIFIER_LOOKUP_PEPPER!")
            if not self.cv_verification_token_pepper or self.cv_verification_token_pepper == "talentra-cv-token-pepper-v1":
                raise RuntimeError("CRITICAL: Production must supply a unique, non-default CV_VERIFICATION_TOKEN_PEPPER!")
            if not self.public_app_url or "localhost" in self.public_app_url:
                raise RuntimeError("CRITICAL: Production requires a valid non-localhost PUBLIC_APP_URL!")
            if "*" in self.allowed_origins:
                raise RuntimeError("CRITICAL: Production CORS cannot allow wildcard origins (*)! Must be explicit domains.")

settings = Settings()
# Execute initial production safety check
if settings.app_env == "production":
    settings.validate_production_safety()
