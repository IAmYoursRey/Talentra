import os
import time
import uuid
import pytest
from urllib.parse import urlparse, parse_qs

from app.core.config import settings
from app.storage.base import (
    generate_safe_object_key,
    validate_upload_policy,
    ALLOWED_CONTENT_TYPES,
)
from app.storage.local import LocalObjectStorage
from app.storage.s3 import S3ObjectStorage


def test_safe_object_key_and_privacy_guarantee():
    """
    MANDATORY REQUIREMENT 6, 16, 51:
    - Object key must be internal-ID based.
    - Zero leakage: No NISN, NIP, NUPTK, or NPSN may appear in object key.
    - Original user filename is NOT the key.
    """
    school_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())
    portfolio_id = str(uuid.uuid4())
    user_filename = "Sertifikat_LKS_NISN_0071234321_Rahasia.pdf"

    safe_key = generate_safe_object_key(
        school_id=school_id,
        student_id=student_id,
        portfolio_id=portfolio_id,
        original_filename=user_filename,
    )

    # 1. Structure verification
    assert safe_key.startswith(f"schools/{school_id}/students/{student_id}/portfolio/{portfolio_id}/")
    assert safe_key.endswith(".pdf")

    # 2. Privacy verification: No NISN or original filename in path
    assert "0071234321" not in safe_key
    assert "Sertifikat_LKS" not in safe_key
    assert "Rahasia" not in safe_key

    # 3. Path traversal prevention in extension
    malicious_filename = "exploit.pdf/../../../etc/passwd"
    safe_key2 = generate_safe_object_key(
        school_id=school_id,
        student_id=student_id,
        portfolio_id=portfolio_id,
        original_filename=malicious_filename,
    )
    assert ".." not in safe_key2


def test_upload_policy_validation():
    """
    MANDATORY REQUIREMENT 32:
    - Allowed: application/pdf, image/jpeg, image/png, video/mp4
    - Size limits enforced: Image <= 5MB, PDF <= 15MB, Video <= 50MB
    """
    # Valid PDF
    validate_upload_policy(content_type="application/pdf", file_size_bytes=10 * 1024 * 1024)

    # PDF exceeding 15MB limit
    with pytest.raises(ValueError, match="15 MB"):
        validate_upload_policy(content_type="application/pdf", file_size_bytes=20 * 1024 * 1024)

    # Valid PNG image
    validate_upload_policy(content_type="image/png", file_size_bytes=3 * 1024 * 1024)

    # Image exceeding 5MB limit
    with pytest.raises(ValueError, match="5 MB"):
        validate_upload_policy(content_type="image/jpeg", file_size_bytes=6 * 1024 * 1024)

    # Valid Video
    validate_upload_policy(content_type="video/mp4", file_size_bytes=40 * 1024 * 1024)

    # Video exceeding 50MB limit
    with pytest.raises(ValueError, match="50 MB"):
        validate_upload_policy(content_type="video/mp4", file_size_bytes=60 * 1024 * 1024)

    # Disallowed MIME types
    with pytest.raises(ValueError, match="tidak diizinkan"):
        validate_upload_policy(content_type="application/x-msdownload", file_size_bytes=1024)

    with pytest.raises(ValueError, match="tidak diizinkan"):
        validate_upload_policy(content_type="text/html", file_size_bytes=1024)


def test_local_object_storage_lifecycle(tmp_path):
    """
    MANDATORY REQUIREMENT 51:
    Test LocalObjectStorage creation, signed download URL, head metadata, and deletion.
    """
    storage = LocalObjectStorage(base_directory=str(tmp_path))
    object_key = f"schools/sch-1/students/std-1/portfolio/port-1/{uuid.uuid4()}.pdf"
    content = b"%PDF-1.4 test certificate content for Talentra"
    content_type = "application/pdf"

    # 1. Initially object does not exist
    head_before = storage.head_object(object_key)
    assert head_before is None

    # 2. Upload/write object
    storage.write_object(object_key=object_key, data=content, content_type=content_type)

    # 3. Head object confirms presence and metadata
    head_after = storage.head_object(object_key)
    assert head_after is not None
    assert head_after["size_bytes"] == len(content)

    # 4. Generate signed download URL
    download_url = storage.create_download_url(object_key=object_key, expires_in_seconds=300)
    assert "/api/v1/storage/download" in download_url
    assert "sig=" in download_url

    # 5. Verify valid URL components
    parsed = urlparse(download_url)
    qs = parse_qs(parsed.query)
    key = qs["key"][0]
    expires = int(qs["expires"][0])
    sig = qs["sig"][0]
    assert storage.verify_signed_url("download", key, expires, sig) is True

    # 6. Tampered signature is rejected
    assert storage.verify_signed_url("download", key, expires, "tampered_signature") is False

    # 7. Expired signature is rejected
    assert storage.verify_signed_url("download", key, int(time.time()) - 10, sig) is False

    # 8. Delete object
    deleted = storage.delete_object(object_key)
    assert deleted is True

    # 9. Confirm deleted
    head_deleted = storage.head_object(object_key)
    assert head_deleted is None


def test_s3_object_storage_mocked_urls():
    """
    Tests S3ObjectStorage presigned URL generation and parameter passing.
    """
    storage = S3ObjectStorage(
        endpoint_url="http://localhost:9000",
        region_name="us-east-1",
        bucket_name="talentra-test-bucket",
        access_key_id="mock_key",
        secret_access_key="mock_secret",
    )
    object_key = f"schools/sch-uuid/students/std-uuid/portfolio/port-uuid/{uuid.uuid4()}.pdf"

    # Test presigned upload URL generation
    upload_url = storage.create_upload_url(
        object_key=object_key,
        content_type="application/pdf",
        expires_in_seconds=600,
    )
    assert upload_url is not None
    assert "talentra-test-bucket" in upload_url or "localhost:9000" in upload_url
    assert object_key in upload_url or "Key=" in upload_url

    # Test presigned download URL generation
    download_url = storage.create_download_url(
        object_key=object_key,
        expires_in_seconds=600,
    )
    assert download_url is not None
    assert "talentra-test-bucket" in download_url or "localhost:9000" in download_url
