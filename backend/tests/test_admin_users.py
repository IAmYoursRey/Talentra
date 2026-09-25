import os
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base
from app.core.security import create_access_token, hash_password, compute_identifier_lookup_hash
from app.db.models import SchoolModel, UserModel, AuthIdentityModel, ClassModel, SessionModel
from app.domain.enums import UserRole, UserStatus
from app.domain.models import SessionRecord
from app.repositories.postgres import PostgresIdentityRepository, PostgresSessionRepository, PostgresAuditRepository
from app.repositories.admin_user import AdminUserRepository
from app.api import dependencies
from app.main import app


async def setup_admin_test_db(tmp_path):
    db_file = tmp_path / f"admin_user_test_{uuid.uuid4().hex[:8]}.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed School A and School B
    school_a_id = "sch_alpha_001"
    school_b_id = "sch_beta_002"

    admin_a_id = "usr_adm_alpha"
    admin_b_id = "usr_adm_beta"
    student_a_id = "usr_std_alpha"
    teacher_a_id = "usr_tch_alpha"
    class_a_id = "cls_alpha_1"

    async with session_factory() as session:
        school_a = SchoolModel(id=school_a_id, name="SMK Negeri 1 Jakarta", status="active")
        school_b = SchoolModel(id=school_b_id, name="SMK Negeri 2 Bandung", status="active")

        admin_a = UserModel(
            id=admin_a_id,
            school_id=school_a_id,
            role="admin",
            status="active",
            display_name="Admin Sekolah Alpha",
            email="admin@alpha.talentra.id",
        )
        admin_b = UserModel(
            id=admin_b_id,
            school_id=school_b_id,
            role="admin",
            status="active",
            display_name="Admin Sekolah Beta",
            email="admin@beta.talentra.id",
        )
        student_a = UserModel(
            id=student_a_id,
            school_id=school_a_id,
            role="student",
            status="active",
            display_name="Siswa Alpha",
            email="student@alpha.talentra.id",
        )
        teacher_a = UserModel(
            id=teacher_a_id,
            school_id=school_a_id,
            role="teacher",
            status="active",
            display_name="Guru Alpha",
            email="teacher@alpha.talentra.id",
        )
        class_a = ClassModel(
            id=class_a_id,
            school_id=school_a_id,
            name="X RPL 1",
            grade_level="10",
            academic_year="2025/2026",
            status="active",
        )

        ident_admin_a = AuthIdentityModel(
            id="idn_adm_a",
            user_id=admin_a_id,
            identifier_type="NPSN",
            identifier_lookup_hash="hash_npsn_alpha",
            identifier_last4="1234",
            password_hash=hash_password("PasswordAdmin123!"),
            active=True,
        )
        ident_student_a = AuthIdentityModel(
            id="idn_std_a",
            user_id=student_a_id,
            identifier_type="NISN",
            identifier_lookup_hash=compute_identifier_lookup_hash("0071234321"),
            identifier_last4="4321",
            password_hash=hash_password("PasswordSiswa123!"),
            active=True,
        )

        session.add_all([
            school_a, school_b,
            admin_a, admin_b, student_a, teacher_a, class_a,
            ident_admin_a, ident_student_a,
        ])
        await session.commit()

    return engine, session_factory, {
        "school_a_id": school_a_id,
        "school_b_id": school_b_id,
        "admin_a_id": admin_a_id,
        "admin_b_id": admin_b_id,
        "student_a_id": student_a_id,
        "teacher_a_id": teacher_a_id,
        "class_a_id": class_a_id,
    }


def make_auth_cookies(user_id: str, school_id: str, role: UserRole):
    sid = str(uuid.uuid4())
    token, _ = create_access_token(user_id=user_id, school_id=school_id, role=role, session_id=sid)
    return sid, token


@pytest.mark.asyncio
async def test_admin_rbac_and_cross_tenant_isolation(tmp_path):
    engine, session_factory, ids = await setup_admin_test_db(tmp_path)
    try:
        ident_repo = PostgresIdentityRepository(session_factory=session_factory)
        sess_repo = PostgresSessionRepository(session_factory=session_factory)
        audit_repo = PostgresAuditRepository(session_factory=session_factory)

        dependencies.set_identity_repo(ident_repo)
        dependencies.set_session_repo(sess_repo)
        dependencies.set_audit_repo(audit_repo)

        # 1. Admin A session
        sid_a, token_a = make_auth_cookies(ids["admin_a_id"], ids["school_a_id"], UserRole.ADMIN)
        await sess_repo.create_session(SessionRecord(
            session_id=sid_a, user_id=ids["admin_a_id"], school_id=ids["school_a_id"],
            role=UserRole.ADMIN, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        # 2. Student A session
        sid_s, token_s = make_auth_cookies(ids["student_a_id"], ids["school_a_id"], UserRole.STUDENT)
        await sess_repo.create_session(SessionRecord(
            session_id=sid_s, user_id=ids["student_a_id"], school_id=ids["school_a_id"],
            role=UserRole.STUDENT, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        # 3. Admin B session (different school)
        sid_b, token_b = make_auth_cookies(ids["admin_b_id"], ids["school_b_id"], UserRole.ADMIN)
        await sess_repo.create_session(SessionRecord(
            session_id=sid_b, user_id=ids["admin_b_id"], school_id=ids["school_b_id"],
            role=UserRole.ADMIN, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Anonymous -> 401
            res_anon = await client.get("/api/v1/admin/users")
            assert res_anon.status_code == 401

            # Student -> 403 Forbidden
            client.cookies.set("talentra_session", token_s)
            res_std = await client.get("/api/v1/admin/users")
            assert res_std.status_code == 403

            # Admin A -> 200 OK (own school)
            client.cookies.set("talentra_session", token_a)
            res_adm = await client.get("/api/v1/admin/users")
            assert res_adm.status_code == 200
            data = res_adm.json()
            assert "items" in data
            assert len(data["items"]) >= 1

            # Cross-tenant check: Admin B cannot access School A student details
            client.cookies.set("talentra_session", token_b)
            res_cross = await client.get(f"/api/v1/admin/users/{ids['student_a_id']}")
            assert res_cross.status_code == 404, "Cross-tenant breach: Admin B accessed School A user!"
    finally:
        dependencies.set_identity_repo(None)
        dependencies.set_session_repo(None)
        dependencies.set_audit_repo(None)
        await engine.dispose()


@pytest.mark.asyncio
async def test_student_creation_and_identifier_privacy(tmp_path):
    engine, session_factory, ids = await setup_admin_test_db(tmp_path)
    try:
        ident_repo = PostgresIdentityRepository(session_factory=session_factory)
        sess_repo = PostgresSessionRepository(session_factory=session_factory)
        audit_repo = PostgresAuditRepository(session_factory=session_factory)

        dependencies.set_identity_repo(ident_repo)
        dependencies.set_session_repo(sess_repo)
        dependencies.set_audit_repo(audit_repo)

        sid_a, token_a = make_auth_cookies(ids["admin_a_id"], ids["school_a_id"], UserRole.ADMIN)
        await sess_repo.create_session(SessionRecord(
            session_id=sid_a, user_id=ids["admin_a_id"], school_id=ids["school_a_id"],
            role=UserRole.ADMIN, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            client.cookies.set("talentra_session", token_a)

            # Get CSRF
            csrf_res = await client.get("/api/v1/auth/csrf")
            csrf_token = csrf_res.json()["csrfToken"]

            # 1. Create Student with leading zero NISN
            create_res = await client.post(
                "/api/v1/admin/users/students",
                headers={"X-CSRF-Token": csrf_token},
                json={
                    "displayName": "Citra Lestari",
                    "nisn": "0098765432",
                    "gradeLevel": "10",
                    "classId": ids["class_a_id"],
                },
            )
            assert create_res.status_code == 201
            res_data = create_res.json()
            assert res_data["displayName"] == "Citra Lestari"
            assert res_data["role"] == "student"
            assert "0098765432" not in res_data["maskedIdentifier"]
            assert res_data["maskedIdentifier"] == "NISN: ••••••5432"
            assert "temporaryPassword" in res_data
            temp_pwd = res_data["temporaryPassword"]
            assert len(temp_pwd) >= 12

            # 2. Check duplicate NISN rejection
            dup_res = await client.post(
                "/api/v1/admin/users/students",
                headers={"X-CSRF-Token": csrf_token},
                json={
                    "displayName": "Citra Duplicate",
                    "nisn": "0098765432",
                    "gradeLevel": "10",
                },
            )
            assert dup_res.status_code == 409
            assert dup_res.json()["error"]["code"] == "IDENTITY_ALREADY_EXISTS"

            # 3. Check list users: full NISN is NEVER returned
            list_res = await client.get("/api/v1/admin/users")
            assert list_res.status_code == 200
            items_str = str(list_res.json()).lower()
            assert "0098765432" not in items_str
    finally:
        dependencies.set_identity_repo(None)
        dependencies.set_session_repo(None)
        dependencies.set_audit_repo(None)
        await engine.dispose()


@pytest.mark.asyncio
async def test_teacher_creation_and_identifier_resolution(tmp_path):
    engine, session_factory, ids = await setup_admin_test_db(tmp_path)
    try:
        ident_repo = PostgresIdentityRepository(session_factory=session_factory)
        sess_repo = PostgresSessionRepository(session_factory=session_factory)
        audit_repo = PostgresAuditRepository(session_factory=session_factory)

        dependencies.set_identity_repo(ident_repo)
        dependencies.set_session_repo(sess_repo)
        dependencies.set_audit_repo(audit_repo)

        sid_a, token_a = make_auth_cookies(ids["admin_a_id"], ids["school_a_id"], UserRole.ADMIN)
        await sess_repo.create_session(SessionRecord(
            session_id=sid_a, user_id=ids["admin_a_id"], school_id=ids["school_a_id"],
            role=UserRole.ADMIN, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            client.cookies.set("talentra_session", token_a)
            csrf_res = await client.get("/api/v1/auth/csrf")
            csrf_token = csrf_res.json()["csrfToken"]

            # Create teacher with 16-digit NUPTK
            res_nuptk = await client.post(
                "/api/v1/admin/users/teachers",
                headers={"X-CSRF-Token": csrf_token},
                json={
                    "displayName": "Dewi Sartika, S.Pd.",
                    "identifier": "1234567890123456",
                    "title": "Guru Produktif RPL",
                },
            )
            assert res_nuptk.status_code == 201
            data = res_nuptk.json()
            assert data["role"] == "teacher"
            assert "NUPTK" in data["maskedIdentifier"]
            assert data["temporaryPassword"] is not None

            # Create teacher with 18-digit NIP
            res_nip = await client.post(
                "/api/v1/admin/users/teachers",
                headers={"X-CSRF-Token": csrf_token},
                json={
                    "displayName": "Hendra Wijaya, M.T.",
                    "identifier": "198001012005011005",
                    "title": "Kepala Program Keahlian",
                },
            )
            assert res_nip.status_code == 201
            data_nip = res_nip.json()
            assert "NIP" in data_nip["maskedIdentifier"]
    finally:
        dependencies.set_identity_repo(None)
        dependencies.set_session_repo(None)
        dependencies.set_audit_repo(None)
        await engine.dispose()


@pytest.mark.asyncio
async def test_disable_reactivate_and_session_revocation(tmp_path):
    engine, session_factory, ids = await setup_admin_test_db(tmp_path)
    try:
        ident_repo = PostgresIdentityRepository(session_factory=session_factory)
        sess_repo = PostgresSessionRepository(session_factory=session_factory)
        audit_repo = PostgresAuditRepository(session_factory=session_factory)

        dependencies.set_identity_repo(ident_repo)
        dependencies.set_session_repo(sess_repo)
        dependencies.set_audit_repo(audit_repo)

        # Admin A
        sid_a, token_a = make_auth_cookies(ids["admin_a_id"], ids["school_a_id"], UserRole.ADMIN)
        await sess_repo.create_session(SessionRecord(
            session_id=sid_a, user_id=ids["admin_a_id"], school_id=ids["school_a_id"],
            role=UserRole.ADMIN, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        # Student A
        sid_s, token_s = make_auth_cookies(ids["student_a_id"], ids["school_a_id"], UserRole.STUDENT)
        await sess_repo.create_session(SessionRecord(
            session_id=sid_s, user_id=ids["student_a_id"], school_id=ids["school_a_id"],
            role=UserRole.STUDENT, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 1. Student A can access /auth/me initially
            client.cookies.set("talentra_session", token_s)
            me_res = await client.get("/api/v1/auth/me")
            assert me_res.status_code == 200

            # 2. Admin A disables Student A
            client.cookies.set("talentra_session", token_a)
            csrf_res = await client.get("/api/v1/auth/csrf")
            csrf_token = csrf_res.json()["csrfToken"]

            dis_res = await client.post(
                f"/api/v1/admin/users/{ids['student_a_id']}/disable",
                headers={"X-CSRF-Token": csrf_token},
            )
            assert dis_res.status_code == 200

            # 3. Student A's active session is REVOKED -> 401 Unauthorized
            client.cookies.set("talentra_session", token_s)
            me_res2 = await client.get("/api/v1/auth/me")
            assert me_res2.status_code == 401

            # 4. Student A cannot login while disabled
            login_dis = await client.post(
                "/api/v1/auth/login",
                json={"identifier": "0071234321", "password": "PasswordSiswa123!"},
            )
            assert login_dis.status_code == 401

            # 5. Admin A reactivates Student A
            client.cookies.set("talentra_session", token_a)
            react_res = await client.post(
                f"/api/v1/admin/users/{ids['student_a_id']}/reactivate",
                headers={"X-CSRF-Token": csrf_token},
            )
            assert react_res.status_code == 200

            # Old session must STILL remain invalid
            client.cookies.set("talentra_session", token_s)
            me_res3 = await client.get("/api/v1/auth/me")
            assert me_res3.status_code == 401
    finally:
        dependencies.set_identity_repo(None)
        dependencies.set_session_repo(None)
        dependencies.set_audit_repo(None)
        await engine.dispose()


@pytest.mark.asyncio
async def test_admin_password_reset_and_must_change_password_gate(tmp_path):
    engine, session_factory, ids = await setup_admin_test_db(tmp_path)
    try:
        ident_repo = PostgresIdentityRepository(session_factory=session_factory)
        sess_repo = PostgresSessionRepository(session_factory=session_factory)
        audit_repo = PostgresAuditRepository(session_factory=session_factory)

        dependencies.set_identity_repo(ident_repo)
        dependencies.set_session_repo(sess_repo)
        dependencies.set_audit_repo(audit_repo)

        # Admin session
        sid_a, token_a = make_auth_cookies(ids["admin_a_id"], ids["school_a_id"], UserRole.ADMIN)
        await sess_repo.create_session(SessionRecord(
            session_id=sid_a, user_id=ids["admin_a_id"], school_id=ids["school_a_id"],
            role=UserRole.ADMIN, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        # Student session with existing password
        sid_s, token_s = make_auth_cookies(ids["student_a_id"], ids["school_a_id"], UserRole.STUDENT)
        await sess_repo.create_session(SessionRecord(
            session_id=sid_s, user_id=ids["student_a_id"], school_id=ids["school_a_id"],
            role=UserRole.STUDENT, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            client.cookies.set("talentra_session", token_a)
            csrf_res = await client.get("/api/v1/auth/csrf")
            csrf_token = csrf_res.json()["csrfToken"]

            # 1. Admin resets student password
            reset_res = await client.post(
                f"/api/v1/admin/users/{ids['student_a_id']}/reset-password",
                headers={"X-CSRF-Token": csrf_token},
            )
            assert reset_res.status_code == 200
            temp_pwd = reset_res.json()["temporaryPassword"]
            assert temp_pwd is not None

            # 2. Student old session is REVOKED
            client.cookies.set("talentra_session", token_s)
            me_res = await client.get("/api/v1/auth/me")
            assert me_res.status_code == 401

            # 3. Student logs in with TEMPORARY password
            login_res = await client.post(
                "/api/v1/auth/login",
                json={"identifier": "0071234321", "password": temp_pwd},
            )
            # In our synthetic db, let's verify login works with the updated hash
            assert login_res.status_code == 200

            # 4. must_change_password gate:
            # /api/v1/auth/me is ALLOWED
            me_res2 = await client.get("/api/v1/auth/me")
            assert me_res2.status_code == 200
            assert me_res2.json()["requiresCredentialUpdate"] is True

            # Other protected endpoint is BLOCKED with 403 AUTH_PASSWORD_CHANGE_REQUIRED
            skill_res = await client.get("/api/v1/student/skills")
            assert skill_res.status_code == 403
            assert skill_res.json()["error"]["code"] == "AUTH_PASSWORD_CHANGE_REQUIRED"

            # 5. Student changes password via /api/v1/auth/change-password
            csrf_token_student = login_res.cookies.get("talentra_csrf")
            change_res = await client.post(
                "/api/v1/auth/change-password",
                headers={"X-CSRF-Token": csrf_token_student},
                json={
                    "currentPassword": temp_pwd,
                    "newPassword": "BrandNewPermanentPassword2026!",
                },
            )
            assert change_res.status_code == 200

            # 6. Now normal endpoints are UNBLOCKED!
            skill_res2 = await client.get("/api/v1/student/skills")
            assert skill_res2.status_code == 200
    finally:
        dependencies.set_identity_repo(None)
        dependencies.set_session_repo(None)
        dependencies.set_audit_repo(None)
        await engine.dispose()
