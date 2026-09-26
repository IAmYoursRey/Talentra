import os
import time
import pytest
from unittest.mock import patch, MagicMock
from backend.app.storage.vercel_blob import VercelBlobStorage
from backend.app.core.config import settings, get_internal_app_origin


def test_vercel_blob_auth_preference(monkeypatch):
    monkeypatch.delenv("BLOB_READ_WRITE_TOKEN", raising=False)
    storage_prod = VercelBlobStorage()
    assert storage_prod.token == ""

    monkeypatch.setenv("BLOB_READ_WRITE_TOKEN", "static-token-val")
    storage_fallback = VercelBlobStorage()
    assert storage_fallback.token == "static-token-val"


def test_secret_separation_jwt_vs_broker(monkeypatch):
    """
    Test 39: Changing JWT_SECRET_KEY does NOT change Blob broker signature behavior
    when BLOB_BROKER_HMAC_SECRET is unchanged, and changing broker secret invalidates old tokens.
    """
    broker_secret = "a" * 32
    monkeypatch.setattr(settings, "blob_broker_hmac_secret", broker_secret)
    monkeypatch.setattr(settings, "jwt_secret_key", "jwt_secret_initial_32_characters_long")

    storage1 = VercelBlobStorage()
    expires, sig1 = storage1._broker_sign("get", "schools/1/evidence/test.pdf")

    # Change JWT_SECRET_KEY
    monkeypatch.setattr(settings, "jwt_secret_key", "jwt_secret_changed_32_characters_long!")
    storage2 = VercelBlobStorage()
    expires2, sig2 = storage2._broker_sign("get", "schools/1/evidence/test.pdf")

    # Signatures must be identical because they use BLOB_BROKER_HMAC_SECRET, not JWT_SECRET_KEY
    assert sig1 == sig2
    assert storage2.verify_signed_url("get", "schools/1/evidence/test.pdf", expires, sig1) is True

    # Changing BLOB_BROKER_HMAC_SECRET invalidates old signatures
    monkeypatch.setattr(settings, "blob_broker_hmac_secret", "b" * 32)
    storage3 = VercelBlobStorage()
    assert storage3.verify_signed_url("get", "schools/1/evidence/test.pdf", expires, sig1) is False


def test_cross_operation_replay(monkeypatch):
    """
    Test 40: GET-signed internal token cannot authorize DELETE or PUT.
    """
    monkeypatch.setattr(settings, "blob_broker_hmac_secret", "c" * 32)
    storage = VercelBlobStorage()
    expires, get_sig = storage._broker_sign("get", "evidence/file.pdf")

    # GET succeeds
    assert storage.verify_signed_url("get", "evidence/file.pdf", expires, get_sig) is True

    # Same token for DELETE must fail
    assert storage.verify_signed_url("delete", "evidence/file.pdf", expires, get_sig) is False

    # Same token for PUT must fail
    assert storage.verify_signed_url("put", "evidence/file.pdf", expires, get_sig) is False


def test_cross_path_replay(monkeypatch):
    """
    Test 41: Token for path A cannot access path B.
    """
    monkeypatch.setattr(settings, "blob_broker_hmac_secret", "d" * 32)
    storage = VercelBlobStorage()
    expires, path_a_sig = storage._broker_sign("get", "evidence/path_a.pdf")

    assert storage.verify_signed_url("get", "evidence/path_a.pdf", expires, path_a_sig) is True
    assert storage.verify_signed_url("get", "evidence/path_b.pdf", expires, path_a_sig) is False


def test_expiration_rejection(monkeypatch):
    """
    Test 42: Expired broker token is strictly denied.
    """
    monkeypatch.setattr(settings, "blob_broker_hmac_secret", "e" * 32)
    storage = VercelBlobStorage()
    past_time = int(time.time()) - 10
    expires, sig = storage._broker_sign("get", "evidence/file.pdf", ttl=-10)

    assert storage.verify_signed_url("get", "evidence/file.pdf", expires, sig) is False


def test_direct_signed_put_cv_upload(monkeypatch):
    """
    Test 44: CV storage architecture: FastAPI requests presigned PUT from /api/blob/sign
    and performs direct HTTP PUT to that signed URL. PDF bytes do NOT pass through /api/blob/cv-put.
    """
    monkeypatch.setattr(settings, "blob_broker_hmac_secret", "f" * 32)
    storage = VercelBlobStorage(token="")  # Production mode without static token

    presigned_put_target = "https://blob.vercel-storage.com/cv/sch-1/cv-123.pdf?presigned_token=abc"

    with patch("httpx.Client.post") as mock_sign_post, patch("httpx.Client.put") as mock_blob_put:
        # Mock broker sign response
        sign_resp = MagicMock()
        sign_resp.status_code = 200
        sign_resp.json.return_value = {"url": presigned_put_target, "validUntil": int(time.time()) + 300}
        mock_sign_post.return_value = sign_resp

        # Mock direct Blob PUT response
        blob_resp = MagicMock()
        blob_resp.status_code = 200
        mock_blob_put.return_value = blob_resp

        cv_pdf_bytes = b"%PDF-1.4 reportlab generated test cv"
        result_url = storage.upload_object("cv/sch-1/cv-123.pdf", cv_pdf_bytes, "application/pdf")

        # 1. Verify broker /api/blob/sign was called with metadata only (no PDF bytes)
        assert mock_sign_post.call_count == 1
        sign_call_args, sign_call_kwargs = mock_sign_post.call_args
        assert "/api/blob/sign" in sign_call_args[0]
        sign_payload = sign_call_kwargs.get("json", {})
        assert sign_payload.get("action") == "put"
        assert sign_payload.get("pathname") == "cv/sch-1/cv-123.pdf"
        assert "content" not in sign_call_kwargs  # Zero bytes to broker

        # 2. Verify direct PUT was performed to presigned_put_target with the PDF bytes
        assert mock_blob_put.call_count == 1
        blob_call_args, blob_call_kwargs = mock_blob_put.call_args
        assert blob_call_args[0] == presigned_put_target
        assert blob_call_kwargs.get("content") == cv_pdf_bytes
        assert blob_call_kwargs.get("headers", {}).get("content-type") == "application/pdf"


def test_direct_signed_get_read_range(monkeypatch):
    """
    Test 43/46: Post-upload validation reads byte range directly from Blob presigned GET URL,
    not proxied through Node.
    """
    monkeypatch.setattr(settings, "blob_broker_hmac_secret", "g" * 32)
    storage = VercelBlobStorage(token="")

    presigned_get_target = "https://blob.vercel-storage.com/evidence/doc.pdf?presigned_token=xyz"

    with patch("httpx.Client.post") as mock_sign_post, patch("httpx.Client.get") as mock_blob_get:
        sign_resp = MagicMock()
        sign_resp.status_code = 200
        sign_resp.json.return_value = {"url": presigned_get_target, "validUntil": int(time.time()) + 300}
        mock_sign_post.return_value = sign_resp

        blob_resp = MagicMock()
        blob_resp.status_code = 206
        blob_resp.content = b"%PDF-1.4 header bytes"
        mock_blob_get.return_value = blob_resp

        magic = storage.read_range("evidence/doc.pdf", offset=0, length=8)
        assert magic == b"%PDF-1.4"

        # Verify broker sign called for "get"
        assert mock_sign_post.call_count == 1
        assert "/api/blob/sign" in mock_sign_post.call_args[0][0]

        # Verify direct range GET on Blob URL
        assert mock_blob_get.call_count == 1
        assert mock_blob_get.call_args[0][0] == presigned_get_target
        headers = mock_blob_get.call_args[1].get("headers", {})
        assert headers.get("range") == "bytes=0-7"


def test_direct_download_url_generation(monkeypatch):
    """
    Test 43: create_download_url returns direct presigned GET URL.
    """
    monkeypatch.setattr(settings, "blob_broker_hmac_secret", "h" * 32)
    storage = VercelBlobStorage(token="")

    presigned_url = "https://blob.vercel-storage.com/evidence/doc.pdf?signed_get=1"

    with patch("httpx.Client.post") as mock_sign_post:
        sign_resp = MagicMock()
        sign_resp.status_code = 200
        sign_resp.json.return_value = {"url": presigned_url, "validUntil": int(time.time()) + 300}
        mock_sign_post.return_value = sign_resp

        url = storage.create_download_url("evidence/doc.pdf", expires_in=300)
        assert url == presigned_url


def test_ssrf_protection_origin_resolver(monkeypatch):
    """
    Test 33/34: Internal app origin strictly resolves from trusted environment, never client input.
    """
    monkeypatch.delenv("VERCEL_URL", raising=False)
    monkeypatch.setenv("INTERNAL_APP_URL", "http://127.0.0.1:3000")
    assert get_internal_app_origin() == "http://127.0.0.1:3000"

    monkeypatch.setenv("VERCEL_URL", "talentra-preview.vercel.app")
    assert get_internal_app_origin() == "https://talentra-preview.vercel.app"
