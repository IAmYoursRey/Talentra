import pytest
from datetime import datetime, timezone
from fastapi import HTTPException

from app.domain.models import User, School
from app.domain.enums import UserRole, UserStatus, VerificationStatus
from app.domain.documents import CVContentSnapshotDocument
from app.repositories.portfolio import InMemoryPortfolioRepository
from app.repositories.verification import InMemoryVerificationRepository
from app.repositories.postgres import PostgresIdentityRepository
from app.services.cv_service import CVService
from app.services.public_verification_service import PublicVerificationService
from app.core.cv_security import generate_verification_token, hash_verification_token


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
def revocation_env():
    school_1 = School(id="sch_01", name="SMK 1 Jakarta", npsn_masked="NPSN: *****001")
    school_2 = School(id="sch_02", name="SMK 2 Surabaya", npsn_masked="NPSN: *****002")

    student_1 = User(id="stu_01", school_id="sch_01", role=UserRole.STUDENT, status=UserStatus.ACTIVE, display_name="Siswa A", email="siswa_a@smk.sch.id", masked_identifier="NISN: *******001", must_change_password=False)
    student_2 = User(id="stu_02", school_id="sch_01", role=UserRole.STUDENT, status=UserStatus.ACTIVE, display_name="Siswa B", email="siswa_b@smk.sch.id", masked_identifier="NISN: *******002", must_change_password=False)
    admin_1 = User(id="adm_01", school_id="sch_01", role=UserRole.ADMIN, status=UserStatus.ACTIVE, display_name="Admin SMK 1", email="admin@smk1.sch.id", masked_identifier="NIP: *******001", must_change_password=False)
    admin_2 = User(id="adm_02", school_id="sch_02", role=UserRole.ADMIN, status=UserStatus.ACTIVE, display_name="Admin SMK 2", email="admin@smk2.sch.id", masked_identifier="NIP: *******002", must_change_password=False)
    teacher_1 = User(id="tch_01", school_id="sch_01", role=UserRole.TEACHER, status=UserStatus.ACTIVE, display_name="Guru SMK 1", email="guru@smk1.sch.id", masked_identifier="NUPTK: *******001", must_change_password=False)

    id_repo = MockIdentityRepo()
    for s in [school_1, school_2]:
        id_repo.schools[s.id] = s
    for u in [student_1, student_2, admin_1, admin_2, teacher_1]:
        id_repo.users[u.id] = u

    port_repo = InMemoryPortfolioRepository()
    verif_repo = InMemoryVerificationRepository()

    cv_svc = CVService(
        portfolio_repo=port_repo,
        identity_repo=id_repo,
        verification_repo=verif_repo,
    )
    public_svc = PublicVerificationService(
        verification_repo=verif_repo,
        portfolio_repo=port_repo,
    )

    return {
        "cv_svc": cv_svc,
        "public_svc": public_svc,
        "port_repo": port_repo,
        "verif_repo": verif_repo,
        "schools": {"sch_01": school_1, "sch_02": school_2},
        "users": {
            "stu_01": student_1,
            "stu_02": student_2,
            "adm_01": admin_1,
            "adm_02": admin_2,
            "tch_01": teacher_1,
        },
    }


@pytest.mark.asyncio
async def test_student_revocation_lifecycle(revocation_env):
    """
    SECTIONS 51, 91:
    Student revokes own CV -> verification immediately reports REVOKED.
    Another student cannot revoke it.
    """
    cv_svc: CVService = revocation_env["cv_svc"]
    public_svc: PublicVerificationService = revocation_env["public_svc"]
    port_repo: InMemoryPortfolioRepository = revocation_env["port_repo"]
    verif_repo: InMemoryVerificationRepository = revocation_env["verif_repo"]

    snapshot_id = "snap_rev_01"
    snap_doc = CVContentSnapshotDocument(
        snapshot_id=snapshot_id,
        school_id="sch_01",
        student_id="stu_01",
        profile={"display_name": "Siswa A", "school_name": "SMK 1 Jakarta"},
        status="issued",
    )
    await port_repo.save_cv_snapshot(snap_doc)

    raw_token = generate_verification_token()
    token_hash = hash_verification_token(raw_token)
    verif_rec = await verif_repo.create_verification_record({
        "school_id": "sch_01",
        "student_id": "stu_01",
        "cv_snapshot_id": snapshot_id,
        "token_hash": token_hash,
        "display_code": "TLN-REV1-TEST",
        "snapshot_digest": "abcdef",
        "status": VerificationStatus.ACTIVE.value,
        "issued_at": datetime.now(timezone.utc),
    })

    # Verify public status is verified before revocation
    res_before = await public_svc.verify_public_token(raw_token)
    assert res_before["status"] == "verified"

    # Student 2 tries to revoke Student 1's CV -> Fails
    with pytest.raises(HTTPException):
        await cv_svc.revoke_cv(
            school_id="sch_01",
            student_id="stu_02",  # Different student!
            snapshot_id=snapshot_id,
        )

    # Student 1 revokes own CV
    revoke_res = await cv_svc.revoke_cv(
        school_id="sch_01",
        student_id="stu_01",
        snapshot_id=snapshot_id,
        reason="Diperbarui dengan sertifikasi baru",
    )
    assert revoke_res["status"] == "revoked"

    # Public verification immediately reports revoked
    res_after = await public_svc.verify_public_token(raw_token)
    assert res_after["status"] == "revoked"
    assert "tidak lagi berlaku" in res_after["message"]


@pytest.mark.asyncio
async def test_admin_revocation_policy_and_tenant_boundary(revocation_env):
    """
    SECTIONS 52, 92:
    - Same-school Admin can revoke verification with required reason.
    - Other-school Admin is denied with 403.
    - Reason is mandatory.
    """
    cv_svc: CVService = revocation_env["cv_svc"]
    verif_repo: InMemoryVerificationRepository = revocation_env["verif_repo"]
    public_svc: PublicVerificationService = revocation_env["public_svc"]

    raw_token = generate_verification_token()
    token_hash = hash_verification_token(raw_token)
    verif_rec = await verif_repo.create_verification_record({
        "id": "rec_admin_rev_01",
        "school_id": "sch_01",
        "student_id": "stu_01",
        "cv_snapshot_id": "snap_admin_01",
        "token_hash": token_hash,
        "display_code": "TLN-ADM1-TEST",
        "snapshot_digest": "abcdef123",
        "status": VerificationStatus.ACTIVE.value,
        "issued_at": datetime.now(timezone.utc),
    })

    # 1. Other-school admin attempts revocation -> 403 Forbidden
    with pytest.raises(HTTPException) as exc_cross:
        await cv_svc.admin_revoke_cv(
            school_id="sch_02",  # Different school!
            admin_user_id="adm_02",
            verification_id="rec_admin_rev_01",
            reason="Pencabutan dokumen cross-tenant",
        )
    assert exc_cross.value.status_code == 403
    assert "bukan berasal dari sekolah Anda" in exc_cross.value.detail

    # 2. Same-school admin without valid reason (< 5 chars) -> 400 Bad Request
    with pytest.raises(HTTPException) as exc_reason:
        await cv_svc.admin_revoke_cv(
            school_id="sch_01",
            admin_user_id="adm_01",
            verification_id="rec_admin_rev_01",
            reason="abc",
        )
    assert exc_reason.value.status_code == 400

    # 3. Same-school admin with valid reason -> Allowed
    admin_res = await cv_svc.admin_revoke_cv(
        school_id="sch_01",
        admin_user_id="adm_01",
        verification_id="rec_admin_rev_01",
        reason="Ditemukan ketidaksesuaian data prestasi siswa.",
    )
    assert admin_res["status"] == "revoked"

    # Public verification immediately reflects revocation
    res_after = await public_svc.verify_public_token(raw_token)
    assert res_after["status"] == "revoked"
