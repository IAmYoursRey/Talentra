import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base
from app.core.security import create_access_token, hash_password
from app.db.models import SchoolModel, UserModel, AuthIdentityModel, ClassModel, EnrollmentModel, TeacherAssignmentModel
from app.domain.enums import UserRole
from app.domain.models import SessionRecord
from app.repositories.postgres import PostgresIdentityRepository, PostgresSessionRepository, PostgresAuditRepository
from app.repositories.portfolio import InMemoryPortfolioRepository
from app.repositories.validation import TeacherValidationRepository
from app.services.teacher_review_service import TeacherReviewService
from app.api.v1.teacher_reviews import set_teacher_review_service
from app.api import dependencies
from app.main import app


async def setup_class_test_db(tmp_path):
    db_file = tmp_path / f"admin_class_test_{uuid.uuid4().hex[:8]}.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    school_a_id = "sch_cls_alpha"
    school_b_id = "sch_cls_beta"

    admin_a_id = "usr_adm_cls_a"
    teacher_a_id = "usr_tch_cls_a"
    student_a_id = "usr_std_cls_a"
    class_1_id = "cls_alpha_1"
    class_2_id = "cls_alpha_2"

    async with session_factory() as session:
        school_a = SchoolModel(id=school_a_id, name="SMK 1 Jakarta", status="active")
        school_b = SchoolModel(id=school_b_id, name="SMK 2 Bandung", status="active")

        admin_a = UserModel(
            id=admin_a_id, school_id=school_a_id, role="admin", status="active",
            display_name="Admin Kelas A", email="admin@cls.id"
        )
        teacher_a = UserModel(
            id=teacher_a_id, school_id=school_a_id, role="teacher", status="active",
            display_name="Guru Validator A", email="teacher@cls.id"
        )
        student_a = UserModel(
            id=student_a_id, school_id=school_a_id, role="student", status="active",
            display_name="Siswa Budi", email="budi@cls.id"
        )

        class_1 = ClassModel(
            id=class_1_id, school_id=school_a_id, name="X RPL 1", grade_level="10",
            academic_year="2025/2026", status="active"
        )
        class_2 = ClassModel(
            id=class_2_id, school_id=school_a_id, name="XI RPL 1", grade_level="11",
            academic_year="2025/2026", status="active"
        )

        session.add_all([school_a, school_b, admin_a, teacher_a, student_a, class_1, class_2])
        await session.commit()

    return engine, session_factory, {
        "school_a_id": school_a_id,
        "school_b_id": school_b_id,
        "admin_a_id": admin_a_id,
        "teacher_a_id": teacher_a_id,
        "student_a_id": student_a_id,
        "class_1_id": class_1_id,
        "class_2_id": class_2_id,
    }


def make_admin_session(admin_id: str, school_id: str):
    sid = str(uuid.uuid4())
    token, _ = create_access_token(user_id=admin_id, school_id=school_id, role=UserRole.ADMIN, session_id=sid)
    return sid, token


def make_teacher_session(teacher_id: str, school_id: str):
    sid = str(uuid.uuid4())
    token, _ = create_access_token(user_id=teacher_id, school_id=school_id, role=UserRole.TEACHER, session_id=sid)
    return sid, token


@pytest.mark.asyncio
async def test_class_lifecycle_and_archival(tmp_path):
    engine, session_factory, ids = await setup_class_test_db(tmp_path)
    try:
        ident_repo = PostgresIdentityRepository(session_factory=session_factory)
        sess_repo = PostgresSessionRepository(session_factory=session_factory)
        audit_repo = PostgresAuditRepository(session_factory=session_factory)

        dependencies.set_identity_repo(ident_repo)
        dependencies.set_session_repo(sess_repo)
        dependencies.set_audit_repo(audit_repo)

        sid_a, token_a = make_admin_session(ids["admin_a_id"], ids["school_a_id"])
        await sess_repo.create_session(SessionRecord(
            session_id=sid_a, user_id=ids["admin_a_id"], school_id=ids["school_a_id"],
            role=UserRole.ADMIN, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            client.cookies.set("talentra_session", token_a)
            csrf_res = await client.get("/api/v1/auth/csrf")
            csrf_token = csrf_res.json()["csrfToken"]

            # 1. Create class
            create_res = await client.post(
                "/api/v1/admin/classes",
                headers={"X-CSRF-Token": csrf_token},
                json={
                    "name": "XII RPL 1",
                    "gradeLevel": "12",
                    "academicYear": "2025/2026",
                },
            )
            assert create_res.status_code == 201
            created_class = create_res.json()
            class_id = created_class["id"]
            assert created_class["name"] == "XII RPL 1"
            assert created_class["status"] == "active"

            # 2. Update class
            update_res = await client.patch(
                f"/api/v1/admin/classes/{class_id}",
                headers={"X-CSRF-Token": csrf_token},
                json={"name": "XII Rekayasa Perangkat Lunak 1"},
            )
            assert update_res.status_code == 200
            assert update_res.json()["name"] == "XII Rekayasa Perangkat Lunak 1"

            # 3. Archive class (preserves historical record)
            arch_res = await client.post(
                f"/api/v1/admin/classes/{class_id}/archive",
                headers={"X-CSRF-Token": csrf_token},
            )
            assert arch_res.status_code == 200

            # Verify status is archived
            detail_res = await client.get(f"/api/v1/admin/classes/{class_id}")
            assert detail_res.status_code == 200
            assert detail_res.json()["status"] == "archived"
    finally:
        dependencies.set_identity_repo(None)
        dependencies.set_session_repo(None)
        dependencies.set_audit_repo(None)
        await engine.dispose()


@pytest.mark.asyncio
async def test_student_enrollment_and_historical_preservation(tmp_path):
    engine, session_factory, ids = await setup_class_test_db(tmp_path)
    try:
        ident_repo = PostgresIdentityRepository(session_factory=session_factory)
        sess_repo = PostgresSessionRepository(session_factory=session_factory)
        audit_repo = PostgresAuditRepository(session_factory=session_factory)

        dependencies.set_identity_repo(ident_repo)
        dependencies.set_session_repo(sess_repo)
        dependencies.set_audit_repo(audit_repo)

        sid_a, token_a = make_admin_session(ids["admin_a_id"], ids["school_a_id"])
        await sess_repo.create_session(SessionRecord(
            session_id=sid_a, user_id=ids["admin_a_id"], school_id=ids["school_a_id"],
            role=UserRole.ADMIN, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            client.cookies.set("talentra_session", token_a)
            csrf_res = await client.get("/api/v1/auth/csrf")
            csrf_token = csrf_res.json()["csrfToken"]

            # 1. Enroll student into Class 1
            enr_res = await client.post(
                f"/api/v1/admin/classes/{ids['class_1_id']}/students",
                headers={"X-CSRF-Token": csrf_token},
                json={"studentId": ids["student_a_id"]},
            )
            assert enr_res.status_code == 200

            # Check student appears in class detail
            cls_detail = await client.get(f"/api/v1/admin/classes/{ids['class_1_id']}")
            assert cls_detail.status_code == 200
            assert cls_detail.json()["studentsCount"] == 1
            assert cls_detail.json()["students"][0]["id"] == ids["student_a_id"]

            # 2. Unenroll student
            unenr_res = await client.delete(
                f"/api/v1/admin/classes/{ids['class_1_id']}/students/{ids['student_a_id']}",
                headers={"X-CSRF-Token": csrf_token},
            )
            assert unenr_res.status_code == 200

            # Inactive enrollment preserved in DB, but active count drops to 0
            cls_detail2 = await client.get(f"/api/v1/admin/classes/{ids['class_1_id']}")
            assert cls_detail2.json()["studentsCount"] == 0
    finally:
        dependencies.set_identity_repo(None)
        dependencies.set_session_repo(None)
        dependencies.set_audit_repo(None)
        await engine.dispose()


@pytest.mark.asyncio
async def test_teacher_assignment_controls_validation_queue_scope(tmp_path):
    """
    CRITICAL CROSS-PHASE REGRESSION:
    1. Student in Class 1 submits portfolio.
    2. Teacher assigned to Class 1 sees submission in queue.
    3. Admin removes teacher assignment from Class 1.
    4. Teacher queue immediately drops the Class 1 submission.
    """
    engine, session_factory, ids = await setup_class_test_db(tmp_path)
    try:
        ident_repo = PostgresIdentityRepository(session_factory=session_factory)
        sess_repo = PostgresSessionRepository(session_factory=session_factory)
        audit_repo = PostgresAuditRepository(session_factory=session_factory)

        dependencies.set_identity_repo(ident_repo)
        dependencies.set_session_repo(sess_repo)
        dependencies.set_audit_repo(audit_repo)

        # In-memory portfolio repo with 1 submitted item for Student A
        portfolio_repo = InMemoryPortfolioRepository()
        portfolio_id = "port_test_001"
        revision_id = "rev_test_001"
        portfolio_repo.items[portfolio_id] = {
            "portfolio_id": portfolio_id,
            "school_id": ids["school_a_id"],
            "student_id": ids["student_a_id"],
            "title": "Aplikasi Web Inventory",
            "activity_type": "project",
            "status": "submitted",
            "current_revision_id": revision_id,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }

        # Initialize teacher review service with the same DB session factory
        review_service = TeacherReviewService(
            portfolio_repo=portfolio_repo,
            validation_repo=TeacherValidationRepository(session_factory=session_factory),
        )
        set_teacher_review_service(review_service)

        # Admin session
        sid_a, token_a = make_admin_session(ids["admin_a_id"], ids["school_a_id"])
        await sess_repo.create_session(SessionRecord(
            session_id=sid_a, user_id=ids["admin_a_id"], school_id=ids["school_a_id"],
            role=UserRole.ADMIN, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        # Teacher session
        sid_t, token_t = make_teacher_session(ids["teacher_a_id"], ids["school_a_id"])
        await sess_repo.create_session(SessionRecord(
            session_id=sid_t, user_id=ids["teacher_a_id"], school_id=ids["school_a_id"],
            role=UserRole.TEACHER, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            client.cookies.set("talentra_session", token_a)
            csrf_res = await client.get("/api/v1/auth/csrf")
            csrf_token = csrf_res.json()["csrfToken"]

            # Enroll Student A in Class 1
            await client.post(
                f"/api/v1/admin/classes/{ids['class_1_id']}/students",
                headers={"X-CSRF-Token": csrf_token},
                json={"studentId": ids["student_a_id"]},
            )

            # Assign Teacher A to Class 1
            asg_res = await client.post(
                f"/api/v1/admin/classes/{ids['class_1_id']}/teachers",
                headers={"X-CSRF-Token": csrf_token},
                json={"teacherId": ids["teacher_a_id"], "assignmentType": "portfolio_validator"},
            )
            assert asg_res.status_code == 200

            # Check Teacher queue -> Must SEE Student A's submitted portfolio!
            client.cookies.set("talentra_session", token_t)
            queue_res1 = await client.get("/api/v1/teacher/reviews")
            assert queue_res1.status_code == 200
            assert queue_res1.json()["total"] == 1
            assert queue_res1.json()["items"][0]["portfolioId"] == portfolio_id

            # Now Admin REMOVES Teacher A's assignment from Class 1
            client.cookies.set("talentra_session", token_a)
            del_asg_res = await client.delete(
                f"/api/v1/admin/classes/{ids['class_1_id']}/teachers/{ids['teacher_a_id']}",
                headers={"X-CSRF-Token": csrf_token},
            )
            assert del_asg_res.status_code == 200

            # Check Teacher queue -> MUST BE EMPTY now!
            client.cookies.set("talentra_session", token_t)
            queue_res2 = await client.get("/api/v1/teacher/reviews")
            assert queue_res2.status_code == 200
            assert queue_res2.json()["total"] == 0, "Regression failure: Teacher still sees unassigned class items!"
    finally:
        set_teacher_review_service(None)
        dependencies.set_identity_repo(None)
        dependencies.set_session_repo(None)
        dependencies.set_audit_repo(None)
        await engine.dispose()
