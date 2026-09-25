import pytest
import io
import uuid
import asyncio
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.portfolio_service import PortfolioService
from app.services.teacher_review_service import TeacherReviewService
from app.services.projection_service import StudentSkillProjectionService
from app.api.v1.student_portfolio import set_portfolio_service
from app.api.v1.teacher_reviews import set_teacher_review_service
from app.api.v1.student_skills import set_projection_service
from app.repositories.portfolio import InMemoryPortfolioRepository
from app.repositories.validation import TeacherValidationRepository
from app.repositories.storage_metadata import StorageMetadataRepository
from app.repositories.skill_tag import SkillTagRepository
from app.storage.local import LocalObjectStorage
from app.db.models import (
    UserModel,
    SchoolModel,
    ClassModel,
    EnrollmentModel,
    TeacherAssignmentModel,
    ValidationDecisionModel,
)
from app.core.database import AsyncSessionLocal


@pytest.fixture(autouse=True)
def setup_services(tmp_path):
    storage_dir = tmp_path / "test_storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    local_storage = LocalObjectStorage(base_directory=str(storage_dir))

    portfolio_repo = InMemoryPortfolioRepository()
    validation_repo = TeacherValidationRepository()
    storage_meta_repo = StorageMetadataRepository()
    skill_tag_repo = SkillTagRepository()

    proj_service = StudentSkillProjectionService(
        portfolio_repo=portfolio_repo,
        validation_repo=validation_repo,
        skill_tag_repo=skill_tag_repo,
    )

    port_service = PortfolioService(
        portfolio_repo=portfolio_repo,
        storage_meta_repo=storage_meta_repo,
        skill_tag_repo=skill_tag_repo,
        object_storage=local_storage,
        validation_repo=validation_repo,
    )

    teach_service = TeacherReviewService(
        portfolio_repo=portfolio_repo,
        validation_repo=validation_repo,
        storage_meta_repo=storage_meta_repo,
        object_storage=local_storage,
        projection_service=proj_service,
    )

    set_portfolio_service(port_service)
    set_teacher_review_service(teach_service)
    set_projection_service(proj_service)

    yield {
        "portfolio_service": port_service,
        "teacher_service": teach_service,
        "projection_service": proj_service,
        "portfolio_repo": portfolio_repo,
        "validation_repo": validation_repo,
    }

    set_portfolio_service(None)
    set_teacher_review_service(None)
    set_projection_service(None)


async def get_authenticated_client(identifier: str, password: str) -> AsyncClient:
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    res = await client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})
    assert res.status_code == 200, f"Login failed for {identifier}: {res.text}"
    return client


# --- 1. Teacher Scope Authorization & Queue Scoping ---

@pytest.mark.asyncio
async def test_teacher_scope_authorization_and_queue():
    # Student Alya submits portfolio
    client_student = await get_authenticated_client("0071234321", "PasswordSiswa123!")
    create_payload = {
        "title": "Aplikasi Web Monitoring Presensi Siswa",
        "activityType": "project",
        "activityDate": "2026-08-20",
        "description": "Pengembangan web presensi modern dengan Next.js dan TailwindCSS.",
        "canonicalTagIds": ["web-development", "digital-literacy", "problem-solving"],
        "evidence": {
            "type": "external_link",
            "url": "https://github.com/alya-student/presensi-app",
            "label": "Source Code",
        },
    }
    res_create = await client_student.post("/api/v1/student/portfolio", json=create_payload)
    assert res_create.status_code == 201
    portfolio_id = res_create.json()["portfolio_id"]

    # Submit portfolio
    res_sub = await client_student.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
    assert res_sub.status_code == 200
    rev_id = res_sub.json()["current_revision_id"]

    # 1. Assigned Teacher (Pak Budi - XII RPL 1) -> CAN SEE in Queue
    client_teacher = await get_authenticated_client("198204152005011789", "PasswordGuru123!")
    res_queue = await client_teacher.get("/api/v1/teacher/reviews")
    assert res_queue.status_code == 200
    queue_data = res_queue.json()
    assert queue_data["total"] >= 1
    item = next((i for i in queue_data["items"] if i["portfolioId"] == portfolio_id), None)
    assert item is not None
    assert item["studentDisplayName"] == "Alya Rahma Azzahra"
    assert item["classDisplayName"] == "XII RPL 1"
    # MANDATORY PRIVACY: NISN is NEVER present in queue response
    assert "nisn" not in str(res_queue.text).lower()

    # 2. Assigned Teacher can view detail
    res_detail = await client_teacher.get(f"/api/v1/teacher/reviews/{portfolio_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["revision"]["revisionId"] == rev_id
    assert "nisn" not in str(res_detail.text).lower()

    # 3. Student role cannot access teacher reviews -> 403 Forbidden
    res_std_attempt = await client_student.get("/api/v1/teacher/reviews")
    assert res_std_attempt.status_code == 403

    # 4. Admin role cannot validate portfolio -> 403 Forbidden
    client_admin = await get_authenticated_client("20101543", "PasswordAdmin123!")
    res_adm_attempt = await client_admin.get("/api/v1/teacher/reviews")
    assert res_adm_attempt.status_code == 403
    res_adm_dec = await client_admin.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json={"revisionId": rev_id, "action": "approved", "rubric": {"initiative": 4, "collaboration": 4, "communication": 4, "responsibility": 4, "resilience": 4}},
    )
    assert res_adm_dec.status_code == 403

    # 5. Anonymous cannot access -> 401 Unauthorized
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as anon_client:
        res_anon = await anon_client.get("/api/v1/teacher/reviews")
        assert res_anon.status_code == 401

    # 6. Unassigned teacher in same school cannot see in queue, cannot view detail, cannot decide
    client_unassigned = await get_authenticated_client("198501012010011001", "PasswordGuru123!")
    res_unassigned_q = await client_unassigned.get("/api/v1/teacher/reviews")
    assert res_unassigned_q.status_code == 200
    assert not any(i["portfolioId"] == portfolio_id for i in res_unassigned_q.json()["items"])

    res_unassigned_detail = await client_unassigned.get(f"/api/v1/teacher/reviews/{portfolio_id}")
    assert res_unassigned_detail.status_code == 403

    res_unassigned_dec = await client_unassigned.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json={"revisionId": rev_id, "action": "approved", "rubric": {"initiative": 4, "collaboration": 4, "communication": 4, "responsibility": 4, "resilience": 4}},
    )
    assert res_unassigned_dec.status_code == 403

    # 7. Cross-school teacher cannot view detail or decide -> 404 (isolated tenant)
    client_cross = await get_authenticated_client("197903032003011003", "PasswordGuru123!")
    res_cross_detail = await client_cross.get(f"/api/v1/teacher/reviews/{portfolio_id}")
    assert res_cross_detail.status_code in (403, 404)

    res_cross_dec = await client_cross.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json={"revisionId": rev_id, "action": "approved", "rubric": {"initiative": 4, "collaboration": 4, "communication": 4, "responsibility": 4, "resilience": 4}},
    )
    assert res_cross_dec.status_code in (403, 404)

    # 8. Draft portfolio cannot be reviewed
    res_draft = await client_student.post(
        "/api/v1/student/portfolio",
        json={
            "title": "Draf Masih Belum Diajukan",
            "activityType": "project",
            "activityDate": "2026-08-20",
            "description": "Deskripsi draf.",
            "canonicalTagIds": ["web-development", "digital-literacy", "problem-solving"],
            "evidence": {"type": "external_link", "url": "https://github.com/alya-student/draft", "label": "Draft"},
        },
    )
    draft_id = res_draft.json()["portfolio_id"]
    draft_rev_id = res_draft.json()["current_revision_id"]
    res_draft_dec = await client_teacher.post(
        f"/api/v1/teacher/reviews/{draft_id}/decision",
        json={"revisionId": draft_rev_id, "action": "approved", "rubric": {"initiative": 4, "collaboration": 4, "communication": 4, "responsibility": 4, "resilience": 4}},
    )
    assert res_draft_dec.status_code == 409
    assert res_draft_dec.json()["error"]["code"] == "REVIEW_ALREADY_DECIDED"


# --- 2. Decision State Machine: Endorse, Revision Request, Reject ---

@pytest.mark.asyncio
async def test_teacher_decision_approve_endorse():
    client_student = await get_authenticated_client("0071234321", "PasswordSiswa123!")
    res_create = await client_student.post(
        "/api/v1/student/portfolio",
        json={
            "title": "Karya Desain UI Portal Siswa",
            "activityType": "creative-work",
            "activityDate": "2026-08-22",
            "description": "Desain antarmuka responsif Figma untuk portal pembelajaran siswa.",
            "canonicalTagIds": ["ui-ux", "graphic-design", "creativity"],
            "evidence": {"type": "external_link", "url": "https://figma.com/file/123", "label": "Figma Design"},
        },
    )
    portfolio_id = res_create.json()["portfolio_id"]
    res_sub = await client_student.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
    rev_id = res_sub.json()["current_revision_id"]

    client_teacher = await get_authenticated_client("198204152005011789", "PasswordGuru123!")

    # Attempt approve with missing rubric -> FAIL (400)
    res_fail = await client_teacher.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json={"revisionId": rev_id, "action": "approved", "feedback": "Bagus"},
    )
    assert res_fail.status_code == 400
    assert res_fail.json()["error"]["code"] == "RUBRIC_REQUIRED"

    # Attempt approve with rubric value out of 1-5 -> FAIL (400)
    res_fail_score = await client_teacher.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json={
            "revisionId": rev_id,
            "action": "approved",
            "rubric": {
                "initiative": 6,  # Invalid: > 5
                "collaboration": 4,
                "communication": 4,
                "responsibility": 4,
                "resilience": 3,
            },
        },
    )
    assert res_fail_score.status_code == 422

    # Successful Approval
    res_approve = await client_teacher.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json={
            "revisionId": rev_id,
            "action": "approved",
            "feedback": "Karya sangat orisinal dan sesuai standar industri.",
            "rubric": {
                "initiative": 5,
                "collaboration": 4,
                "communication": 4,
                "responsibility": 5,
                "resilience": 4,
            },
        },
    )
    assert res_approve.status_code == 200
    app_data = res_approve.json()
    assert app_data["status"] == "approved"
    assert app_data["applicationStatus"] == "applied"

    # Subsequent decision on already-decided portfolio -> 409 Conflict
    res_double = await client_teacher.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json={"revisionId": rev_id, "action": "approved", "rubric": {"initiative": 4, "collaboration": 4, "communication": 4, "responsibility": 4, "resilience": 4}},
    )
    assert res_double.status_code == 409
    assert res_double.json()["error"]["code"] == "REVIEW_ALREADY_DECIDED"


@pytest.mark.asyncio
async def test_teacher_decision_revision_request_and_student_cycle():
    client_student = await get_authenticated_client("0071234321", "PasswordSiswa123!")
    res_create = await client_student.post(
        "/api/v1/student/portfolio",
        json={
            "title": "Dokumentasi Instalasi Server Jaringan",
            "activityType": "project",
            "activityDate": "2026-08-25",
            "description": "Konfigurasi server Ubuntu dengan Nginx dan SSL.",
            "canonicalTagIds": ["web-development", "digital-literacy", "problem-solving"],
            "evidence": {"type": "external_link", "url": "https://github.com/alya-student/server-doc", "label": "Doc"},
        },
    )
    portfolio_id = res_create.json()["portfolio_id"]
    res_sub = await client_student.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
    v1_rev_id = res_sub.json()["current_revision_id"]

    client_teacher = await get_authenticated_client("198204152005011789", "PasswordGuru123!")

    # Attempt revision request with empty/too-short feedback -> FAIL (400)
    res_fail_fb = await client_teacher.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json={"revisionId": v1_rev_id, "action": "revision_requested", "feedback": "ok"},
    )
    assert res_fail_fb.status_code == 400
    assert res_fail_fb.json()["error"]["code"] == "FEEDBACK_REQUIRED"

    # Valid Revision Request
    teacher_feedback_text = "Tolong tambahkan diagram topologi jaringan dan tangkapan layar pengujian latency."
    res_rev = await client_teacher.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json={"revisionId": v1_rev_id, "action": "revision_requested", "feedback": teacher_feedback_text},
    )
    assert res_rev.status_code == 200
    assert res_rev.json()["status"] == "revision_requested"

    # Student views portfolio detail and sees REAL teacher feedback
    res_detail = await client_student.get(f"/api/v1/student/portfolio/{portfolio_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["status"] == "revision_requested"
    assert detail["teacher_feedback"] == teacher_feedback_text
    assert len(detail.get("validation_history", [])) >= 1

    # Student initiates next revision (Phase 4 existing flow)
    res_next_rev = await client_student.post(f"/api/v1/student/portfolio/{portfolio_id}/revision")
    assert res_next_rev.status_code == 200
    assert res_next_rev.json()["status"] == "draft"
    assert res_next_rev.json()["current_revision_number"] == 2
    v2_rev_id = res_next_rev.json()["current_revision_id"]
    assert v2_rev_id != v1_rev_id

    # Teacher attempting decision against stale revision v1 -> FAIL 409
    res_stale = await client_teacher.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json={"revisionId": v1_rev_id, "action": "approved", "rubric": {"initiative": 4, "collaboration": 4, "communication": 4, "responsibility": 4, "resilience": 4}},
    )
    assert res_stale.status_code == 409

    # Student resubmits revision v2
    res_resub = await client_student.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
    assert res_resub.status_code == 200
    assert res_resub.json()["status"] == "submitted"

    # Teacher now sees v2 in queue and approves
    res_app_v2 = await client_teacher.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json={
            "revisionId": v2_rev_id,
            "action": "approved",
            "feedback": "Diagram topologi sangat jelas, karya disetujui!",
            "rubric": {"initiative": 4, "collaboration": 4, "communication": 5, "responsibility": 4, "resilience": 4},
        },
    )
    assert res_app_v2.status_code == 200
    assert res_app_v2.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_teacher_decision_reject():
    client_student = await get_authenticated_client("0071234321", "PasswordSiswa123!")
    res_create = await client_student.post(
        "/api/v1/student/portfolio",
        json={
            "title": "Karya Tidak Sesuai Ketentuan",
            "activityType": "project",
            "activityDate": "2026-08-25",
            "description": "Deskripsi karya.",
            "canonicalTagIds": ["web-development", "digital-literacy", "problem-solving"],
            "evidence": {"type": "external_link", "url": "https://example.com", "label": "Link"},
        },
    )
    portfolio_id = res_create.json()["portfolio_id"]
    res_sub = await client_student.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
    rev_id = res_sub.json()["current_revision_id"]

    client_teacher = await get_authenticated_client("198204152005011789", "PasswordGuru123!")

    # Missing rejection reason -> FAIL
    res_fail = await client_teacher.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json={"revisionId": rev_id, "action": "rejected", "feedback": ""},
    )
    assert res_fail.status_code == 400
    assert res_fail.json()["error"]["code"] == "REJECTION_REASON_REQUIRED"

    # Valid rejection
    res_rej = await client_teacher.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json={"revisionId": rev_id, "action": "rejected", "feedback": "Karya ini bukan hasil karya asli dan terbukti plagiasi."},
    )
    assert res_rej.status_code == 200
    assert res_rej.json()["status"] == "rejected"

    # Student cannot begin revision on rejected work
    res_std_rev = await client_student.post(f"/api/v1/student/portfolio/{portfolio_id}/revision")
    assert res_std_rev.status_code == 409


# --- 3. Decision Idempotency and Double-Click Protection ---

@pytest.mark.asyncio
async def test_decision_idempotency_and_double_click():
    client_student = await get_authenticated_client("0071234321", "PasswordSiswa123!")
    res_create = await client_student.post(
        "/api/v1/student/portfolio",
        json={
            "title": "Karya Uji Idempotensi Validasi",
            "activityType": "project",
            "activityDate": "2026-08-26",
            "description": "Karya untuk verifikasi idempotensi keputusan guru.",
            "canonicalTagIds": ["web-development", "digital-literacy", "problem-solving"],
            "evidence": {"type": "external_link", "url": "https://github.com/alya-student/idem", "label": "Code"},
        },
    )
    portfolio_id = res_create.json()["portfolio_id"]
    res_sub = await client_student.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
    rev_id = res_sub.json()["current_revision_id"]

    client_teacher = await get_authenticated_client("198204152005011789", "PasswordGuru123!")

    idempotency_key = f"key-dec-{uuid.uuid4()}"
    approve_body = {
        "revisionId": rev_id,
        "action": "approved",
        "feedback": "Bagus sekali.",
        "rubric": {"initiative": 4, "collaboration": 4, "communication": 4, "responsibility": 4, "resilience": 4},
    }

    # First request
    res1 = await client_teacher.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json=approve_body,
        headers={"Idempotency-Key": idempotency_key},
    )
    assert res1.status_code == 200
    dec_id_1 = res1.json()["decisionId"]

    # Repeated request with same Idempotency-Key
    res2 = await client_teacher.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json=approve_body,
        headers={"Idempotency-Key": idempotency_key},
    )
    assert res2.status_code == 200
    assert res2.json()["decisionId"] == dec_id_1


# --- 4. Private Evidence Download Authorization ---

@pytest.mark.asyncio
async def test_teacher_evidence_download_access(setup_services):
    client_student = await get_authenticated_client("0071234321", "PasswordSiswa123!")

    # 1. Create initial draft portfolio
    res_create = await client_student.post(
        "/api/v1/student/portfolio",
        json={
            "title": "Laporan Proyek Jaringan Sekolah",
            "activityType": "project",
            "activityDate": "2026-08-28",
            "description": "Laporan pengujian infrastruktur jaringan.",
            "canonicalTagIds": ["web-development", "digital-literacy", "problem-solving"],
        },
    )
    assert res_create.status_code == 201
    portfolio_id = res_create.json()["portfolio_id"]

    # 2. Upload intent on draft portfolio
    res_intent = await client_student.post(
        f"/api/v1/student/portfolio/{portfolio_id}/uploads",
        json={"filename": "laporan_akhir.pdf", "contentType": "application/pdf", "sizeBytes": 2048},
    )
    assert res_intent.status_code == 201
    intent_data = res_intent.json()
    storage_id = intent_data["storageObjectId"]
    object_key = intent_data["objectKey"]

    # 3. Store valid file bytes into object storage
    genuine_pdf_bytes = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    teach_service = setup_services["teacher_service"]
    teach_service.storage.upload_object(
        object_key=object_key,
        data=io.BytesIO(genuine_pdf_bytes),
        content_type="application/pdf",
    )

    # 4. Complete upload
    res_complete = await client_student.post(
        f"/api/v1/student/portfolio/{portfolio_id}/uploads/{storage_id}/complete"
    )
    assert res_complete.status_code == 200

    # 5. Attach file evidence to draft portfolio
    await client_student.patch(
        f"/api/v1/student/portfolio/{portfolio_id}",
        json={"evidence": {"type": "file", "storageObjectId": storage_id}},
    )

    # 6. Submit portfolio
    res_sub = await client_student.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
    assert res_sub.status_code == 200

    # 7. Assigned teacher accesses evidence
    client_teacher = await get_authenticated_client("198204152005011789", "PasswordGuru123!")
    res_ev = await client_teacher.get(f"/api/v1/teacher/reviews/{portfolio_id}/evidence/{storage_id}/access")
    assert res_ev.status_code == 200
    assert "downloadUrl" in res_ev.json()
    assert "private" in res_ev.headers.get("cache-control", "").lower()
    assert "no-store" in res_ev.headers.get("cache-control", "").lower()


# --- 5. Critical End-to-End Integration Flow ---

@pytest.mark.asyncio
async def test_end_to_end_validation_and_skills_flow(setup_services):
    """
    SECTION 16 & Acceptance Criteria:
    Student creates draft -> uploads evidence -> submits v1
    Teacher sees queue -> requests revision with feedback
    Student sees feedback -> starts v2 -> edits -> resubmits
    Teacher sees v2 -> completes 5-dimension rubric -> approves
    Skills radar updates strictly from approved v2
    Old v1 remains completely immutable
    """
    client_student = await get_authenticated_client("0071234321", "PasswordSiswa123!")

    # 1. Student creates draft
    res_create = await client_student.post(
        "/api/v1/student/portfolio",
        json={
            "title": "Aplikasi Toko Online Koperasi Sekolah",
            "activityType": "project",
            "activityDate": "2026-08-30",
            "description": "Pengembangan web e-commerce koperasi sekolah dengan Next.js.",
            "canonicalTagIds": ["web-development", "digital-literacy", "problem-solving"],
        },
    )
    assert res_create.status_code == 201
    portfolio_id = res_create.json()["portfolio_id"]

    # Upload evidence
    res_intent = await client_student.post(
        f"/api/v1/student/portfolio/{portfolio_id}/uploads",
        json={"filename": "arsitektur_ecom.pdf", "contentType": "application/pdf", "sizeBytes": 2048},
    )
    assert res_intent.status_code == 201
    storage_id = res_intent.json()["storageObjectId"]
    object_key = res_intent.json()["objectKey"]

    genuine_pdf_bytes = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    teach_service = setup_services["teacher_service"]
    teach_service.storage.upload_object(
        object_key=object_key,
        data=io.BytesIO(genuine_pdf_bytes),
        content_type="application/pdf",
    )
    res_comp = await client_student.post(f"/api/v1/student/portfolio/{portfolio_id}/uploads/{storage_id}/complete")
    assert res_comp.status_code == 200

    await client_student.patch(
        f"/api/v1/student/portfolio/{portfolio_id}",
        json={"evidence": {"type": "file", "storageObjectId": storage_id}},
    )

    # Submit v1
    res_sub_v1 = await client_student.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
    assert res_sub_v1.status_code == 200
    v1_rev_id = res_sub_v1.json()["current_revision_id"]

    # 2. Teacher sees queue & requests revision
    client_teacher = await get_authenticated_client("198204152005011789", "PasswordGuru123!")
    feedback_msg = "Tolong lengkapi rancangan skema basis data dan pengujian API payment gateway."
    res_req_rev = await client_teacher.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json={"revisionId": v1_rev_id, "action": "revision_requested", "feedback": feedback_msg},
    )
    assert res_req_rev.status_code == 200

    # Skills check: revision_requested contributes 0
    res_skills_pre = await client_student.get("/api/v1/student/skills")
    assert res_skills_pre.status_code == 200
    # No approved items yet from this portfolio
    pre_radar = {r["dimension"]: r for r in res_skills_pre.json()["radar"]}
    assert not any(contrib["portfolioId"] == portfolio_id for r in pre_radar.values() for contrib in r.get("contributors", []))

    # 3. Student sees feedback & creates v2
    res_detail = await client_student.get(f"/api/v1/student/portfolio/{portfolio_id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["teacher_feedback"] == feedback_msg

    res_new_rev = await client_student.post(f"/api/v1/student/portfolio/{portfolio_id}/revision")
    assert res_new_rev.status_code == 200
    v2_rev_id = res_new_rev.json()["current_revision_id"]
    assert v2_rev_id != v1_rev_id

    # Edit & resubmit v2
    await client_student.patch(
        f"/api/v1/student/portfolio/{portfolio_id}",
        json={"description": "Versi 2 lengkap dengan skema basis data dan modul payment gateway."},
    )
    res_sub_v2 = await client_student.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
    assert res_sub_v2.status_code == 200
    assert res_sub_v2.json()["status"] == "submitted"

    # 4. Teacher reviews and approves v2 with complete rubric
    res_app_v2 = await client_teacher.post(
        f"/api/v1/teacher/reviews/{portfolio_id}/decision",
        json={
            "revisionId": v2_rev_id,
            "action": "approved",
            "feedback": "Perbaikan sangat memuaskan, karya disetujui!",
            "rubric": {
                "initiative": 5,
                "collaboration": 4,
                "communication": 4,
                "responsibility": 5,
                "resilience": 4,
            },
        },
    )
    assert res_app_v2.status_code == 200
    assert res_app_v2.json()["status"] == "approved"

    # 5. Verify Student Skills radar is updated from approved v2
    res_skills_post = await client_student.get("/api/v1/student/skills")
    assert res_skills_post.status_code == 200
    skills_data = res_skills_post.json()
    post_radar = {r["dimension"]: r for r in skills_data["radar"]}

    # Contributor provenance links to portfolio_id
    dig_lit = post_radar["digital-literacy"]
    assert any(c["portfolioId"] == portfolio_id for c in dig_lit["contributors"])
    assert dig_lit["evidenceCount"] >= 1
    assert dig_lit["score"] >= 20

    # Old v1 revision snapshot remains immutable
    v1_doc = await setup_services["portfolio_repo"].get_revision_by_id(v1_rev_id)
    assert v1_doc is not None
    assert v1_doc["version"] == 1
    assert "payment gateway" not in v1_doc["description_snapshot"].lower()
