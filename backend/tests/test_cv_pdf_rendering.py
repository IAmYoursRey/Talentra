import io
import pytest
import pymupdf

from app.services.cv_pdf_renderer import ReportLabCVRenderer
from app.core.cv_security import derive_snapshot_fingerprint


def test_pdf_rendering_selectable_text_and_no_pii_leakage():
    """
    SECTION 85: PDF text must be real selectable text.
    Must contain: Student name, School, approved project title, document code, fingerprint.
    Must NOT contain: NISN, NIP, NPSN, user UUID, JWT, storage key, passwords.
    """
    renderer = ReportLabCVRenderer()

    snapshot = {
        "profile": {
            "display_name": "Rizky Ramadhan",
            "school_name": "SMK Negeri 7 Semarang",
            "class_name": "XII RPL 1",
            "professional_summary": "Siswa dengan rekam jejak karya tervalidasi pada Literasi Digital dan Pemecahan Masalah.",
        },
        "approved_skills": [
            {"name": "Literasi Digital", "score": 85, "level": "Tingkat Mahir"},
            {"name": "Pemecahan Masalah", "score": 78, "level": "Tingkat Menengah"},
        ],
        "selected_portfolios": [
            {
                "title": "Aplikasi Monitoring Suhu IoT",
                "activity_type": "project",
                "activity_date": "15 Agustus 2026",
                "professional_description": "Mengembangkan sistem telemetri sensor suhu berbasis mikrokontroler.",
                "tags": ["IoT", "Web Development"],
            }
        ],
        "teacher_validated_competencies": [
            {"dimension": "Inisiatif Mandiri", "score": 4.8, "summary": "Rata-rata penilaian guru: 4.8/5 (2 karya)"}
        ],
        "content_digest": "3a8b2c1d9e4f0a7b5c8d6e3f1a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6a8b",
    }

    display_code = "TLN-8F4K-2M7P"
    token = "test_high_entropy_token_secret_12345"
    issued_date = "25 September 2026"

    pdf_bytes = renderer.render(
        snapshot=snapshot,
        display_code=display_code,
        verification_token=token,
        issued_date=issued_date,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000

    # Inspect PDF with PyMuPDF
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    page_count = len(doc)
    assert page_count <= 2, f"Target page count <= 2, got {page_count}"

    full_text = ""
    for page in doc:
        full_text += page.get_text()

    # 1. Assert required visible fields
    assert "Rizky Ramadhan" in full_text
    assert "SMK Negeri 7 Semarang" in full_text
    assert "Aplikasi Monitoring Suhu IoT" in full_text
    assert "Literasi Digital" in full_text
    assert display_code in full_text
    fingerprint = derive_snapshot_fingerprint(snapshot["content_digest"])
    assert fingerprint in full_text

    # 2. Assert strictly forbidden confidential data
    forbidden_tokens = [
        "0051234567",  # Synthetic NISN
        "19850101",    # Synthetic NIP
        "20101234",    # Synthetic NPSN
        token,         # Raw verification secret bearer token must not be printed in text
        "schools/",    # Private storage key prefix
        "students/",
        "Bearer ",
        "eyJ",         # Common JWT header prefix
    ]
    for ft in forbidden_tokens:
        assert ft not in full_text, f"Forbidden confidential token '{ft}' leaked into PDF text!"

    # 3. Assert Metadata is safe
    metadata = doc.metadata
    assert metadata.get("title") == "TALENTRA Digital CV"
    assert metadata.get("author") == "Rizky Ramadhan"
    for ft in forbidden_tokens:
        for k, v in metadata.items():
            if v:
                assert ft not in str(v), f"Forbidden confidential token '{ft}' leaked into PDF metadata!"


def test_pdf_rendering_xss_and_untrusted_input_sanitization():
    """
    SECTION 80, 86: Treat all candidate text as untrusted.
    Renderer must not crash on HTML tags or entities.
    """
    renderer = ReportLabCVRenderer()

    malicious_snapshot = {
        "profile": {
            "display_name": "Andi <script>alert(1)</script>",
            "school_name": "SMK 1 <img src=x onerror=alert(2) /> & Sons",
            "class_name": "XII & RPL > A",
            "professional_summary": "Testing <b>bold</b> and <unclosed tag & entities.",
        },
        "approved_skills": [
            {"name": "Skill <Special> & Test", "score": 90, "level": "Mahir & Juara"}
        ],
        "selected_portfolios": [
            {
                "title": "Proyek <script> Hack",
                "activity_type": "project & research",
                "activity_date": "2026-09-25",
                "professional_description": "Describing <a href='evil.com'>link</a> & entities.",
                "tags": ["<tag1>", "tag & 2"],
            }
        ],
        "content_digest": "abcdef1234567890abcdef1234567890",
    }

    # Must complete safely without xml.parsers.expat.ExpatError
    pdf_bytes = renderer.render(
        snapshot=malicious_snapshot,
        display_code="TLN-XSS1-TEST",
        verification_token="token_xss_safe_12345",
        issued_date="25 September 2026",
    )
    assert len(pdf_bytes) > 1000
