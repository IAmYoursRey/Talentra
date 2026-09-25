import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import create_access_token
from app.domain.enums import UserRole


async def get_authenticated_client(role: str) -> AsyncClient:
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")

    identifiers = {
        "student": ("0071234321", "PasswordSiswa123!"),
        "teacher": ("198204152005011789", "PasswordGuru123!"),
        "admin": ("20101543", "PasswordAdmin123!"),
    }
    ident, pwd = identifiers[role]
    res = await client.post("/api/v1/auth/login", json={"identifier": ident, "password": pwd})
    assert res.status_code == 200
    return client


@pytest.mark.asyncio
async def test_rbac_matrix_student():
    client = await get_authenticated_client("student")
    try:
        # Student -> Student (ALLOW)
        res_s = await client.get("/api/v1/protected/student")
        assert res_s.status_code == 200
        assert res_s.json()["status"] == "authorized"

        # Student -> Teacher (DENY 403)
        res_t = await client.get("/api/v1/protected/teacher")
        assert res_t.status_code == 403

        # Student -> Admin (DENY 403)
        res_a = await client.get("/api/v1/protected/admin")
        assert res_a.status_code == 403
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_rbac_matrix_teacher():
    client = await get_authenticated_client("teacher")
    try:
        # Teacher -> Student (DENY 403)
        res_s = await client.get("/api/v1/protected/student")
        assert res_s.status_code == 403

        # Teacher -> Teacher (ALLOW 200)
        res_t = await client.get("/api/v1/protected/teacher")
        assert res_t.status_code == 200

        # Teacher -> Admin (DENY 403)
        res_a = await client.get("/api/v1/protected/admin")
        assert res_a.status_code == 403
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_rbac_matrix_admin():
    client = await get_authenticated_client("admin")
    try:
        # Admin -> Student (DENY 403 - School Admin is not a student)
        res_s = await client.get("/api/v1/protected/student")
        assert res_s.status_code == 403

        # Admin -> Teacher (DENY 403 - School Admin is not a teacher validator)
        res_t = await client.get("/api/v1/protected/teacher")
        assert res_t.status_code == 403

        # Admin -> Admin (ALLOW 200)
        res_a = await client.get("/api/v1/protected/admin")
        assert res_a.status_code == 200
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_rbac_matrix_anonymous():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Anonymous -> All protected endpoints must return 401
        res_s = await client.get("/api/v1/protected/student")
        assert res_s.status_code == 401

        res_t = await client.get("/api/v1/protected/teacher")
        assert res_t.status_code == 401

        res_a = await client.get("/api/v1/protected/admin")
        assert res_a.status_code == 401


@pytest.mark.asyncio
async def test_privilege_escalation_attacks():
    # Attack A: Student client passes ?role=admin in query param
    client = await get_authenticated_client("student")
    try:
        res = await client.get("/api/v1/protected/admin?role=admin")
        assert res.status_code == 403

        # Attack B: Student client sends custom header claiming admin
        res_hdr = await client.get(
            "/api/v1/protected/admin",
            headers={"X-User-Role": "admin", "X-Role": "admin"},
        )
        assert res_hdr.status_code == 403
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_forged_jwt_token_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Create a valid token with student role, then tamper payload to admin
        token, _ = create_access_token(
            user_id="11111111-1111-1111-1111-111111111111",
            school_id="99999999-9999-9999-9999-999999999999",
            role=UserRole.STUDENT,
            session_id="valid-session-id",
        )

        # Alter the token payload (middle segment)
        parts = token.split(".")
        # Tamper payload
        tampered_token = f"{parts[0]}.eyJzdWIiOiIxMTExMTExMS0xMTExLTExMTEtMTExMS0xMTExMTExMTExMTEiLCJyb2xlIjoiYWRtaW4ifQ.{parts[2]}"

        client.cookies.set("talentra_session", tampered_token)
        res = await client.get("/api/v1/protected/admin")
        assert res.status_code == 401
