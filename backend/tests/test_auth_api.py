import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.core.rate_limiter import login_rate_limiter
from app.repositories.in_memory import InMemoryIdentityRepository, InMemorySessionRepository


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    login_rate_limiter.attempts.clear()


@pytest.mark.asyncio
async def test_student_login_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.post(
            "/api/v1/auth/login",
            json={
                "identifier": "0071234321",
                "password": "PasswordSiswa123!",
            },
        )
        assert res.status_code == 200
        data = res.json()

        # Check canonical redirect and role
        assert data["redirectTo"] == "/student"
        assert data["user"]["role"] == "student"
        assert data["user"]["displayName"] == "Alya Rahma Azzahra"
        assert data["user"]["school"]["name"] == "SMA Negeri 1 Teladan Jakarta"

        # Check raw token is NOT in response JSON
        assert "token" not in data
        assert "accessToken" not in data
        assert "jwt" not in data

        # Check cookies
        cookies = res.cookies
        assert "talentra_session" in cookies
        assert "talentra_csrf" in cookies

        # Check Set-Cookie headers
        set_cookie_headers = res.headers.get_list("set-cookie")
        session_cookie_header = next((h for h in set_cookie_headers if "talentra_session=" in h), "")
        assert "HttpOnly" in session_cookie_header or "httponly" in session_cookie_header.lower()
        assert "Path=/" in session_cookie_header or "path=/" in session_cookie_header.lower()


@pytest.mark.asyncio
async def test_teacher_login_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.post(
            "/api/v1/auth/login",
            json={
                "identifier": "198204152005011789",
                "password": "PasswordGuru123!",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["redirectTo"] == "/teacher"
        assert data["user"]["role"] == "teacher"
        assert data["user"]["displayName"] == "Budi Santoso, S.Kom., M.Kom."


@pytest.mark.asyncio
async def test_admin_login_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.post(
            "/api/v1/auth/login",
            json={
                "identifier": "20101543",
                "password": "PasswordAdmin123!",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["redirectTo"] == "/admin"
        assert data["user"]["role"] == "admin"
        assert data["user"]["displayName"] == "Dra. Hj. Ratna Juwita, M.Pd."


@pytest.mark.asyncio
async def test_raihan_admin_email_login_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.post(
            "/api/v1/auth/login",
            json={
                "identifier": "raihanansari6678@gmail.com",
                "password": "raihanansari6678@gmail.com",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["redirectTo"] == "/admin"
        assert data["user"]["role"] == "admin"
        assert data["user"]["displayName"] == "Admin Demo"
        assert data["user"]["email"] == "raihanansari6678@gmail.com"
        assert "talentra_session" in res.cookies


@pytest.mark.asyncio
async def test_unknown_identifier_generic_failure():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.post(
            "/api/v1/auth/login",
            json={
                "identifier": "9999999999",  # Valid 10-digit NISN format but non-existent
                "password": "anypassword",
            },
        )
        assert res.status_code == 401
        data = res.json()
        assert data["error"]["code"] == "AUTH_INVALID_CREDENTIALS"
        # Must NOT leak that user was not found
        assert "tidak terdaftar" not in data["error"]["message"].lower()
        assert data["error"]["message"] == "ID pengguna atau kata sandi tidak sesuai."


@pytest.mark.asyncio
async def test_wrong_password_exact_same_generic_failure():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.post(
            "/api/v1/auth/login",
            json={
                "identifier": "0071234321",
                "password": "wrong-password-here!",
            },
        )
        assert res.status_code == 401
        data = res.json()
        assert data["error"]["code"] == "AUTH_INVALID_CREDENTIALS"
        assert data["error"]["message"] == "ID pengguna atau kata sandi tidak sesuai."


@pytest.mark.asyncio
async def test_disabled_account_failure():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.post(
            "/api/v1/auth/login",
            json={
                "identifier": "0089999884",
                "password": "PasswordSiswa123!",
            },
        )
        assert res.status_code in (401, 403)
        data = res.json()
        assert data["error"]["code"] in ("AUTH_ACCOUNT_DISABLED", "AUTH_INVALID_CREDENTIALS")


@pytest.mark.asyncio
async def test_rate_limiting_triggers_after_threshold():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Trigger 5 failed attempts
        for _ in range(5):
            await client.post(
                "/api/v1/auth/login",
                json={
                    "identifier": "0071234321",
                    "password": "wrong-password",
                },
            )

        # 6th attempt should be rate limited
        res = await client.post(
            "/api/v1/auth/login",
            json={
                "identifier": "0071234321",
                "password": "PasswordSiswa123!",
            },
        )
        assert res.status_code == 429
        data = res.json()
        assert data["error"]["code"] == "AUTH_RATE_LIMITED"


@pytest.mark.asyncio
async def test_auth_me_and_logout_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Login as teacher
        login_res = await client.post(
            "/api/v1/auth/login",
            json={
                "identifier": "198204152005011789",
                "password": "PasswordGuru123!",
            },
        )
        assert login_res.status_code == 200

        # 2. Call /auth/me with cookies
        me_res = await client.get("/api/v1/auth/me")
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["role"] == "teacher"
        assert me_data["displayName"] == "Budi Santoso, S.Kom., M.Kom."

        # Verify no sensitive password/hash returned
        assert "password" not in str(me_data).lower()
        assert "hash" not in str(me_data).lower()

        # 3. Call /auth/logout with CSRF token
        csrf_token = login_res.cookies.get("talentra_csrf")
        assert csrf_token is not None

        # Verify that calling logout without CSRF header is rejected with 403
        no_csrf_res = await client.post("/api/v1/auth/logout")
        assert no_csrf_res.status_code == 403
        assert no_csrf_res.json()["error"]["code"] == "CSRF_INVALID"

        # Verify that calling logout with valid CSRF succeeds
        logout_res = await client.post(
            "/api/v1/auth/logout",
            headers={"X-CSRF-Token": csrf_token},
        )
        assert logout_res.status_code == 200
        assert logout_res.json()["success"] is True

        # 4. Subsequent /auth/me should fail with 401
        after_logout_res = await client.get("/api/v1/auth/me")
        assert after_logout_res.status_code == 401


@pytest.mark.asyncio
async def test_demo_auth_endpoint_development_vs_production():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Development mode demo login
        res = await client.post(
            "/api/v1/auth/demo-login",
            json={"role": "student"},
        )
        assert res.status_code == 200
        assert res.json()["user"]["role"] == "student"

    # Simulate production mode where demo auth is forbidden
    original_env = settings.app_env
    original_enable = settings.enable_demo_auth
    try:
        settings.app_env = "production"
        settings.enable_demo_auth = False
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            res_prod = await client.post(
                "/api/v1/auth/demo-login",
                json={"role": "student"},
            )
            assert res_prod.status_code in (403, 404)
    finally:
        settings.app_env = original_env
        settings.enable_demo_auth = original_enable



def test_in_memory_repository_fails_in_production():
    original_env = settings.app_env
    try:
        settings.app_env = "production"
        with pytest.raises(RuntimeError, match="CRITICAL"):
            InMemoryIdentityRepository()
        with pytest.raises(RuntimeError, match="CRITICAL"):
            InMemorySessionRepository()
    finally:
        settings.app_env = original_env
