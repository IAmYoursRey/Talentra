import pytest
import uuid
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.projection_service import StudentSkillProjectionService
from app.repositories.portfolio import InMemoryPortfolioRepository
from app.repositories.validation import TeacherValidationRepository
from app.repositories.skill_tag import SkillTagRepository
from app.api.v1.student_skills import set_projection_service
from app.domain.documents import EvidenceTagSnapshotDocument, PortfolioItemDocument


@pytest.fixture(autouse=True)
def setup_projection_service():
    portfolio_repo = InMemoryPortfolioRepository()
    validation_repo = TeacherValidationRepository()
    skill_tag_repo = SkillTagRepository()

    proj_svc = StudentSkillProjectionService(
        portfolio_repo=portfolio_repo,
        validation_repo=validation_repo,
        skill_tag_repo=skill_tag_repo,
    )
    set_projection_service(proj_svc)

    yield {
        "projection_service": proj_svc,
        "portfolio_repo": portfolio_repo,
        "validation_repo": validation_repo,
    }

    set_projection_service(None)


async def get_authenticated_client(identifier: str, password: str = "PasswordSiswa123!") -> AsyncClient:
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    res = await client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})
    assert res.status_code == 200
    return client


# --- 1. Approved-Only Invariant & Zero-Signal for Non-Approved Work ---

@pytest.mark.asyncio
async def test_approved_only_invariant(setup_projection_service):
    """
    SECTION 63:
    Create student with:
    - 2 approved portfolios
    - 5 submitted portfolios
    - 3 rejected portfolios
    - 1 revision_requested portfolio
    Expected: Radar sees ONLY 2 approved portfolios.
    Submitted, rejected, revision_requested contribute ZERO.
    """
    services = setup_projection_service
    portfolio_repo: InMemoryPortfolioRepository = services["portfolio_repo"]
    proj_service: StudentSkillProjectionService = services["projection_service"]

    school_id = "sch_teladan_001"
    student_id = "usr_std_001"  # Alya

    # Create 2 approved items + snapshots
    for i in range(1, 3):
        pid = f"port_approved_{i}"
        revid = f"rev_approved_{i}"
        decid = f"dec_approved_{i}"
        portfolio_repo.items[pid] = {
            "portfolio_id": pid,
            "school_id": school_id,
            "student_id": student_id,
            "title": f"Approved Portfolio {i}",
            "activity_type": "project",
            "status": "approved",
            "current_revision_id": revid,
            "canonical_tag_ids": ["web-development", "digital-literacy"],
            "submitted_at": datetime.now(timezone.utc),
        }
        await proj_service.project_approved_evidence(
            school_id=school_id,
            student_id=student_id,
            portfolio_id=pid,
            revision_id=revid,
            validation_decision_id=decid,
            canonical_tag_ids=["web-development", "digital-literacy"],
        )

    # Create 5 submitted items (NO projection snapshot)
    for i in range(1, 6):
        pid = f"port_submitted_{i}"
        portfolio_repo.items[pid] = {
            "portfolio_id": pid,
            "school_id": school_id,
            "student_id": student_id,
            "title": f"Submitted Portfolio {i}",
            "activity_type": "project",
            "status": "submitted",
            "canonical_tag_ids": ["problem-solving", "research"],
            "submitted_at": datetime.now(timezone.utc),
        }

    # Create 3 rejected items (NO projection snapshot)
    for i in range(1, 4):
        pid = f"port_rejected_{i}"
        portfolio_repo.items[pid] = {
            "portfolio_id": pid,
            "school_id": school_id,
            "student_id": student_id,
            "title": f"Rejected Portfolio {i}",
            "activity_type": "project",
            "status": "rejected",
            "canonical_tag_ids": ["leadership", "event-management"],
            "submitted_at": datetime.now(timezone.utc),
        }

    # Create 1 revision_requested item (NO projection snapshot)
    pid = "port_rev_req_1"
    portfolio_repo.items[pid] = {
        "portfolio_id": pid,
        "school_id": school_id,
        "student_id": student_id,
        "title": "Revision Requested Portfolio",
        "activity_type": "project",
        "status": "revision_requested",
        "canonical_tag_ids": ["teamwork"],
        "submitted_at": datetime.now(timezone.utc),
    }

    # Query student skills API
    client = await get_authenticated_client("0071234321")
    res = await client.get("/api/v1/student/skills")
    assert res.status_code == 200
    data = res.json()

    assert data["approvedEvidenceCount"] == 2
    assert data["scoringVersion"] == "approved-evidence-count-v1"

    radar = {r["dimension"]: r for r in data["radar"]}
    # 'digital-literacy' was mapped from 'web-development' and 'digital-literacy'
    # 2 unique approved portfolios -> 2 * 20 = 40 score
    assert radar["digital-literacy"]["score"] == 40
    assert radar["digital-literacy"]["evidenceCount"] == 2

    # All unapproved dimensions MUST have 0 score and 0 evidence count
    assert radar["problem-solving"]["score"] == 0
    assert radar["problem-solving"]["evidenceCount"] == 0
    assert radar["leadership"]["score"] == 0
    assert radar["leadership"]["evidenceCount"] == 0
    assert radar["collaboration"]["score"] == 0
    assert radar["collaboration"]["evidenceCount"] == 0


# --- 2. Tag Stacking Prevention ---

@pytest.mark.asyncio
async def test_tag_stacking_prevention(setup_projection_service):
    """
    SECTION 64:
    Approved portfolio has:
    - ui-ux
    - graphic-design
    - creativity
    All 3 mapped to 'creativity'.
    Expected: creativity evidence count += 1, NOT 3! Score is 20, NOT 60!
    """
    services = setup_projection_service
    portfolio_repo: InMemoryPortfolioRepository = services["portfolio_repo"]
    proj_service: StudentSkillProjectionService = services["projection_service"]

    school_id = "sch_teladan_001"
    student_id = "usr_std_001"

    pid = "port_stacked_1"
    portfolio_repo.items[pid] = {
        "portfolio_id": pid,
        "school_id": school_id,
        "student_id": student_id,
        "title": "Desain Branding Visual & Identitas",
        "status": "approved",
        "canonical_tag_ids": ["ui-ux", "graphic-design", "creativity"],
    }

    await proj_service.project_approved_evidence(
        school_id=school_id,
        student_id=student_id,
        portfolio_id=pid,
        revision_id="rev_stacked_1",
        validation_decision_id="dec_stacked_1",
        canonical_tag_ids=["ui-ux", "graphic-design", "creativity"],
    )

    client = await get_authenticated_client("0071234321")
    res = await client.get("/api/v1/student/skills")
    assert res.status_code == 200
    data = res.json()

    radar = {r["dimension"]: r for r in data["radar"]}
    creativity = radar["creativity"]
    # MANDATORY: Evidence count is exactly 1 (not 3), Score is 20 (not 60)
    assert creativity["evidenceCount"] == 1
    assert creativity["score"] == 20
    # Contributor links to the 1 portfolio
    assert len(creativity["contributors"]) == 1
    assert creativity["contributors"][0]["portfolioId"] == pid


# --- 3. Radar Formula V1 ---

@pytest.mark.asyncio
async def test_radar_formula_v1_deterministic_scaling(setup_projection_service):
    """
    SECTION 65:
    Formula: min(100, evidence_units * 20)
    0 evidence -> 0
    1 -> 20
    2 -> 40
    3 -> 60
    4 -> 80
    5 -> 100
    6+ -> 100
    """
    services = setup_projection_service
    portfolio_repo: InMemoryPortfolioRepository = services["portfolio_repo"]
    proj_service: StudentSkillProjectionService = services["projection_service"]

    school_id = "sch_teladan_001"
    student_id = "usr_std_001"

    # Add 6 distinct approved portfolios with 'leadership'
    for i in range(1, 7):
        pid = f"port_lead_{i}"
        portfolio_repo.items[pid] = {
            "portfolio_id": pid,
            "school_id": school_id,
            "student_id": student_id,
            "title": f"Kepemimpinan Kegiatan {i}",
            "status": "approved",
            "canonical_tag_ids": ["leadership"],
        }
        await proj_service.project_approved_evidence(
            school_id=school_id,
            student_id=student_id,
            portfolio_id=pid,
            revision_id=f"rev_lead_{i}",
            validation_decision_id=f"dec_lead_{i}",
            canonical_tag_ids=["leadership"],
        )

        # Test incremental score at each step
        skills = await proj_service.get_student_skills(school_id, student_id)
        radar = {r["dimension"]: r for r in skills["radar"]}
        expected_score = min(100, i * 20)
        assert radar["leadership"]["evidenceCount"] == i
        assert radar["leadership"]["score"] == expected_score


# --- 4. Provenance Transparency ---

@pytest.mark.asyncio
async def test_provenance_transparency(setup_projection_service):
    """
    SECTION 66:
    Every non-zero dimension must provide contributor data linking to actual approved portfolios.
    No ghost contribution.
    """
    services = setup_projection_service
    portfolio_repo: InMemoryPortfolioRepository = services["portfolio_repo"]
    proj_service: StudentSkillProjectionService = services["projection_service"]

    school_id = "sch_teladan_001"
    student_id = "usr_std_001"

    pid = "port_prov_1"
    p_title = "Riset Komputasi Awan"
    portfolio_repo.items[pid] = {
        "portfolio_id": pid,
        "school_id": school_id,
        "student_id": student_id,
        "title": p_title,
        "status": "approved",
        "canonical_tag_ids": ["research"],
    }
    await proj_service.project_approved_evidence(
        school_id=school_id,
        student_id=student_id,
        portfolio_id=pid,
        revision_id="rev_prov_1",
        validation_decision_id="dec_prov_1",
        canonical_tag_ids=["research"],
    )

    client = await get_authenticated_client("0071234321")
    res = await client.get("/api/v1/student/skills")
    assert res.status_code == 200
    data = res.json()

    radar = {r["dimension"]: r for r in data["radar"]}
    prob_solving = radar["problem-solving"]  # 'research' maps to 'problem-solving'
    assert len(prob_solving["contributors"]) == 1
    contrib = prob_solving["contributors"][0]
    assert contrib["portfolioId"] == pid
    assert contrib["title"] == p_title
    assert "research" in contrib["tags"]


# --- 5. Projector Idempotency on Retry ---

@pytest.mark.asyncio
async def test_projector_idempotency_retry(setup_projection_service):
    """
    SECTION 22 & 70:
    Retrying the projection with the same validation_decision_id must NOT duplicate snapshots.
    """
    services = setup_projection_service
    portfolio_repo: InMemoryPortfolioRepository = services["portfolio_repo"]
    proj_service: StudentSkillProjectionService = services["projection_service"]

    school_id = "sch_teladan_001"
    student_id = "usr_std_001"
    dec_id = "dec_idem_123"

    # First projection
    s1 = await proj_service.project_approved_evidence(
        school_id=school_id,
        student_id=student_id,
        portfolio_id="port_1",
        revision_id="rev_1",
        validation_decision_id=dec_id,
        canonical_tag_ids=["web-development"],
    )

    # Second projection (retry)
    s2 = await proj_service.project_approved_evidence(
        school_id=school_id,
        student_id=student_id,
        portfolio_id="port_1",
        revision_id="rev_1",
        validation_decision_id=dec_id,
        canonical_tag_ids=["web-development"],
    )

    assert s1.validation_decision_id == s2.validation_decision_id
    snapshots = await portfolio_repo.get_evidence_tag_snapshots_for_student(school_id, student_id)
    assert len(snapshots) == 1
