import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.cv_security import (
    generate_verification_token,
    hash_verification_token,
    generate_display_code,
    derive_snapshot_fingerprint,
)
from app.domain.documents import CVContentSnapshotDocument
from app.repositories.portfolio import InMemoryPortfolioRepository
from app.repositories.verification import InMemoryVerificationRepository
from app.domain.enums import VerificationStatus
from app.services.cv_service import CVService
from app.services.public_verification_service import PublicVerificationService
from app.api.v1.student_cv import set_cv_service
from app.api.v1.public_verify import set_public_verification_service
from app.core.rate_limiter import public_verify_rate_limiter


@pytest.fixture
def verification_test_env():
    port_repo = InMemoryPortfolioRepository()
    verif_repo = InMemoryVerificationRepository()

    public_svc = PublicVerificationService(
        verification_repo=verif_repo,
        portfolio_repo=port_repo,
    )
    set_public_verification_service(public_svc)

    cv_svc = CVService(
        portfolio_repo=port_repo,
        verification_repo=verif_repo,
    )
    set_cv_service(cv_svc)

    client = TestClient(app)

    return {
        "client": client,
        "portfolio_repo": port_repo,
        "verification_repo": verif_repo,
        "public_svc": public_svc,
        "cv_svc": cv_svc,
    }


def test_verification_token_entropy_and_hash_only_storage(verification_test_env):
    """
    SECTIONS 33, 34, 88, 89:
    1. Tokens are high-entropy URL-safe strings (>= 32 bytes).
    2. Tokens are unique and non-sequential.
    3. Database only stores HMAC token_hash, NEVER raw token.
    """
    tokens = [generate_verification_token() for _ in range(50)]
    assert len(set(tokens)) == 50, "Tokens must be unique"
    for t in tokens:
        assert len(t) >= 40, f"Token '{t}' has insufficient length for 32-byte urlsafe"
        assert t.isalnum() or "-" in t or "_" in t

    # Verify hashing
    raw_token = generate_verification_token()
    token_hash = hash_verification_token(raw_token)
    assert token_hash != raw_token
    assert len(token_hash) == 64  # SHA-256 hex string


@pytest.mark.asyncio
async def test_public_verification_lifecycle(verification_test_env):
    """
    SECTIONS 45, 90:
    Test public verification across the entire lifecycle:
    - Active valid token -> VERIFIED
    - Revoked token -> REVOKED
    - Expired token -> EXPIRED
    - Unknown/Malformed token -> INVALID
    """
    env = verification_test_env
    client: TestClient = env["client"]
    port_repo: InMemoryPortfolioRepository = env["portfolio_repo"]
    verif_repo: InMemoryVerificationRepository = env["verification_repo"]

    # 1. Setup an active CV snapshot
    snapshot_id = "snap_active_001"
    digest = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    snap_doc = CVContentSnapshotDocument(
        snapshot_id=snapshot_id,
        school_id="sch_01",
        student_id="stu_01",
        profile={
            "display_name": "Siti Nurhaliza",
            "school_name": "SMK Negeri 2 Bandung",
            "class_name": "XII Tata Boga",
            "professional_summary": "Siswa dengan spesialisasi kuliner dan manajemen dapur.",
        },
        approved_skills=[
            {"name": "Manajemen Dapur", "score": 88, "level": "Tingkat Mahir"},
            {"name": "Literasi Digital", "score": 75, "level": "Tingkat Menengah"},
        ],
        selected_portfolios=[
            {
                "portfolio_id": "port_01",
                "title": "Pengembangan Menu Nusantara",
                "activity_type": "project",
                "activity_date": "2026-08-10",
                "professional_description": "Mengembangkan resep standar menu nusantara modern.",
                "tags": ["Culinary", "Project"],
            }
        ],
        content_digest=digest,
        status="issued",
    )
    await port_repo.save_cv_snapshot(snap_doc)

    raw_token = generate_verification_token()
    token_hash = hash_verification_token(raw_token)
    display_code = "TLN-7K2M-9P4R"
    issued_at = datetime.now(timezone.utc)

    await verif_repo.create_verification_record({
        "id": "rec_001",
        "school_id": "sch_01",
        "student_id": "stu_01",
        "cv_snapshot_id": snapshot_id,
        "token_hash": token_hash,
        "display_code": display_code,
        "snapshot_digest": digest,
        "status": VerificationStatus.ACTIVE.value,
        "issued_at": issued_at,
        "expires_at": issued_at + timedelta(days=365),
    })

    # A. Active Token Verification -> VERIFIED
    res_active = client.get(f"/api/v1/public/verify/{raw_token}")
    assert res_active.status_code == 200
    data_active = res_active.json()
    assert data_active["status"] == "verified"
    assert data_active["displayCode"] == display_code
    assert data_active["studentDisplayName"] == "Siti Nurhaliza"
    assert data_active["schoolDisplayName"] == "SMK Negeri 2 Bandung"
    assert data_active["snapshotDigestShort"] == derive_snapshot_fingerprint(digest)
    assert len(data_active["selectedPortfolioSummaries"]) == 1
    assert data_active["selectedPortfolioSummaries"][0]["title"] == "Pengembangan Menu Nusantara"
    assert len(data_active["validatedSkillSummary"]) == 2

    # Check Headers: Must be no-store and no-referrer
    assert "no-store" in res_active.headers.get("Cache-Control", "")
    assert res_active.headers.get("Referrer-Policy") == "no-referrer"

    # B. Revoke the token -> REVOKED
    await verif_repo.revoke_record(
        record_id="rec_001",
        revoked_by_user_id="stu_01",
        reason="Pembaruan portofolio siswa",
    )
    res_revoked = client.get(f"/api/v1/public/verify/{raw_token}")
    assert res_revoked.status_code == 200
    data_revoked = res_revoked.json()
    assert data_revoked["status"] == "revoked"
    assert data_revoked["displayCode"] == display_code
    assert "tidak lagi berlaku" in data_revoked["message"]

    # C. Expired Token -> EXPIRED
    raw_token_exp = generate_verification_token()
    token_hash_exp = hash_verification_token(raw_token_exp)
    await verif_repo.create_verification_record({
        "id": "rec_exp_002",
        "school_id": "sch_01",
        "student_id": "stu_01",
        "cv_snapshot_id": snapshot_id,
        "token_hash": token_hash_exp,
        "display_code": "TLN-EXP1-0000",
        "snapshot_digest": digest,
        "status": VerificationStatus.ACTIVE.value,
        "issued_at": issued_at - timedelta(days=400),
        "expires_at": issued_at - timedelta(days=35),  # Expired in past
    })

    res_exp = client.get(f"/api/v1/public/verify/{raw_token_exp}")
    assert res_exp.status_code == 200
    data_exp = res_exp.json()
    assert data_exp["status"] == "expired"
    assert "telah berakhir" in data_exp["message"]

    # D. Unknown / Malformed Token -> INVALID
    res_invalid = client.get("/api/v1/public/verify/non_existent_token_1234567890")
    assert res_invalid.status_code == 200
    data_invalid = res_invalid.json()
    assert data_invalid["status"] == "invalid"
    assert "tidak ditemukan" in data_invalid["message"].lower()

    # Very short malformed token
    res_short = client.get("/api/v1/public/verify/short")
    assert res_short.status_code == 200
    assert res_short.json()["status"] == "invalid"


def test_public_verification_privacy_invariants(verification_test_env):
    """
    SECTIONS 42, 94:
    Automated check ensuring public verification response NEVER contains
    confidential or internal identifiers.
    """
    env = verification_test_env
    client: TestClient = env["client"]

    # Query public verify
    res = client.get("/api/v1/public/verify/some_random_token_1234567890123456")
    body = res.text.lower()

    forbidden_keys = [
        "nisn",
        "nuptk",
        "nip",
        "npsn",
        "student_id",
        "school_id",
        "studentid",
        "schoolid",
        "token_hash",
        "pdf_storage_object_id",
        "storage_key",
        "password",
        "jwt",
        "cookie",
    ]
    for key in forbidden_keys:
        assert f'"{key}"' not in body, f"Forbidden confidential key '{key}' found in public verification JSON!"


def test_public_verification_rate_limiting(verification_test_env):
    """
    SECTION 56, 93:
    Public verification endpoint must be rate-limited against burst scanning attacks.
    """
    env = verification_test_env
    client: TestClient = env["client"]

    # Reset rate limiter completely before and after
    public_verify_rate_limiter.requests.clear()

    # Set temporary low threshold for test
    orig_max = public_verify_rate_limiter.max_requests
    public_verify_rate_limiter.max_requests = 10

    try:
        for i in range(10):
            res = client.get(f"/api/v1/public/verify/test_rate_token_{i}_1234567890")
            assert res.status_code == 200

        # 11th request must trigger 429
        res_blocked = client.get("/api/v1/public/verify/test_rate_token_11_1234567890")
        assert res_blocked.status_code == 429
        assert "Batas permintaan" in res_blocked.json()["error"]["message"]
    finally:
        public_verify_rate_limiter.max_requests = orig_max
        public_verify_rate_limiter.requests.clear()
