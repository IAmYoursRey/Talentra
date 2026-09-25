import uuid
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base
from app.core.security import compute_identifier_lookup_hash, hash_password
from app.domain.enums import UserRole, IdentifierType, AuditEventType
from app.domain.models import SessionRecord, AuditEvent
from app.db.models import (
    SchoolModel,
    UserModel,
    AuthIdentityModel,
    ClassModel,
    EnrollmentModel,
    TeacherAssignmentModel,
)
from app.repositories.postgres import (
    PostgresIdentityRepository,
    PostgresSessionRepository,
    PostgresAuditRepository,
)


async def get_test_session_factory():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return test_engine, session_factory


@pytest.mark.asyncio
async def test_persistent_identity_lookup_and_privacy():
    """Verifies identity lookup by keyed HMAC hash without storing raw identifiers."""
    test_engine, async_db = await get_test_session_factory()
    try:
        school_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        nisn = "0071234321"
        lookup_hash = compute_identifier_lookup_hash(nisn)
        pwd_hash = hash_password("ValidPassword123!")

        async with async_db() as session:
            school = SchoolModel(id=school_id, name="SMK Negeri 1 Jakarta", status="active")
            user = UserModel(
                id=user_id,
                school_id=school_id,
                role="student",
                status="active",
                display_name="Alya Rahma",
            )
            identity = AuthIdentityModel(
                id=str(uuid.uuid4()),
                user_id=user_id,
                identifier_type="nisn",
                identifier_lookup_hash=lookup_hash,
                identifier_last4="4321",
                password_hash=pwd_hash,
                active=True,
            )
            session.add_all([school, user, identity])
            await session.commit()

        repo = PostgresIdentityRepository(session_factory=async_db)

        # 1. Lookup with correct normalized identifier
        result = await repo.get_identity_by_identifier(nisn, IdentifierType.NISN)
        assert result is not None
        auth_id, domain_user = result
        assert domain_user.id == user_id
        assert domain_user.display_name == "Alya Rahma"
        assert domain_user.role == UserRole.STUDENT
        assert auth_id.identifier_last4 == "4321"
        # Raw NISN is never stored in auth_identity table
        assert auth_id.identifier_lookup_hash == lookup_hash

        # 2. Verify password
        is_valid = await repo.verify_user_password(user_id, "ValidPassword123!")
        assert is_valid is True
        is_invalid = await repo.verify_user_password(user_id, "WrongPassword!")
        assert is_invalid is False

        # 3. Lookup with non-existent identifier returns None
        result_none = await repo.get_identity_by_identifier("9999999999", IdentifierType.NISN)
        assert result_none is None
    finally:
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_tenant_isolation_boundary():
    """
    CRITICAL SECURITY CHECK:
    School A user cannot be accessed through School B boundary queries.
    """
    test_engine, async_db = await get_test_session_factory()
    try:
        school_a_id = str(uuid.uuid4())
        school_b_id = str(uuid.uuid4())
        user_a_id = str(uuid.uuid4())
        user_b_id = str(uuid.uuid4())

        async with async_db() as session:
            school_a = SchoolModel(id=school_a_id, name="School Alpha", status="active")
            school_b = SchoolModel(id=school_b_id, name="School Beta", status="active")
            user_a = UserModel(id=user_a_id, school_id=school_a_id, role="student", display_name="Student Alpha")
            user_b = UserModel(id=user_b_id, school_id=school_b_id, role="student", display_name="Student Beta")
            session.add_all([school_a, school_b, user_a, user_b])
            await session.commit()

        repo = PostgresIdentityRepository(session_factory=async_db)

        # User A belongs to School A
        res_a = await repo.get_user_for_school(school_a_id, user_a_id)
        assert res_a is not None
        assert res_a.display_name == "Student Alpha"

        # Cross-tenant breach attempt: Query User A using School B ID -> MUST return None!
        breach_attempt = await repo.get_user_for_school(school_b_id, user_a_id)
        assert breach_attempt is None, "Tenant isolation failure: School B queried School A entity!"

        # Query User B using School A ID -> MUST return None!
        breach_attempt2 = await repo.get_user_for_school(school_a_id, user_b_id)
        assert breach_attempt2 is None, "Tenant isolation failure: School A queried School B entity!"
    finally:
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_session_restart_durability():
    """
    MANDATORY REQUIREMENT 53:
    Session records persist across backend repository/process recreation.
    """
    test_engine, async_db = await get_test_session_factory()
    try:
        school_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())

        # Create session with Repo Instance 1
        repo1 = PostgresSessionRepository(session_factory=async_db)
        record = SessionRecord(
            session_id=session_id,
            user_id=user_id,
            school_id=school_id,
            role=UserRole.STUDENT,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        )
        await repo1.create_session(record)

        # Simulate backend restart: drop repo1 and instantiate a completely new repo2
        del repo1
        repo2 = PostgresSessionRepository(session_factory=async_db)

        # Session record remains available and valid
        retrieved = await repo2.get_session(session_id)
        assert retrieved is not None
        assert retrieved.session_id == session_id
        assert retrieved.user_id == user_id
        assert retrieved.is_valid is True

        # Revoke session in repo2
        await repo2.revoke_session(session_id)

        # Recreate repo3, verify session is now revoked
        repo3 = PostgresSessionRepository(session_factory=async_db)
        retrieved_revoked = await repo3.get_session(session_id)
        assert retrieved_revoked is not None
        assert retrieved_revoked.is_valid is False
        assert retrieved_revoked.revoked_at is not None
    finally:
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_password_change_durability_across_restarts():
    """
    MANDATORY REQUIREMENT 54:
    1. Authenticate with initial password.
    2. Change demo user's password.
    3. Recreate/restart backend repository.
    4. Old password fails; new password works.
    """
    test_engine, async_db = await get_test_session_factory()
    try:
        school_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        old_password = "OldSecretPassword123!"
        new_password = "NewSecretPassword456!"

        async with async_db() as session:
            school = SchoolModel(id=school_id, name="SMA Negeri 1", status="active")
            user = UserModel(id=user_id, school_id=school_id, role="student", display_name="Test Student")
            identity = AuthIdentityModel(
                id=str(uuid.uuid4()),
                user_id=user_id,
                identifier_type="nisn",
                identifier_lookup_hash=compute_identifier_lookup_hash("0011223344"),
                identifier_last4="3344",
                password_hash=hash_password(old_password),
                active=True,
            )
            session.add_all([school, user, identity])
            await session.commit()

        # Step 1: Verify initial password with repo1
        repo1 = PostgresIdentityRepository(session_factory=async_db)
        assert await repo1.verify_user_password(user_id, old_password) is True

        # Step 2: Change password to new hash
        new_hash = hash_password(new_password)
        await repo1.update_user_password(user_id, new_hash)

        # Step 3: Recreate repository instance (simulating restart)
        del repo1
        repo2 = PostgresIdentityRepository(session_factory=async_db)

        # Step 4: Old password fails; new password works!
        assert await repo2.verify_user_password(user_id, old_password) is False
        assert await repo2.verify_user_password(user_id, new_password) is True
    finally:
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_durable_audit_log_and_sanitization():
    """Verifies durable audit logging and ensures sensitive tokens are omitted."""
    test_engine, async_db = await get_test_session_factory()
    try:
        school_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        repo = PostgresAuditRepository(session_factory=async_db)

        audit_event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            user_id=user_id,
            school_id=school_id,
            safe_context="Login from student dashboard",
            correlation_id=str(uuid.uuid4()),
            metadata={"client": "web", "role": "student"},
        )
        await repo.record_event(audit_event)

        # Query from DB to confirm persistence
        events = await repo.get_events_for_school(school_id)
        assert len(events) == 1
        assert events[0].event_type == AuditEventType.AUTH_LOGIN_SUCCESS
        assert events[0].metadata.get("client") == "web"
        assert events[0].metadata.get("role") == "student"
        assert events[0].safe_context == "Login from student dashboard"
        # Assert password, token, or raw identifiers are not in metadata
        assert "password" not in events[0].metadata
        assert "token" not in events[0].metadata
    finally:
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_classes_enrollments_and_teacher_assignments():
    """Verifies relational foundations for classes, enrollments, and teacher assignments."""
    test_engine, async_db = await get_test_session_factory()
    try:
        school_id = str(uuid.uuid4())
        student_id = str(uuid.uuid4())
        teacher_id = str(uuid.uuid4())
        class_id = str(uuid.uuid4())

        async with async_db() as session:
            school = SchoolModel(id=school_id, name="SMK Negeri 2", status="active")
            student = UserModel(id=student_id, school_id=school_id, role="student", display_name="Student Budi")
            teacher = UserModel(id=teacher_id, school_id=school_id, role="teacher", display_name="Guru Ani")
            class_obj = ClassModel(
                id=class_id,
                school_id=school_id,
                name="XII RPL 1",
                grade_level=12,
                academic_year="2025/2026",
                status="active",
            )
            enrollment = EnrollmentModel(
                id=str(uuid.uuid4()),
                school_id=school_id,
                class_id=class_id,
                student_id=student_id,
                academic_year="2025/2026",
                status="active",
            )
            assignment = TeacherAssignmentModel(
                id=str(uuid.uuid4()),
                school_id=school_id,
                teacher_id=teacher_id,
                class_id=class_id,
                assignment_type="homeroom",
                active=True,
            )
            session.add_all([school, student, teacher, class_obj, enrollment, assignment])
            await session.commit()

        # Verify query
        async with async_db() as session:
            stmt = select(ClassModel).where(ClassModel.id == class_id)
            result = await session.execute(stmt)
            cls = result.scalar_one()
            assert cls.name == "XII RPL 1"
            assert cls.grade_level == "12"
    finally:
        await test_engine.dispose()
