import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base
from app.core.security import create_access_token
from app.db.models import (
    SchoolModel,
    UserModel,
    ClassModel,
    EnrollmentModel,
    TeacherAssignmentModel,
    ValidationDecisionModel,
    RubricAssessmentModel,
    SkillTagModel,
)
from app.domain.enums import UserRole
from app.domain.models import SessionRecord
from app.repositories.postgres import PostgresIdentityRepository, PostgresSessionRepository, PostgresAuditRepository
from app.repositories.portfolio import InMemoryPortfolioRepository
from app.repositories.validation import TeacherValidationRepository
from app.services.school_analytics_service import SchoolAnalyticsService
from app.api.v1.admin_analytics import set_school_analytics_service
from app.api import dependencies
from app.main import app


async def setup_analytics_test_db(tmp_path):
    db_file = tmp_path / f"admin_analytics_test_{uuid.uuid4().hex[:8]}.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    school_a_id = "sch_analytics_a"
    school_b_id = "sch_analytics_b"

    admin_a_id = "usr_adm_analytics_a"
    teacher_a_id = "usr_tch_analytics_a"

    class_10_students_id = "cls_cohort_10"
    class_4_students_id = "cls_cohort_4"

    # We will create:
    # Class 1: 10 students (students s0 to s9) -> meets threshold >= 5
    # Class 2: 4 students (students s10 to s13) -> below threshold < 5
    students_c10 = [f"usr_std_c10_{i}" for i in range(10)]
    students_c4 = [f"usr_std_c4_{i}" for i in range(4)]

    canonical_tags = [
        ("web-development", "digital-literacy"),
        ("data-analysis", "digital-literacy"),
        ("public-speaking", "communication"),
        ("leadership", "leadership"),
        ("problem-solving", "problem-solving"),
        ("ui-ux", "creativity"),
        ("teamwork", "collaboration"),
    ]

    async with session_factory() as session:
        school_a = SchoolModel(id=school_a_id, name="SMK 1 Jakarta", status="active")
        school_b = SchoolModel(id=school_b_id, name="SMK 2 Bandung", status="active")

        admin_a = UserModel(
            id=admin_a_id, school_id=school_a_id, role="admin", status="active",
            display_name="Admin Analisis", email="admin@analytics.id"
        )
        teacher_a = UserModel(
            id=teacher_a_id, school_id=school_a_id, role="teacher", status="active",
            display_name="Guru Validator", email="teacher@analytics.id"
        )

        c10 = ClassModel(
            id=class_10_students_id, school_id=school_a_id, name="X RPL 10",
            grade_level="10", academic_year="2025/2026", status="active"
        )
        c4 = ClassModel(
            id=class_4_students_id, school_id=school_a_id, name="X RPL 4",
            grade_level="10", academic_year="2025/2026", status="active"
        )

        session.add_all([school_a, school_b, admin_a, teacher_a, c10, c4])

        # Add canonical tags with radar dimensions
        for code, radar_dim in canonical_tags:
            tag = SkillTagModel(
                id=str(uuid.uuid4()),
                code=code,
                display_name=code.replace("-", " ").title(),
                category="technical",
                radar_dimension=radar_dim,
                active=True,
            )
            session.add(tag)

        # Add teacher assignment
        asg = TeacherAssignmentModel(
            id=str(uuid.uuid4()), school_id=school_a_id, teacher_id=teacher_a_id,
            class_id=class_10_students_id, active=True
        )
        session.add(asg)

        # Add 10 students for c10
        for i, sid in enumerate(students_c10):
            std = UserModel(
                id=sid, school_id=school_a_id, role="student", status="active",
                display_name=f"Siswa C10 #{i}", email=f"{sid}@student.id"
            )
            enr = EnrollmentModel(
                id=str(uuid.uuid4()), school_id=school_a_id, class_id=class_10_students_id,
                student_id=sid, academic_year="2025/2026", status="active"
            )
            session.add_all([std, enr])

        # Add 4 students for c4
        for i, sid in enumerate(students_c4):
            std = UserModel(
                id=sid, school_id=school_a_id, role="student", status="active",
                display_name=f"Siswa C4 #{i}", email=f"{sid}@student.id"
            )
            enr = EnrollmentModel(
                id=str(uuid.uuid4()), school_id=school_a_id, class_id=class_4_students_id,
                student_id=sid, academic_year="2025/2026", status="active"
            )
            session.add_all([std, enr])

        await session.commit()

    return engine, session_factory, {
        "school_a_id": school_a_id,
        "school_b_id": school_b_id,
        "admin_a_id": admin_a_id,
        "teacher_a_id": teacher_a_id,
        "class_10_id": class_10_students_id,
        "class_4_id": class_4_students_id,
        "students_c10": students_c10,
        "students_c4": students_c4,
    }


def make_admin_session(admin_id: str, school_id: str):
    sid = str(uuid.uuid4())
    token, _ = create_access_token(user_id=admin_id, school_id=school_id, role=UserRole.ADMIN, session_id=sid)
    return sid, token


@pytest.mark.asyncio
async def test_privacy_threshold_suppression_and_group_size_rule(tmp_path):
    """
    INVARIANT:
    Cohorts < 5 unique students MUST BE SUPPRESSED.
    Cohorts >= 5 unique students MUST BE AGGREGATED.
    Filtering that leaves < 5 students MUST BE SUPPRESSED after filtering.
    """
    engine, session_factory, ids = await setup_analytics_test_db(tmp_path)
    try:
        ident_repo = PostgresIdentityRepository(session_factory=session_factory)
        sess_repo = PostgresSessionRepository(session_factory=session_factory)
        audit_repo = PostgresAuditRepository(session_factory=session_factory)

        dependencies.set_identity_repo(ident_repo)
        dependencies.set_session_repo(sess_repo)
        dependencies.set_audit_repo(audit_repo)

        portfolio_repo = InMemoryPortfolioRepository()
        analytics_service = SchoolAnalyticsService(
            session_factory=session_factory,
            portfolio_repo=portfolio_repo,
            validation_repo=TeacherValidationRepository(session_factory=session_factory),
        )
        set_school_analytics_service(analytics_service)

        sid_a, token_a = make_admin_session(ids["admin_a_id"], ids["school_a_id"])
        await sess_repo.create_session(SessionRecord(
            session_id=sid_a, user_id=ids["admin_a_id"], school_id=ids["school_a_id"],
            role=UserRole.ADMIN, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            client.cookies.set("talentra_session", token_a)

            # 1. Query class with 4 students -> MUST BE SUPPRESSED!
            res_c4 = await client.get(f"/api/v1/admin/analytics/talent?classId={ids['class_4_id']}")
            assert res_c4.status_code == 200
            data_c4 = res_c4.json()
            assert data_c4["suppressed"] is True
            assert data_c4["reason"] == "GROUP_TOO_SMALL"
            assert data_c4["cohortSize"] is None
            for d in data_c4["dimensions"]:
                assert d["suppressed"] is True
                assert d["reason"] == "GROUP_TOO_SMALL"
                assert "coverageRate" not in d
                assert "meanEvidenceIndex" not in d

            # 2. Query class with 10 students -> MUST NOT BE SUPPRESSED!
            res_c10 = await client.get(f"/api/v1/admin/analytics/talent?classId={ids['class_10_id']}")
            assert res_c10.status_code == 200
            data_c10 = res_c10.json()
            assert data_c10["suppressed"] is False
            assert data_c10["cohortSize"] == 10
            for d in data_c10["dimensions"]:
                assert d["suppressed"] is False
                assert d["coverageRate"] == 0.0  # true zero since no evidence yet
                assert d["meanEvidenceIndex"] == 0.0
    finally:
        set_school_analytics_service(None)
        dependencies.set_identity_repo(None)
        dependencies.set_session_repo(None)
        dependencies.set_audit_repo(None)
        await engine.dispose()


@pytest.mark.asyncio
async def test_deterministic_talent_heatmap_formulas(tmp_path):
    """
    VERIFIES EXACT FORMULA CALCULATION:
    10 eligible students in cohort.
    For digital-literacy:
    Student 0: 2 approved portfolios (radar score = 40)
    Student 1: 1 approved portfolio (radar score = 20)
    Student 2: 3 approved portfolios (radar score = 60)
    Student 3: 1 approved portfolio (radar score = 20)
    Students 4-9: 0 approved portfolios (radar score = 0)

    Expected coverageRate = 4 / 10 * 100 = 40.0%
    Expected meanEvidenceIndex = (40 + 20 + 60 + 20 + 0) / 10 = 14.0
    """
    engine, session_factory, ids = await setup_analytics_test_db(tmp_path)
    try:
        ident_repo = PostgresIdentityRepository(session_factory=session_factory)
        sess_repo = PostgresSessionRepository(session_factory=session_factory)
        audit_repo = PostgresAuditRepository(session_factory=session_factory)

        dependencies.set_identity_repo(ident_repo)
        dependencies.set_session_repo(sess_repo)
        dependencies.set_audit_repo(audit_repo)

        portfolio_repo = InMemoryPortfolioRepository()
        school_id = ids["school_a_id"]
        c10_students = ids["students_c10"]

        now = datetime.now(timezone.utc)

        # Helper to seed approved evidence tag snapshots
        def add_snapshot(student_id: str, portfolio_id: str, tags: list):
            snap_id = str(uuid.uuid4())
            portfolio_repo.snapshots[snap_id] = {
                "snapshot_id": snap_id,
                "school_id": school_id,
                "student_id": student_id,
                "portfolio_id": portfolio_id,
                "revision_id": str(uuid.uuid4()),
                "validation_decision_id": str(uuid.uuid4()),
                "canonical_tag_ids": tags,
                "approved_at": now,
            }

        # Student 0: 2 portfolios touching digital-literacy
        add_snapshot(c10_students[0], "p0_1", ["web-development"])
        add_snapshot(c10_students[0], "p0_2", ["data-analysis"])

        # Student 1: 1 portfolio touching digital-literacy
        add_snapshot(c10_students[1], "p1_1", ["web-development"])

        # Student 2: 3 portfolios touching digital-literacy
        add_snapshot(c10_students[2], "p2_1", ["web-development"])
        add_snapshot(c10_students[2], "p2_2", ["data-analysis"])
        add_snapshot(c10_students[2], "p2_3", ["web-development"])

        # Student 3: 1 portfolio with TWO digital-literacy tags -> STACKING PREVENTION ensures 1 unit!
        add_snapshot(c10_students[3], "p3_1", ["web-development", "data-analysis"])

        # Student 4-9 have no approved digital-literacy portfolios

        analytics_service = SchoolAnalyticsService(
            session_factory=session_factory,
            portfolio_repo=portfolio_repo,
            validation_repo=TeacherValidationRepository(session_factory=session_factory),
        )
        set_school_analytics_service(analytics_service)

        sid_a, token_a = make_admin_session(ids["admin_a_id"], ids["school_a_id"])
        await sess_repo.create_session(SessionRecord(
            session_id=sid_a, user_id=ids["admin_a_id"], school_id=ids["school_a_id"],
            role=UserRole.ADMIN, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            client.cookies.set("talentra_session", token_a)

            res = await client.get(f"/api/v1/admin/analytics/talent?classId={ids['class_10_id']}")
            assert res.status_code == 200
            data = res.json()
            assert data["suppressed"] is False
            assert data["cohortSize"] == 10

            dim_map = {d["dimension"]: d for d in data["dimensions"]}
            dl = dim_map["digital-literacy"]

            assert dl["studentsWithEvidence"] == 4
            assert dl["coverageRate"] == 40.0
            assert dl["meanEvidenceIndex"] == 14.0

            # Communication has 0 evidence -> TRUE ZERO (not suppressed!)
            comm = dim_map["communication"]
            assert comm["studentsWithEvidence"] == 0
            assert comm["coverageRate"] == 0.0
            assert comm["meanEvidenceIndex"] == 0.0
            assert comm["suppressed"] is False
    finally:
        set_school_analytics_service(None)
        dependencies.set_identity_repo(None)
        dependencies.set_session_repo(None)
        dependencies.set_audit_repo(None)
        await engine.dispose()


@pytest.mark.asyncio
async def test_teacher_rubric_aggregates_and_validation_metrics(tmp_path):
    """
    VERIFIES RUBRIC AND OPERATIONAL METRICS:
    - Only applied approved validation decisions contribute to rubric aggregates.
    - Rubric dimensions are separate from evidence radar.
    - Operational throughput and completion rate calculated accurately.
    """
    engine, session_factory, ids = await setup_analytics_test_db(tmp_path)
    try:
        ident_repo = PostgresIdentityRepository(session_factory=session_factory)
        sess_repo = PostgresSessionRepository(session_factory=session_factory)
        audit_repo = PostgresAuditRepository(session_factory=session_factory)

        dependencies.set_identity_repo(ident_repo)
        dependencies.set_session_repo(sess_repo)
        dependencies.set_audit_repo(audit_repo)

        school_id = ids["school_a_id"]
        c10_students = ids["students_c10"]
        teacher_id = ids["teacher_a_id"]

        now = datetime.now(timezone.utc)

        # Seed 5 approved decisions with rubric scores for 5 students
        scores = [4, 5, 3, 4, 4]  # Average = 4.0
        async with session_factory() as session:
            for i, score in enumerate(scores):
                dec_id = str(uuid.uuid4())
                dec = ValidationDecisionModel(
                    id=dec_id,
                    school_id=school_id,
                    portfolio_id=f"port_rubric_{i}",
                    revision_id=f"rev_rubric_{i}",
                    student_id=c10_students[i],
                    teacher_id=teacher_id,
                    action="approved",
                    application_status="applied",
                    created_at=now - timedelta(hours=2),
                    applied_at=now,
                )
                session.add(dec)

                rubric = RubricAssessmentModel(
                    id=str(uuid.uuid4()),
                    school_id=school_id,
                    decision_id=dec_id,
                    portfolio_id=f"port_rubric_{i}",
                    revision_id=f"rev_rubric_{i}",
                    student_id=c10_students[i],
                    teacher_id=teacher_id,
                    dimension_code="initiative",
                    score=score,
                    created_at=now,
                )
                session.add(rubric)

            # Add 1 rejected decision (must not contribute to rubric aggregates)
            dec_rej = ValidationDecisionModel(
                id=str(uuid.uuid4()),
                school_id=school_id,
                portfolio_id="port_rejected",
                revision_id="rev_rejected",
                student_id=c10_students[5],
                teacher_id=teacher_id,
                action="rejected",
                application_status="applied",
                created_at=now - timedelta(hours=1),
                applied_at=now,
            )
            session.add(dec_rej)

            await session.commit()

        portfolio_repo = InMemoryPortfolioRepository()
        # Add 2 pending submissions in portfolio_repo
        portfolio_repo.items["p_pend_1"] = {
            "portfolio_id": "p_pend_1", "school_id": school_id, "student_id": c10_students[6],
            "status": "submitted", "submitted_at": now.isoformat()
        }
        portfolio_repo.items["p_pend_2"] = {
            "portfolio_id": "p_pend_2", "school_id": school_id, "student_id": c10_students[7],
            "status": "submitted", "submitted_at": now.isoformat()
        }

        analytics_service = SchoolAnalyticsService(
            session_factory=session_factory,
            portfolio_repo=portfolio_repo,
            validation_repo=TeacherValidationRepository(session_factory=session_factory),
        )
        set_school_analytics_service(analytics_service)

        sid_a, token_a = make_admin_session(ids["admin_a_id"], ids["school_a_id"])
        await sess_repo.create_session(SessionRecord(
            session_id=sid_a, user_id=ids["admin_a_id"], school_id=ids["school_a_id"],
            role=UserRole.ADMIN, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            client.cookies.set("talentra_session", token_a)

            # 1. Rubrics API
            rub_res = await client.get(f"/api/v1/admin/analytics/rubrics?classId={ids['class_10_id']}")
            assert rub_res.status_code == 200
            rub_data = rub_res.json()
            assert rub_data["suppressed"] is False
            rub_map = {r["dimensionCode"]: r for r in rub_data["rubrics"]}

            init_rubric = rub_map["initiative"]
            assert init_rubric["suppressed"] is False
            assert init_rubric["averageScore"] == 4.0
            assert init_rubric["assessmentCount"] == 5
            assert init_rubric["uniqueStudentCount"] == 5

            # 2. Validation Metrics API
            val_res = await client.get(f"/api/v1/admin/analytics/validation?classId={ids['class_10_id']}")
            assert val_res.status_code == 200
            val_data = val_res.json()
            assert val_data["approvedCount"] == 5
            assert val_data["rejectedCount"] == 1
            assert val_data["completedDecisions"] == 6
            assert val_data["submittedAwaitingValidation"] == 2
            # completionRate = 6 / (6 + 2) * 100 = 75.0%
            assert val_data["validationCompletionRate"] == 75.0
            assert val_data["medianTurnaroundHours"] > 0
    finally:
        set_school_analytics_service(None)
        dependencies.set_identity_repo(None)
        dependencies.set_session_repo(None)
        dependencies.set_audit_repo(None)
        await engine.dispose()
