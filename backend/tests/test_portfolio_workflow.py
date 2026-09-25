import pytest
import io
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.portfolio_service import PortfolioService
from app.api.v1.student_portfolio import get_portfolio_service, set_portfolio_service
from app.repositories.portfolio import InMemoryPortfolioRepository
from app.repositories.storage_metadata import StorageMetadataRepository
from app.repositories.skill_tag import SkillTagRepository
from app.storage.local import LocalObjectStorage
from app.services.maintenance import cleanup_stale_uploads


@pytest.fixture(autouse=True)
def setup_portfolio_service(tmp_path):
    """Ensure in-memory repository and local temporary storage are used for tests."""
    storage_dir = tmp_path / "test_storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    local_storage = LocalObjectStorage(base_directory=str(storage_dir))
    portfolio_repo = InMemoryPortfolioRepository()
    storage_meta_repo = StorageMetadataRepository()
    skill_tag_repo = SkillTagRepository()

    svc = PortfolioService(
        portfolio_repo=portfolio_repo,
        storage_meta_repo=storage_meta_repo,
        skill_tag_repo=skill_tag_repo,
        object_storage=local_storage,
    )
    set_portfolio_service(svc)
    yield svc
    set_portfolio_service(None)


async def get_authenticated_client(identifier: str, password: str = "PasswordSiswa123!") -> AsyncClient:
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    res = await client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})
    assert res.status_code == 200, f"Login failed for {identifier}: {res.text}"
    return client


# --- 1. Skill Tags Catalog API ---

@pytest.mark.asyncio
async def test_skill_tags_catalog_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.get("/api/v1/skill-tags")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert len(data["items"]) >= 14
        codes = [item["code"] for item in data["items"]]
        assert "web-development" in codes
        assert "problem-solving" in codes
        assert "leadership" in codes


# --- 2. Create Draft, Read Detail, List, Update, and Delete ---

@pytest.mark.asyncio
async def test_portfolio_draft_lifecycle():
    client = await get_authenticated_client("0071234321")  # Student 1
    try:
        # 1. Create Draft
        create_payload = {
            "title": "Aplikasi Web E-Commerce Koperasi Siswa",
            "activityType": "project",
            "activityDate": "2026-08-15",
            "description": "Pengembangan aplikasi web berbasis React dan FastAPI untuk koperasi sekolah.",
            "canonicalTagIds": ["web-development", "problem-solving"],
            "evidence": {
                "type": "external_link",
                "url": "https://github.com/alya-student/koperasi-app",
                "label": "GitHub Repository",
            },
        }
        res = await client.post("/api/v1/student/portfolio", json=create_payload)
        assert res.status_code == 201, res.text
        created = res.json()
        portfolio_id = created["portfolio_id"]
        assert created["status"] == "draft"
        assert created["current_revision_number"] == 1

        # 2. Get Detail
        res_get = await client.get(f"/api/v1/student/portfolio/{portfolio_id}")
        assert res_get.status_code == 200
        detail = res_get.json()
        assert detail["title"] == "Aplikasi Web E-Commerce Koperasi Siswa"
        assert len(detail["evidence_refs"]) == 1
        assert detail["evidence_refs"][0]["type"] == "external_link"

        # 3. List with search & status filter
        res_list = await client.get("/api/v1/student/portfolio?status=draft&search=koperasi")
        assert res_list.status_code == 200
        list_data = res_list.json()
        assert list_data["total"] >= 1
        assert any(item["portfolio_id"] == portfolio_id for item in list_data["items"])

        # 4. Update Draft
        update_payload = {
            "title": "Aplikasi Web E-Commerce Koperasi Siswa Revisi Judul",
            "canonicalTagIds": ["web-development", "problem-solving", "teamwork"],
        }
        res_patch = await client.patch(f"/api/v1/student/portfolio/{portfolio_id}", json=update_payload)
        assert res_patch.status_code == 200
        assert res_patch.json()["title"] == "Aplikasi Web E-Commerce Koperasi Siswa Revisi Judul"

        # 5. Delete Draft
        res_del = await client.delete(f"/api/v1/student/portfolio/{portfolio_id}")
        assert res_del.status_code == 204

        # Verify deletion
        res_after = await client.get(f"/api/v1/student/portfolio/{portfolio_id}")
        assert res_after.status_code == 404
    finally:
        await client.aclose()


# --- 3. Tag Validation Rules (Strict 3 to 5 Tags upon submission) ---

@pytest.mark.asyncio
async def test_tag_count_and_validity_on_submission():
    client = await get_authenticated_client("0071234321")
    try:
        # Create draft with valid evidence
        create_payload = {
            "title": "Proyek Uji Validasi Tag",
            "activityType": "project",
            "description": "Deskripsi proyek yang cukup panjang untuk memenuhi syarat pengajuan.",
            "canonicalTagIds": ["web-development"],  # only 1 tag
            "evidence": {
                "type": "external_link",
                "url": "https://github.com/alya-student/tag-test",
                "label": "Demo Link",
            },
        }
        res = await client.post("/api/v1/student/portfolio", json=create_payload)
        assert res.status_code == 201
        portfolio_id = res.json()["portfolio_id"]

        # Attempt submit with 1 tag -> REJECT
        res_sub1 = await client.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
        assert res_sub1.status_code == 400
        assert res_sub1.json()["error"]["code"] == "PORTFOLIO_TAG_COUNT_INVALID"

        # Update to 2 tags -> REJECT
        await client.patch(
            f"/api/v1/student/portfolio/{portfolio_id}",
            json={"canonicalTagIds": ["web-development", "teamwork"]},
        )
        res_sub2 = await client.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
        assert res_sub2.status_code == 400
        assert res_sub2.json()["error"]["code"] == "PORTFOLIO_TAG_COUNT_INVALID"

        # Update to 6 tags -> REJECT
        await client.patch(
            f"/api/v1/student/portfolio/{portfolio_id}",
            json={
                "canonicalTagIds": [
                    "web-development",
                    "teamwork",
                    "problem-solving",
                    "leadership",
                    "research",
                    "creativity",
                ]
            },
        )
        res_sub6 = await client.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
        assert res_sub6.status_code == 400
        assert res_sub6.json()["error"]["code"] == "PORTFOLIO_TAG_COUNT_INVALID"

        # Update with unknown/invalid tag -> REJECT
        await client.patch(
            f"/api/v1/student/portfolio/{portfolio_id}",
            json={"canonicalTagIds": ["web-development", "teamwork", "tag-palsu-ngawur"]},
        )
        res_sub_unknown = await client.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
        assert res_sub_unknown.status_code == 400
        assert res_sub_unknown.json()["error"]["code"] == "PORTFOLIO_TAG_INVALID"

        # Update to 3 valid tags -> PASS
        await client.patch(
            f"/api/v1/student/portfolio/{portfolio_id}",
            json={"canonicalTagIds": ["web-development", "teamwork", "problem-solving"]},
        )
        res_sub_ok = await client.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
        assert res_sub_ok.status_code == 200
        assert res_sub_ok.json()["status"] == "submitted"
    finally:
        await client.aclose()


# --- 4. Evidence Required Gate ---

@pytest.mark.asyncio
async def test_evidence_required_gate():
    client = await get_authenticated_client("0071234321")
    try:
        # Create draft with NO evidence
        create_payload = {
            "title": "Proyek Tanpa Bukti",
            "activityType": "project",
            "description": "Deskripsi proyek valid namun tidak memiliki berkas ataupun tautan bukti.",
            "canonicalTagIds": ["web-development", "teamwork", "problem-solving"],
        }
        res = await client.post("/api/v1/student/portfolio", json=create_payload)
        assert res.status_code == 201
        portfolio_id = res.json()["portfolio_id"]

        # Attempt submit without evidence -> FAIL
        res_sub = await client.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
        assert res_sub.status_code == 400
        assert res_sub.json()["error"]["code"] == "PORTFOLIO_EVIDENCE_REQUIRED"
    finally:
        await client.aclose()


# --- 5. File Upload Lifecycle & Magic-Byte Validation ---

@pytest.mark.asyncio
async def test_upload_policy_and_magic_byte_validation(setup_portfolio_service):
    svc = setup_portfolio_service
    client = await get_authenticated_client("0071234321")
    try:
        # Create draft
        res = await client.post(
            "/api/v1/student/portfolio",
            json={
                "title": "Proyek Uji Berkas",
                "activityType": "project",
                "description": "Deskripsi lengkap pengujian unggahan berkas bukti portofolio.",
                "canonicalTagIds": ["web-development", "teamwork", "problem-solving"],
            },
        )
        portfolio_id = res.json()["portfolio_id"]

        # 1. Reject forbidden extension
        res_bad_ext = await client.post(
            f"/api/v1/student/portfolio/{portfolio_id}/uploads",
            json={"filename": "malware.exe", "contentType": "application/x-msdownload", "sizeBytes": 1024},
        )
        assert res_bad_ext.status_code == 400

        # 2. Reject oversized image (> 5MB)
        res_over_img = await client.post(
            f"/api/v1/student/portfolio/{portfolio_id}/uploads",
            json={"filename": "huge.png", "contentType": "image/png", "sizeBytes": 6 * 1024 * 1024},
        )
        assert res_over_img.status_code == 400

        # 3. Valid PDF intent
        res_intent = await client.post(
            f"/api/v1/student/portfolio/{portfolio_id}/uploads",
            json={"filename": "laporan.pdf", "contentType": "application/pdf", "sizeBytes": 1024},
        )
        assert res_intent.status_code == 201
        intent_data = res_intent.json()
        storage_id = intent_data["storageObjectId"]
        object_key = intent_data["objectKey"]

        # 4. MIME Spoofing Test: Upload text/executable binary pretending to be PDF
        fake_pdf_content = b"This is plain text pretending to be PDF"
        svc.storage.upload_object(
            object_key=object_key,
            data=io.BytesIO(fake_pdf_content),
            content_type="application/pdf",
        )

        res_complete_fake = await client.post(
            f"/api/v1/student/portfolio/{portfolio_id}/uploads/{storage_id}/complete"
        )
        assert res_complete_fake.status_code == 400
        assert res_complete_fake.json()["error"]["code"] == "UPLOAD_VALIDATION_FAILED"

        # 5. Genuine PDF Upload Test
        real_pdf_intent = await client.post(
            f"/api/v1/student/portfolio/{portfolio_id}/uploads",
            json={"filename": "dokumen_asli.pdf", "contentType": "application/pdf", "sizeBytes": 2048},
        )
        real_storage_id = real_pdf_intent.json()["storageObjectId"]
        real_object_key = real_pdf_intent.json()["objectKey"]

        genuine_pdf_bytes = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        svc.storage.upload_object(
            object_key=real_object_key,
            data=io.BytesIO(genuine_pdf_bytes),
            content_type="application/pdf",
        )

        res_complete_real = await client.post(
            f"/api/v1/student/portfolio/{portfolio_id}/uploads/{real_storage_id}/complete"
        )
        assert res_complete_real.status_code == 200
        completed_data = res_complete_real.json()
        assert completed_data["status"] == "available"

        # 6. Attach available evidence to draft & access download URL
        await client.patch(
            f"/api/v1/student/portfolio/{portfolio_id}",
            json={
                "evidence": {
                    "type": "file",
                    "storageObjectId": real_storage_id,
                }
            },
        )

        res_access = await client.get(
            f"/api/v1/student/portfolio/{portfolio_id}/evidence/{real_storage_id}/access"
        )
        assert res_access.status_code == 200
        access_data = res_access.json()
        assert "downloadUrl" in access_data
        assert "no-store" in res_access.headers.get("Cache-Control", "")

        # 7. Submit now succeeds
        res_submit = await client.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
        assert res_submit.status_code == 200
        assert res_submit.json()["status"] == "submitted"
    finally:
        await client.aclose()


# --- 6. External Link Validation (Anti-SSRF) ---

@pytest.mark.asyncio
async def test_external_link_validation():
    client = await get_authenticated_client("0071234321")
    try:
        # 1. Reject javascript: scheme
        res_js = await client.post(
            "/api/v1/student/portfolio",
            json={
                "title": "Proyek XSS Link",
                "description": "Deskripsi proyek dengan tautan tidak aman.",
                "evidence": {"type": "external_link", "url": "javascript:alert(1)"},
            },
        )
        assert res_js.status_code == 400
        assert res_js.json()["error"]["code"] == "EXTERNAL_LINK_INVALID"

        # 2. Reject localhost / SSRF
        res_local = await client.post(
            "/api/v1/student/portfolio",
            json={
                "title": "Proyek SSRF Link",
                "description": "Deskripsi proyek dengan tautan lokal.",
                "evidence": {"type": "external_link", "url": "https://localhost:8080/admin"},
            },
        )
        assert res_local.status_code == 400

        # 3. Reject credentials in URL
        res_cred = await client.post(
            "/api/v1/student/portfolio",
            json={
                "title": "Proyek Cred Link",
                "description": "Deskripsi proyek dengan user:pass di URL.",
                "evidence": {"type": "external_link", "url": "https://user:pass@example.com"},
            },
        )
        assert res_cred.status_code == 400

        # 4. Valid HTTPS link -> PASS
        res_valid = await client.post(
            "/api/v1/student/portfolio",
            json={
                "title": "Proyek Tautan Valid",
                "description": "Deskripsi proyek dengan tautan HTTPS yang benar.",
                "evidence": {
                    "type": "external_link",
                    "url": "https://drive.google.com/file/d/example-id/view",
                    "label": "Google Drive Dokumen",
                },
            },
        )
        assert res_valid.status_code == 201
    finally:
        await client.aclose()


# --- 7. State Immutability & Revision Workflow ---

@pytest.mark.asyncio
async def test_immutability_and_revision_lifecycle():
    client = await get_authenticated_client("0071234321")
    try:
        # Create and submit
        res = await client.post(
            "/api/v1/student/portfolio",
            json={
                "title": "Proyek Siklus Revisi",
                "description": "Deskripsi proyek untuk menguji siklus revisi dan kekekalan riwayat.",
                "canonicalTagIds": ["web-development", "teamwork", "problem-solving"],
                "evidence": {"type": "external_link", "url": "https://github.com/example/repo"},
            },
        )
        portfolio_id = res.json()["portfolio_id"]
        res_submit = await client.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
        assert res_submit.status_code == 200

        # 1. Submitted item CANNOT be edited
        res_edit = await client.patch(
            f"/api/v1/student/portfolio/{portfolio_id}",
            json={"title": "Mencoba Mengubah Karya Terkirim"},
        )
        assert res_edit.status_code == 409
        assert res_edit.json()["error"]["code"] == "PORTFOLIO_NOT_EDITABLE"

        # 2. Submitted item CANNOT be resubmitted
        res_resub = await client.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
        assert res_resub.status_code == 409

        # 3. Student CANNOT delete submitted item
        res_del = await client.delete(f"/api/v1/student/portfolio/{portfolio_id}")
        assert res_del.status_code == 409

        # 4. Student CANNOT call /revision when status is still 'submitted'
        res_rev_fail = await client.post(f"/api/v1/student/portfolio/{portfolio_id}/revision")
        assert res_rev_fail.status_code == 409
        assert res_rev_fail.json()["error"]["code"] == "PORTFOLIO_INVALID_STATE"

        # 5. Simulate Teacher requesting revision (setting status = revision_requested in repository)
        svc = get_portfolio_service()
        await svc.portfolio_repo.set_status_for_testing(
            school_id="sch_teladan_001",
            portfolio_id=portfolio_id,
            status="revision_requested",
        )

        # 6. Now student can begin next revision cycle
        res_rev_ok = await client.post(f"/api/v1/student/portfolio/{portfolio_id}/revision")
        assert res_rev_ok.status_code == 200
        rev_data = res_rev_ok.json()
        assert rev_data["status"] == "draft"
        assert rev_data["current_revision_number"] == 2

        # 7. Edit version 2
        res_edit_v2 = await client.patch(
            f"/api/v1/student/portfolio/{portfolio_id}",
            json={"description": "Deskripsi versi 2 yang telah diperbarui sesuai arahan revisi guru."},
        )
        assert res_edit_v2.status_code == 200

        # 8. Resubmit version 2
        res_resub_ok = await client.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
        assert res_resub_ok.status_code == 200
        assert res_resub_ok.json()["status"] == "submitted"
        assert res_resub_ok.json()["current_revision_number"] == 2

        # 9. Verify history: previous revision 1 remains immutable in storage
        rev1 = await svc.portfolio_repo.get_revision("sch_teladan_001", portfolio_id, 1)
        assert rev1 is not None
        assert rev1["version"] == 1
        assert rev1["submitted_at"] is not None
        assert rev1["description_snapshot"] != "Deskripsi versi 2 yang telah diperbarui sesuai arahan revisi guru."
    finally:
        await client.aclose()


# --- 8. Cross-Student & Tenant Isolation Tests ---

@pytest.mark.asyncio
async def test_cross_student_and_tenant_isolation():
    client_student1 = await get_authenticated_client("0071234321")  # Student 1 in School 1
    client_student2 = await get_authenticated_client("0071234322")  # Student 2 in School 1
    client_student_other = await get_authenticated_client("0071234999")  # Student in School 2
    client_teacher = await get_authenticated_client("198204152005011789", "PasswordGuru123!")
    client_admin = await get_authenticated_client("20101543", "PasswordAdmin123!")

    try:
        # Student 1 creates a draft
        res = await client_student1.post(
            "/api/v1/student/portfolio",
            json={
                "title": "Karya Rahasia Siswa 1",
                "description": "Deskripsi karya pribadi yang tidak boleh diakses siswa lain.",
                "canonicalTagIds": ["web-development", "teamwork", "problem-solving"],
                "evidence": {"type": "external_link", "url": "https://github.com/student1/secret"},
            },
        )
        portfolio_id = res.json()["portfolio_id"]

        # Student 2 (same school) CANNOT read Student 1's portfolio -> 404
        res_s2_get = await client_student2.get(f"/api/v1/student/portfolio/{portfolio_id}")
        assert res_s2_get.status_code == 404

        # Student 2 CANNOT edit Student 1's portfolio -> 404
        res_s2_patch = await client_student2.patch(
            f"/api/v1/student/portfolio/{portfolio_id}",
            json={"title": "Hacked Title"},
        )
        assert res_s2_patch.status_code == 404

        # Student 2 CANNOT submit Student 1's portfolio -> 404
        res_s2_sub = await client_student2.post(f"/api/v1/student/portfolio/{portfolio_id}/submit")
        assert res_s2_sub.status_code == 404

        # Student in School 2 CANNOT read Student 1's portfolio -> 404
        res_other_get = await client_student_other.get(f"/api/v1/student/portfolio/{portfolio_id}")
        assert res_other_get.status_code == 404

        # Teacher accessing student portfolio endpoint -> 403 Forbidden
        res_tch = await client_teacher.get("/api/v1/student/portfolio")
        assert res_tch.status_code == 403

        # Admin accessing student portfolio endpoint -> 403 Forbidden
        res_adm = await client_admin.get("/api/v1/student/portfolio")
        assert res_adm.status_code == 403

        # Anonymous request -> 401 Unauthorized
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as anon_client:
            res_anon = await anon_client.get("/api/v1/student/portfolio")
            assert res_anon.status_code == 401
    finally:
        await client_student1.aclose()
        await client_student2.aclose()
        await client_student_other.aclose()
        await client_teacher.aclose()
        await client_admin.aclose()


# --- 9. Idempotency & Concurrency Tests ---

@pytest.mark.asyncio
async def test_idempotency_and_double_submit():
    client = await get_authenticated_client("0071234321")
    try:
        # Create draft with Idempotency-Key
        idempotency_key = "test-idem-key-12345"
        payload = {
            "title": "Proyek Idempoten",
            "description": "Deskripsi proyek idempoten yang cukup panjang untuk pengajuan.",
            "canonicalTagIds": ["web-development", "teamwork", "problem-solving"],
            "evidence": {"type": "external_link", "url": "https://github.com/test/idem"},
        }
        res1 = await client.post(
            "/api/v1/student/portfolio",
            json=payload,
            headers={"Idempotency-Key": idempotency_key},
        )
        assert res1.status_code == 201
        portfolio_id_1 = res1.json()["portfolio_id"]

        # Repeated request with same Idempotency-Key returns cached response
        res2 = await client.post(
            "/api/v1/student/portfolio",
            json=payload,
            headers={"Idempotency-Key": idempotency_key},
        )
        assert res2.status_code == 201
        assert res2.json()["portfolio_id"] == portfolio_id_1

        # Submit with Idempotency-Key
        sub_key = "test-submit-key-67890"
        res_sub1 = await client.post(
            f"/api/v1/student/portfolio/{portfolio_id_1}/submit",
            headers={"Idempotency-Key": sub_key},
        )
        assert res_sub1.status_code == 200

        # Repeated submit with same Idempotency-Key succeeds with same cached payload
        res_sub2 = await client.post(
            f"/api/v1/student/portfolio/{portfolio_id_1}/submit",
            headers={"Idempotency-Key": sub_key},
        )
        assert res_sub2.status_code == 200
        assert res_sub2.json()["status"] == "submitted"
    finally:
        await client.aclose()


# --- 10. Stale Pending Upload Cleanup Test ---

@pytest.mark.asyncio
async def test_stale_pending_upload_cleanup(setup_portfolio_service):
    svc = setup_portfolio_service
    # Create an old pending upload row
    import uuid
    meta_repo = svc.storage_meta_repo
    stale_id = str(uuid.uuid4())
    stale_key = f"schools/test/students/test/{uuid.uuid4()}.pdf"
    await meta_repo.create_pending_upload(
        id=stale_id,
        school_id="sch_teladan_001",
        owner_user_id="usr_std_001",
        provider="local",
        bucket="local",
        object_key=stale_key,
        original_filename="stale.pdf",
        content_type="application/pdf",
        declared_size=1024,
    )

    # Put a mock blob in storage
    svc.storage.upload_object(stale_key, io.BytesIO(b"old uncompleted blob"), "application/pdf")
    assert svc.storage.object_exists(stale_key)

    # Run cleanup with 0 seconds TTL (cleans all existing pending records)
    purged = await cleanup_stale_uploads(
        older_than_seconds=0,
        storage_meta_repo=meta_repo,
        object_storage=svc.storage,
    )
    assert stale_key in purged
    assert not svc.storage.object_exists(stale_key)
