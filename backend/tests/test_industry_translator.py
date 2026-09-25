import pytest
import uuid
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.api.v1.student_portfolio import set_translator_service
from app.repositories.portfolio import InMemoryPortfolioRepository
from app.services.industry_translator import (
    IndustryTranslatorService,
    DeterministicIndustryTranslator,
    FactualityGuard,
    TRANSLATOR_VERSION,
)


@pytest.fixture
def translator_setup():
    portfolio_repo = InMemoryPortfolioRepository()
    service = IndustryTranslatorService(portfolio_repo=portfolio_repo)
    set_translator_service(service)

    yield {
        "portfolio_repo": portfolio_repo,
        "service": service,
    }

    set_translator_service(None)


async def get_authenticated_client(identifier: str, password: str = "PasswordSiswa123!") -> AsyncClient:
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    res = await client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})
    assert res.status_code == 200
    return client


# --- 1. Factuality Guard Invariants ---

def test_factuality_guard_detects_invented_numbers():
    source = "Membuat website perpustakaan untuk tugas sekolah bersama 3 teman."
    # Case A: Preserves original number 3 -> Valid
    valid_text = "Mengembangkan situs web perpustakaan bersama 3 rekan sekolah dalam kolaborasi terstruktur."
    ok, msg = FactualityGuard.verify(source, valid_text, ["web-development"])
    assert ok is True

    # Case B: Invents 40% efficiency -> Invalid
    invalid_text_1 = "Mengembangkan website perpustakaan dan meningkatkan efisiensi 40%."
    ok, msg = FactualityGuard.verify(source, invalid_text_1, ["web-development"])
    assert ok is False
    assert "40%" in msg

    # Case C: Invents 5000 users -> Invalid
    invalid_text_2 = "Mengembangkan website perpustakaan yang digunakan oleh 5000 siswa."
    ok, msg = FactualityGuard.verify(source, invalid_text_2, ["web-development"])
    assert ok is False


def test_factuality_guard_detects_ungrounded_technologies():
    source = "Membuat aplikasi kalkulator sederhana dengan HTML dan CSS."
    # Case A: Mentions React which is not in source or tags -> Invalid
    invalid_text = "Mengembangkan aplikasi kalkulator menggunakan framework React dan modern UI."
    ok, msg = FactualityGuard.verify(source, invalid_text, ["problem-solving"])
    assert ok is False
    assert "react" in msg.lower()

    # Case B: If react IS in approved canonical tags -> Valid
    ok, msg = FactualityGuard.verify(source, invalid_text, ["problem-solving", "react"])
    assert ok is True


def test_factuality_guard_detects_unsupported_leadership_claim():
    source = "Membantu teman-teman merapikan data inventaris lab komputer."
    # Invents leadership claim without leadership tag -> Invalid
    invalid_text = "Memimpin tim perapian inventaris laboratorium komputer sekolah."
    ok, msg = FactualityGuard.verify(source, invalid_text, ["collaboration"])
    assert ok is False
    assert "leadership" in msg.lower()

    # Valid if leadership tag is present
    ok, msg = FactualityGuard.verify(source, invalid_text, ["collaboration", "leadership"])
    assert ok is True


# --- 2. Service Strict Status Gate & Ownership ---

@pytest.mark.asyncio
async def test_translator_status_gating_approved_only(translator_setup):
    """
    Only approved portfolios can be translated into professional descriptions.
    Draft, submitted, revision_requested, and rejected must fail fast.
    """
    repo: InMemoryPortfolioRepository = translator_setup["portfolio_repo"]
    svc: IndustryTranslatorService = translator_setup["service"]
    school_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    now = datetime.now(timezone.utc)

    # 1. Draft
    draft_id = "p_draft"
    await repo.save_portfolio({
        "school_id": school_id,
        "student_id": student_id,
        "portfolio_id": draft_id,
        "title": "Draf Karya",
        "description": "Deskripsi draf",
        "status": "draft",
        "canonical_tag_ids": ["web-development"],
        "created_at": now,
        "updated_at": now,
    })
    with pytest.raises(ValueError, match="hanya dapat dilakukan pada karya yang telah disetujui guru"):
        await svc.get_or_create_professional_description(school_id, student_id, draft_id)

    # 2. Submitted
    sub_id = "p_submitted"
    await repo.save_portfolio({
        "school_id": school_id,
        "student_id": student_id,
        "portfolio_id": sub_id,
        "title": "Karya Menunggu Validasi",
        "description": "Deskripsi menunggu",
        "status": "submitted",
        "canonical_tag_ids": ["web-development"],
        "created_at": now,
        "updated_at": now,
    })
    with pytest.raises(ValueError, match="hanya dapat dilakukan pada karya yang telah disetujui guru"):
        await svc.get_or_create_professional_description(school_id, student_id, sub_id)

    # 3. Rejected
    rej_id = "p_rejected"
    await repo.save_portfolio({
        "school_id": school_id,
        "student_id": student_id,
        "portfolio_id": rej_id,
        "title": "Karya Ditolak",
        "description": "Deskripsi ditolak",
        "status": "rejected",
        "canonical_tag_ids": ["web-development"],
        "created_at": now,
        "updated_at": now,
    })
    with pytest.raises(ValueError, match="hanya dapat dilakukan pada karya yang telah disetujui guru"):
        await svc.get_or_create_professional_description(school_id, student_id, rej_id)

    # 4. Approved -> Works successfully!
    app_id = "p_approved"
    await repo.save_portfolio({
        "school_id": school_id,
        "student_id": student_id,
        "portfolio_id": app_id,
        "title": "Website Profil Sekolah",
        "description": "Membuat website profil sekolah bersama 2 teman",
        "status": "approved",
        "canonical_tag_ids": ["web-development", "collaboration"],
        "created_at": now,
        "updated_at": now,
    })
    res = await svc.get_or_create_professional_description(school_id, student_id, app_id)
    assert res["portfolioId"] == app_id
    assert res["mode"] == "deterministic"
    assert "Mengembangkan" in res["professionalText"]
    assert res["translatorVersion"] == TRANSLATOR_VERSION


@pytest.mark.asyncio
async def test_translator_preserves_immutable_source(translator_setup):
    """
    Translating description does NOT mutate the original portfolio item or revision.
    It writes to a derived document collection.
    """
    repo: InMemoryPortfolioRepository = translator_setup["portfolio_repo"]
    svc: IndustryTranslatorService = translator_setup["service"]
    school_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    now = datetime.now(timezone.utc)
    app_id = "p_immutable_check"
    original_desc = "Bikin game tebak angka pakai python sederhana."
    await repo.save_portfolio({
        "school_id": school_id,
        "student_id": student_id,
        "portfolio_id": app_id,
        "title": "Game Python",
        "description": original_desc,
        "status": "approved",
        "canonical_tag_ids": ["problem-solving"],
        "created_at": now,
        "updated_at": now,
    })

    await svc.get_or_create_professional_description(school_id, student_id, app_id)

    # Verify original portfolio remains 100% unchanged
    item = await repo.get_portfolio(school_id, student_id, app_id)
    assert item["description"] == original_desc


# --- 3. HTTP API Endpoints ---

@pytest.mark.asyncio
async def test_translator_api_endpoints(translator_setup):
    """
    Tests POST and GET endpoints for professional descriptions.
    """
    repo: InMemoryPortfolioRepository = translator_setup["portfolio_repo"]
    student_client = await get_authenticated_client("0071234321", "PasswordSiswa123!")

    # Student info from login: user id
    me_res = await student_client.get("/api/v1/auth/me")
    assert me_res.status_code == 200
    user_info = me_res.json()
    student_id = user_info["id"]
    school_id = user_info["school"]["id"]

    # Seed an approved portfolio for this student
    now = datetime.now(timezone.utc)
    p_id = "p_api_test"
    await repo.save_portfolio({
        "school_id": school_id,
        "student_id": student_id,
        "portfolio_id": p_id,
        "title": "Aplikasi Catatan Kas Kelas",
        "description": "Mengerjakan sistem pencatatan keuangan kelas sederhana.",
        "status": "approved",
        "canonical_tag_ids": ["digital-literacy", "problem-solving"],
        "created_at": now,
        "updated_at": now,
    })

    # POST to generate
    post_res = await student_client.post(f"/api/v1/student/portfolio/{p_id}/professional-description")
    assert post_res.status_code == 200
    post_data = post_res.json()
    assert post_data["portfolioId"] == p_id
    assert "professionalText" in post_data
    assert "Mengimplementasikan" in post_data["professionalText"]
    assert "Cache-Control" in post_res.headers
    assert "private" in post_res.headers["Cache-Control"]

    # GET to fetch saved snapshot
    get_res = await student_client.get(f"/api/v1/student/portfolio/{p_id}/professional-description")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["documentId"] == post_data["documentId"]
    assert get_data["professionalText"] == post_data["professionalText"]
