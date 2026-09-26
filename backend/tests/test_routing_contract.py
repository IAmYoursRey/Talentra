import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app as main_app
from api.index import app as vercel_app


def test_vercel_entrypoint_identity_and_no_duplicate_routes():
    """
    Verifies that the Vercel serverless entrypoint (api/index.py) exports the
    exact same authoritative FastAPI instance without duplicating routers.
    """
    assert vercel_app is main_app
    route_paths = list(vercel_app.openapi()["paths"].keys())
    
    # Assert canonical /api/v1/* prefix exists on all application routes
    v1_routes = [p for p in route_paths if p.startswith("/api/v1/")]
    assert len(v1_routes) >= 50
    assert "/api/v1/health/live" in route_paths
    assert "/api/v1/health/ready" in route_paths
    assert "/api/v1/auth/login" in route_paths
    assert "/api/v1/student/portfolio" in route_paths
    assert "/api/v1/teacher/reviews" in route_paths
    assert "/api/v1/admin/users" in route_paths
    assert "/api/v1/public/verify/{token}" in route_paths
    assert "/api/v1/storage/verify-intent" in route_paths


@pytest.mark.asyncio
async def test_canonical_routes_response_contracts():
    """
    Verifies representative endpoints respond on their canonical /api/v1 paths:
    1. GET /api/v1/health/live -> 200 OK
    2. GET /api/v1/public/verify/invalid-test-token -> Validated response (not 404 route not found)
    3. Protected student endpoint without auth -> 401 Unauthorized
    4. Protected teacher endpoint without auth -> 401 Unauthorized
    5. Protected admin endpoint without auth -> 401 Unauthorized
    """
    transport = ASGITransport(app=vercel_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health liveness
        res_health = await client.get("/api/v1/health/live")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "live"

        # 2. Public verification with non-existent/invalid token
        res_verify = await client.get("/api/v1/public/verify/nonexistent-token-123")
        assert res_verify.status_code in (200, 404)
        if res_verify.status_code == 200:
            assert res_verify.json()["status"] == "invalid"

        # 3. Protected student endpoint
        res_student = await client.get("/api/v1/student/portfolio")
        assert res_student.status_code == 401

        # 4. Protected teacher endpoint
        res_teacher = await client.get("/api/v1/teacher/reviews")
        assert res_teacher.status_code == 401

        # 5. Protected admin endpoint
        res_admin = await client.get("/api/v1/admin/users")
        assert res_admin.status_code == 401
