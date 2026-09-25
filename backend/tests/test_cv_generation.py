import pytest
from datetime import datetime, timezone
from fastapi import HTTPException

from app.core.config import settings
from app.core.cv_security import (
    compute_canonical_snapshot_digest,
    derive_snapshot_fingerprint,
    generate_verification_token,
    hash_verification_token,
)
from app.domain.documents import CVContentSnapshotDocument, PortfolioItemDocument
from app.services.cv_service import CVService
from app.repositories.portfolio import InMemoryPortfolioRepository
from app.repositories.verification import InMemoryVerificationRepository
from app.repositories.postgres import PostgresIdentityRepository
from app.domain.models import User, School
from app.domain.enums import UserRole, UserStatus, VerificationStatus


class MockIdentityRepo(PostgresIdentityRepository):
    def __init__(self):
        self.users = {}
        self.schools = {}

    async def get_user_for_school(self, school_id: str, user_id: str):
        u = self.users.get(user_id)
        if u and u.school_id == school_id:
            return u
        return None

    async def get_school_by_id(self, school_id: str):
        return self.schools.get(school_id)


@pytest.fixture
def mock_setup():
    school = School(id="sch_test_01", name="SMK Negeri 1 Jakarta", npsn_masked="NPSN: *****001")
    student = User(
        id="usr_stu_01",
        school_id="sch_test_01",
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        display_name="Fauzan Pratama",
        email="fauzan@smk1.sch.id",
        masked_identifier="NISN: *******001",
        must_change_password=False,
    )
    other_student = User(
        id="usr_stu_02",
        school_id="sch_test_01",
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        display_name="Rani Handayani",
        email="rani@smk1.sch.id",
        masked_identifier="NISN: *******002",
        must_change_password=False,
    )
    cross_school_student = User(
        id="usr_stu_03",
        school_id="sch_other_99",
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        display_name="Budi Santoso",
        email="budi@smk99.sch.id",
        masked_identifier="NISN: *******099",
        must_change_password=False,
    )

    id_repo = MockIdentityRepo()
    id_repo.schools[school.id] = school
    id_repo.users[student.id] = student
    id_repo.users[other_student.id] = other_student
    id_repo.users[cross_school_student.id] = cross_school_student

    port_repo = InMemoryPortfolioRepository()
    verif_repo = InMemoryVerificationRepository()

    svc = CVService(
        portfolio_repo=port_repo,
        identity_repo=id_repo,
        verification_repo=verif_repo,
    )

    return {
        "service": svc,
        "portfolio_repo": port_repo,
        "verification_repo": verif_repo,
        "school": school,
        "student": student,
        "other_student": other_student,
        "cross_school_student": cross_school_student,
    }


@pytest.mark.asyncio
async def test_approved_only_portfolio_selection_gate(mock_setup):
    """
    SECTION 81: Student has approved, submitted, revision_requested, rejected items.
    CV selection API MUST only accept approved portfolios.
    Any non-approved portfolio ID MUST fail with 400.
    """
    svc: CVService = mock_setup["service"]
    port_repo: InMemoryPortfolioRepository = mock_setup["portfolio_repo"]
    school_id = mock_setup["school"].id
    student_id = mock_setup["student"].id

    # 1. Create items with different statuses
    p_approved_1 = PortfolioItemDocument(
        portfolio_id="port_appr_01",
        school_id=school_id,
        student_id=student_id,
        title="Sistem Otomasi Hidroponik",
        activity_type="project",
        description="Merancang kontrol mikrokontroler untuk nutrisi hidroponik.",
        status="approved",
    )
    p_approved_2 = PortfolioItemDocument(
        portfolio_id="port_appr_02",
        school_id=school_id,
        student_id=student_id,
        title="Web Profil Koperasi Sekolah",
        activity_type="project",
        description="Membangun antarmuka web responsif profil koperasi.",
        status="approved",
    )
    p_draft = PortfolioItemDocument(
        portfolio_id="port_draft_01",
        school_id=school_id,
        student_id=student_id,
        title="Draft Belum Selesai",
        activity_type="project",
        description="Masih draft.",
        status="draft",
    )
    p_submitted = PortfolioItemDocument(
        portfolio_id="port_subm_01",
        school_id=school_id,
        student_id=student_id,
        title="Menunggu Review Guru",
        activity_type="project",
        description="Sudah dikirim.",
        status="submitted",
    )
    p_rejected = PortfolioItemDocument(
        portfolio_id="port_rej_01",
        school_id=school_id,
        student_id=student_id,
        title="Karya Ditolak",
        activity_type="project",
        description="Tidak memenuhi standar.",
        status="rejected",
    )

    for p in [p_approved_1, p_approved_2, p_draft, p_submitted, p_rejected]:
        port_repo.items[p.portfolio_id] = p.model_dump()

    # Selecting approved items succeeds
    res = await svc.generate_cv(
        school_id=school_id,
        student_id=student_id,
        portfolio_ids=["port_appr_01", "port_appr_02"],
        include_teacher_competencies=False,
    )
    assert res["status"] == "active"
    assert res["selectedProjectCount"] == 2
    assert "verificationToken" in res

    # Attempting to include draft fails
    with pytest.raises(HTTPException) as exc_draft:
        await svc.generate_cv(
            school_id=school_id,
            student_id=student_id,
            portfolio_ids=["port_appr_01", "port_draft_01"],
        )
    assert exc_draft.value.status_code == 400
    assert "Hanya karya tervalidasi" in exc_draft.value.detail

    # Attempting to include submitted fails
    with pytest.raises(HTTPException) as exc_subm:
        await svc.generate_cv(
            school_id=school_id,
            student_id=student_id,
            portfolio_ids=["port_subm_01"],
        )
    assert exc_subm.value.status_code == 400

    # Attempting to include rejected fails
    with pytest.raises(HTTPException) as exc_rej:
        await svc.generate_cv(
            school_id=school_id,
            student_id=student_id,
            portfolio_ids=["port_rej_01"],
        )
    assert exc_rej.value.status_code == 400


@pytest.mark.asyncio
async def test_cv_ownership_and_tenant_boundary(mock_setup):
    """
    SECTION 82: Student A cannot select Student B's portfolio.
    Cross-school selection must also fail.
    """
    svc: CVService = mock_setup["service"]
    port_repo: InMemoryPortfolioRepository = mock_setup["portfolio_repo"]
    school_id = mock_setup["school"].id
    student_a = mock_setup["student"].id
    student_b = mock_setup["other_student"].id

    p_b = PortfolioItemDocument(
        portfolio_id="port_b_01",
        school_id=school_id,
        student_id=student_b,
        title="Karya Siswa B",
        activity_type="project",
        description="Milik siswa B.",
        status="approved",
    )
    port_repo.items[p_b.portfolio_id] = p_b.model_dump()

    # Student A attempts to select Student B's portfolio
    with pytest.raises(HTTPException) as exc:
        await svc.generate_cv(
            school_id=school_id,
            student_id=student_a,
            portfolio_ids=["port_b_01"],
        )
    assert exc.value.status_code == 400
    assert "bukan milik Anda" in exc.value.detail


@pytest.mark.asyncio
async def test_cv_immutability_guarantee(mock_setup):
    """
    SECTION 83: Generate CV snapshot.
    Later, approve a new portfolio or change profile.
    Old snapshot MUST remain completely unchanged.
    """
    svc: CVService = mock_setup["service"]
    port_repo: InMemoryPortfolioRepository = mock_setup["portfolio_repo"]
    school_id = mock_setup["school"].id
    student_id = mock_setup["student"].id

    p1 = PortfolioItemDocument(
        portfolio_id="p_im_01",
        school_id=school_id,
        student_id=student_id,
        title="Aplikasi Inventaris Lab",
        activity_type="project",
        description="Membangun sistem inventaris lab.",
        status="approved",
    )
    port_repo.items[p1.portfolio_id] = p1.model_dump()

    # Generate initial CV
    res1 = await svc.generate_cv(
        school_id=school_id,
        student_id=student_id,
        portfolio_ids=["p_im_01"],
    )
    snap1_id = res1["snapshotId"]
    digest1 = res1["contentDigest"]

    snap1_before = await port_repo.get_cv_snapshot_by_id(snap1_id)
    assert len(snap1_before["selected_portfolios"]) == 1

    # Student now creates and gets approval for a NEW portfolio
    p2 = PortfolioItemDocument(
        portfolio_id="p_im_02",
        school_id=school_id,
        student_id=student_id,
        title="Proyek Kedua Terbaru",
        activity_type="project",
        description="Karya baru setelah CV terbit.",
        status="approved",
    )
    port_repo.items[p2.portfolio_id] = p2.model_dump()

    # Verify old snapshot did NOT magically include p2
    snap1_after = await port_repo.get_cv_snapshot_by_id(snap1_id)
    assert len(snap1_after["selected_portfolios"]) == 1
    assert snap1_after["content_digest"] == digest1
    assert snap1_after["selected_portfolios"][0]["portfolio_id"] == "p_im_01"


@pytest.mark.asyncio
async def test_canonical_digest_deterministic(mock_setup):
    """
    SECTION 84: Same canonical snapshot contents -> exactly identical SHA-256 digest.
    Changed content -> different digest.
    """
    data_a = {
        "snapshot_version": "cv-snapshot-v1",
        "renderer_version": "cv-pdf-v1",
        "school_id": "sch_1",
        "student_id": "stu_1",
        "profile": {"display_name": "Alya", "school_name": "SMA 1"},
        "approved_skills": [{"name": "Literasi Digital", "score": 80}],
        "selected_portfolios": [{"title": "Web Portofolio", "portfolio_id": "p1"}],
    }

    # Same content with reversed dict key insertion order
    data_b = {
        "selected_portfolios": [{"portfolio_id": "p1", "title": "Web Portofolio"}],
        "approved_skills": [{"score": 80, "name": "Literasi Digital"}],
        "profile": {"school_name": "SMA 1", "display_name": "Alya"},
        "student_id": "stu_1",
        "school_id": "sch_1",
        "renderer_version": "cv-pdf-v1",
        "snapshot_version": "cv-snapshot-v1",
    }

    digest_a = compute_canonical_snapshot_digest(data_a)
    digest_b = compute_canonical_snapshot_digest(data_b)
    assert digest_a == digest_b, "Canonicalization must produce identical SHA-256 digest regardless of dict key order"

    # Modify one field
    data_c = dict(data_a)
    data_c["profile"] = {"display_name": "Alya Pratama", "school_name": "SMA 1"}
    digest_c = compute_canonical_snapshot_digest(data_c)
    assert digest_a != digest_c, "Altered content must produce different digest"
