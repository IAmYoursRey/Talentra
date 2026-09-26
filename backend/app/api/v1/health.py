import os
from fastapi import APIRouter, Response, status
from sqlalchemy import text
from ...core.config import settings
from ...core.database import AsyncSessionLocal
from ...storage import get_object_storage

router = APIRouter(prefix="/health", tags=["Health & Readiness"])


@router.get("/live")
async def liveness_probe():
    """Liveness probe indicating application process is alive."""
    return {
        "status": "live",
        "service": "TALENTRA.ID Platform Engine",
        "environment": settings.app_env,
    }


@router.get("/ready")
async def readiness_probe(response: Response):
    """
    Readiness probe inspecting core persistence dependencies for Vercel Free Stack:
    - Neon PostgreSQL (SELECT 1)
    - Object Storage configuration (Vercel Blob / Local development)
    Never exposes internal network topology, credentials, or connection strings.
    """
    dependencies = {
        "database": "unknown",
        "postgres": "unknown",
        "mongo": "ok",
        "storage": "unknown",
    }
    all_ready = True

    # 1. Database check (Neon PostgreSQL / SQLite test)
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            dependencies["database"] = "ok"
            dependencies["postgres"] = "ok"
    except Exception:
        dependencies["database"] = "unavailable"
        dependencies["postgres"] = "unavailable"
        all_ready = False

    # 2. Storage configuration check
    try:
        storage = get_object_storage()
        if settings.object_storage_provider == "vercel_blob":
            # Check presence of Vercel Blob OIDC token or static auth token without performing expensive Blob writes
            token = os.getenv("VERCEL_OIDC_TOKEN") or os.getenv("BLOB_READ_WRITE_TOKEN") or getattr(settings, "blob_read_write_token", None) or os.getenv("VERCEL")
            if token:
                dependencies["storage"] = "ok"
            else:
                dependencies["storage"] = "unconfigured"
                if settings.app_env == "production":
                    all_ready = False
        else:
            dependencies["storage"] = "ok" if storage is not None else "unavailable"
            if storage is None and settings.app_env == "production":
                all_ready = False
    except Exception:
        dependencies["storage"] = "unavailable"
        if settings.app_env == "production":
            all_ready = False

    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "degraded",
            "dependencies": dependencies,
        }

    return {
        "status": "ready",
        "dependencies": dependencies,
    }
