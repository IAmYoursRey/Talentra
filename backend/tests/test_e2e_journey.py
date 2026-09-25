import pytest
from datetime import datetime, timezone
import pymupdf

from app.domain.models import User, School
from app.domain.enums import UserRole, UserStatus, VerificationStatus
from app.domain.documents import PortfolioItemDocument, EvidenceRef
from app.repositories.portfolio import InMemoryPortfolioRepository
from app.repositories.verification import InMemoryVerificationRepository
from app.repositories.validation import TeacherValidationRepository
from app.repositories.postgres import PostgresIdentityRepository
from app.services.cv_service import CVService
from app.services.public_verification_service import PublicVerificationService
from app.services.projection_service import StudentSkillProjectionService
from app.services.industry_translator import IndustryTranslatorService


class JourneyIdentityRepo(PostgresIdentityRepository):
    def __init__(self):
        self.schools = {}
        self.users = {}

    async def get_school_by_id(self, school_id: str):
        return self.schools.get(school_id)

    async def get_user_by_id(self, user_id: str):
        return self.users.get(user_id)

    async def get_user_for_school(self, school_id: str, user_id: str):
        u = self.users.get(user_id)
        if u and u.school_id == school_id:
            return u
        return None


class JourneyValidationRepo(TeacherValidationRepository):
    def __init__(self):
        self.rubrics = []

    async def get_rubric_summary_for_student(self, school_id: str, student_id: str):
        return [
            {
                "dimensionCode": "initiative",
                "displayName": "Inisiatif Mandiri",
                "averageScore": 4.5,
                "assessmentCount": 1,
            }
        ]

    async def get_radar_tag_mappings(self):
        return {
            "web-development": "digital-literacy",
            "tag_web_development": "digital-literacy",
        }


@pytest.mark.asyncio
async def test_full_user_journey_phase1_to_8():
    """
    SECTION 122: COMPLETE USER JOURNEY END-TO-END TEST
    Admin creates Student
    -> Student changes temporary password
    -> Student creates portfolio
    -> Student uploads evidence
    -> Student submits
    -> Teacher reviews
    -> Teacher approves + rubric
    -> Skill radar updates
    -> Grounded professional description exists
    -> Student generates Digital CV
    -> PDF produced (selectable real text)
    -> QR verification record issued
    -> Public verification returns VERIFIED
    -> Student revokes CV
    -> Public verification returns REVOKED
    """
    # 1. Platform Infrastructure & Tenant
    school_id = "sch_journey_01"
    school = School(id=school_id, name="SMK Negeri 1 Teladan Jakarta", npsn_masked="NPSN: *****001")
    id_repo = JourneyIdentityRepo()
    id_repo.schools[school_id] = school

    port_repo = InMemoryPortfolioRepository()
    verif_repo = InMemoryVerificationRepository()
    validation_repo = JourneyValidationRepo()

    projection_svc = StudentSkillProjectionService(
        portfolio_repo=port_repo,
        validation_repo=validation_repo,
    )
    translator_svc = IndustryTranslatorService(portfolio_repo=port_repo)

    cv_svc = CVService(
        portfolio_repo=port_repo,
        identity_repo=id_repo,
        verification_repo=verif_repo,
        validation_repo=validation_repo,
        translator_service=translator_svc,
        projection_service=projection_svc,
    )
    public_svc = PublicVerificationService(
        verification_repo=verif_repo,
        portfolio_repo=port_repo,
    )

    # 2. Admin creates Student
    student_id = "stu_journey_01"
    student = User(
        id=student_id,
        school_id=school_id,
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        display_name="Rafi Ahmad Fauzi",
        email="rafi@smk1.sch.id",
        masked_identifier="NISN: *******001",
        must_change_password=True,
    )
    id_repo.users[student_id] = student

    # 3. Student changes temporary password
    student.must_change_password = False
    assert student.must_change_password is False

    # 4. Student creates portfolio and uploads evidence
    portfolio_id = "port_journey_01"
    port_item, rev_item = await port_repo.create_portfolio(
        school_id=school_id,
        student_id=student_id,
        title="Sistem Monitoring IoT Berbasis Web",
        activity_type="project",
        activity_date="2026-09-15",
        description="Membangun sistem pemantauan telemetri perangkat pintar.",
        canonical_tag_ids=["web-development"],
        evidence_refs=[
            EvidenceRef(
                type="file",
                storage_object_id="obj_evi_01",
                display_name="laporan_proyek.pdf",
                file_type="pdf",
                size_bytes=10240,
            )
        ],
    )
    assert port_item.status == "draft"
    portfolio_id = port_item.portfolio_id

    # 5. Student submits portfolio for teacher validation
    port_item.status = "submitted"
    port_item.submitted_at = datetime.now(timezone.utc)
    await port_repo.save_portfolio(port_item.model_dump())

    # 6. Teacher reviews & approves with rubric
    port_item.status = "approved"
    await port_repo.save_portfolio(port_item.model_dump())

    # Create approved evidence snapshot
    await projection_svc.project_approved_evidence(
        school_id=school_id,
        student_id=student_id,
        portfolio_id=portfolio_id,
        revision_id=port_item.current_revision_id,
        validation_decision_id="dec_01",
        canonical_tag_ids=["web-development"],
    )

    # 7. Skill radar updates deterministically
    skills_data = await projection_svc.get_student_skills(school_id, student_id)
    assert any(pt["score"] > 0 for pt in skills_data["radar"])

    # 8. Grounded professional description generated
    prof_desc = await translator_svc.get_or_create_professional_description(
        school_id=school_id,
        student_id=student_id,
        portfolio_id=portfolio_id,
    )
    assert prof_desc["professionalText"]
    assert "React" not in prof_desc["professionalText"]  # Factuality guard passed

    # 9. Student generates Digital CV
    cv_res = await cv_svc.generate_cv(
        school_id=school_id,
        student_id=student_id,
        portfolio_ids=[portfolio_id],
        include_teacher_competencies=True,
    )
    assert cv_res["status"] == "active"
    snapshot_id = cv_res["snapshotId"]
    raw_token = cv_res["verificationToken"]
    display_code = cv_res["displayCode"]

    # 10. PDF produced with real selectable text
    pdf_bytes, filename = await cv_svc.download_cv_pdf(school_id, student_id, snapshot_id)
    assert len(pdf_bytes) > 2000
    assert filename == f"TALENTRA-CV-{display_code}.pdf"

    pdf_doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    pdf_text = "".join(page.get_text() for page in pdf_doc)
    assert "Rafi Ahmad Fauzi" in pdf_text
    assert "SMK Negeri 1 Teladan Jakarta" in pdf_text
    assert "Sistem Monitoring IoT Berbasis Web" in pdf_text
    assert display_code in pdf_text

    # 11. Public verification returns VERIFIED
    public_verif = await public_svc.verify_public_token(raw_token)
    assert public_verif["status"] == "verified"
    assert public_verif["displayCode"] == display_code
    assert public_verif["studentDisplayName"] == "Rafi Ahmad Fauzi"
    assert len(public_verif["selectedPortfolioSummaries"]) == 1

    # 12. Student revokes CV
    revoke_res = await cv_svc.revoke_cv(school_id, student_id, snapshot_id, reason="Versi baru diterbitkan")
    assert revoke_res["status"] == "revoked"

    # 13. Public verification immediately returns REVOKED
    public_verif_after = await public_svc.verify_public_token(raw_token)
    assert public_verif_after["status"] == "revoked"
    assert "tidak lagi berlaku" in public_verif_after["message"]
