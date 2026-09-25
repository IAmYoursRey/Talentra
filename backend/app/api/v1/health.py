from fastapi import APIRouter, Response, status
from sqlalchemy import text
from ...core.config import settings
from ...core.database import AsyncSessionLocal
from ...core.mongodb import mongo_manager
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
    Readiness probe inspecting core persistence dependencies:
    - PostgreSQL
    - MongoDB
    - Object Storage
    Never exposes internal network topology, credentials, or connection strings.
    """
    dependencies = {
        "postgres": "unknown",
        "mongo": "unknown",
        "storage": "unknown",
    }
    all_ready = True

    # 1. PostgreSQL check
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            dependencies["postgres"] = "ok"
    except Exception:
        dependencies["postgres"] = "unavailable"
        all_ready = False

    # 2. MongoDB check
    try:
        is_mongo_ok = await mongo_manager.ping()
        dependencies["mongo"] = "ok" if is_mongo_ok else "unavailable"
        if not is_mongo_ok:
            all_ready = False
    except Exception:
        dependencies["mongo"] = "unavailable"
        all_ready = False

    # 3. Object Storage check
    try:
        storage = get_object_storage()
        # Verify storage abstraction is initialized
        if storage is not None:
            dependencies["storage"] = "ok"
        else:
            dependencies["storage"] = "unavailable"
            all_ready = False
    except Exception:
        dependencies["storage"] = "unavailable"
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
