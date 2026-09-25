import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.repositories.portfolio import InMemoryPortfolioRepository
from app.repositories.catalog import CareerCatalogRepository
from app.services.projection_service import StudentSkillProjectionService
from app.services.recommendation_engine import RecommendationEngineService
from app.api.v1.student_recommendations import set_recommendation_service


@pytest.fixture(autouse=True)
def setup_recommendation_service():
    portfolio_repo = InMemoryPortfolioRepository()
    catalog_repo = CareerCatalogRepository()
    proj_svc = StudentSkillProjectionService(portfolio_repo=portfolio_repo)
    rec_engine = RecommendationEngineService(
        portfolio_repo=portfolio_repo,
        catalog_repo=catalog_repo,
        projection_service=proj_svc,
    )
    set_recommendation_service(rec_engine)

    yield {
        "portfolio_repo": portfolio_repo,
        "engine": rec_engine,
    }

    set_recommendation_service(None)


async def get_authenticated_client(identifier: str, password: str) -> AsyncClient:
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    res = await client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})
    assert res.status_code == 200
    return client


@pytest.mark.asyncio
async def test_recommendation_rbac_and_private_caching(setup_recommendation_service):
    """
    RBAC:
    - Student: 200 OK
    - Anonymous: 401 Unauthorized
    - Teacher: 403 Forbidden
    - Admin: 403 Forbidden
    Cache-Control: private, no-store
    """
    transport = ASGITransport(app=app)

    # 1. Anonymous
    async with AsyncClient(transport=transport, base_url="http://testserver") as anon_client:
        res_anon = await anon_client.get("/api/v1/student/recommendations")
        assert res_anon.status_code == 401

    # 2. Teacher (should be denied access to student-specific recommendation endpoint)
    teacher_client = await get_authenticated_client("198204152005011789", "PasswordGuru123!")
    res_teacher = await teacher_client.get("/api/v1/student/recommendations")
    assert res_teacher.status_code == 403

    # 3. Admin (should be denied access to individual student recommendation endpoint)
    admin_client = await get_authenticated_client("20101543", "PasswordAdmin123!")
    res_admin = await admin_client.get("/api/v1/student/recommendations")
    assert res_admin.status_code == 403

    # 4. Student (allowed)
    student_client = await get_authenticated_client("0071234321", "PasswordSiswa123!")
    res_student = await student_client.get("/api/v1/student/recommendations")
    assert res_student.status_code == 200

    # Privacy Invariant: Cache-Control must be private
    cache_header = res_student.headers.get("cache-control", "")
    assert "private" in cache_header.lower()
    assert "no-store" in cache_header.lower()

    data = res_student.json()
    assert "scoringVersion" in data
    assert "catalogVersion" in data
    assert "mappingVersion" in data
    assert "evidenceConfidence" in data
    assert "careerPaths" in data
    assert "studyPaths" in data
    assert "disclaimer" in data


@pytest.mark.asyncio
async def test_recommendation_refresh_endpoint(setup_recommendation_service):
    """
    Tests POST /api/v1/student/recommendations/refresh explicitly forces recomputation.
    """
    student_client = await get_authenticated_client("0071234321", "PasswordSiswa123!")
    res = await student_client.post("/api/v1/student/recommendations/refresh")
    assert res.status_code == 200
    data = res.json()
    assert data["evidenceConfidence"]["level"] in ["limited", "developing", "moderate", "strong"]
    assert "Cache-Control" in res.headers
    assert "private" in res.headers["Cache-Control"]
