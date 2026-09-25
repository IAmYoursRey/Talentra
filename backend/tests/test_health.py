import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_liveness_probe():
    """
    MANDATORY REQUIREMENT 33:
    Liveness probe returns status live.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.get("/api/v1/health/live")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "live"
        assert data["service"] == "TALENTRA.ID Platform Engine"


@pytest.mark.asyncio
async def test_health_readiness_probe_structure_and_no_leakage():
    """
    MANDATORY REQUIREMENT 33:
    Readiness probe inspects postgres, mongo, and storage.
    Must NEVER leak credentials, connection strings, or internal network details.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.get("/api/v1/health/ready")
        assert res.status_code in (200, 503)
        data = res.json()
        assert "status" in data
        assert "dependencies" in data
        deps = data["dependencies"]
        assert "postgres" in deps
        assert "mongo" in deps
        assert "storage" in deps

        # Verify no credentials or connection strings leaked in response body
        text_body = res.text
        assert "password" not in text_body.lower()
        assert "secret" not in text_body.lower()
        assert "5432" not in text_body
        assert "27017" not in text_body
        assert "minioadmin" not in text_body
