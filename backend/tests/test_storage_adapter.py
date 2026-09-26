import os
import time
import pytest
from unittest.mock import patch, MagicMock
from backend.app.storage.vercel_blob import VercelBlobStorage


def test_vercel_blob_auth_preference(monkeypatch):
    monkeypatch.delenv("BLOB_READ_WRITE_TOKEN", raising=False)
    storage_prod = VercelBlobStorage()
    # In production without static token, storage.token is empty and operations delegate to Node broker
    assert storage_prod.token == ""

    monkeypatch.setenv("BLOB_READ_WRITE_TOKEN", "static-token-val")
    storage_fallback = VercelBlobStorage()
    assert storage_fallback.token == "static-token-val"


def test_vercel_blob_broker_inspection_mock():
    storage = VercelBlobStorage(token="")  # No static token, forces broker route
    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        import base64
        mock_resp.json.return_value = {
            "size": 1024,
            "contentType": "application/pdf",
            "magicBytesBase64": base64.b64encode(b"%PDF-1.4").decode("ascii"),
        }
        mock_post.return_value = mock_resp

        head_info = storage.head_object("evidence/doc.pdf")
        assert head_info["size_bytes"] == 1024
        assert head_info["content_type"] == "application/pdf"

        magic = storage.read_range("evidence/doc.pdf", offset=0, length=8)
        assert magic == b"%PDF-1.4"


def test_signed_url_scopes_and_verification():
    storage = VercelBlobStorage(token="test-token")
    object_key = "schools/sch-1/evidence/test-file.pdf"

    # Upload URL
    upload_url = storage.create_upload_url(object_key, "application/pdf", expires_in=60)
    assert "/api/blob/upload" in upload_url
    assert f"pathname={object_key}" in upload_url

    # Download URL
    download_url = storage.create_download_url(object_key, expires_in=60)
    assert "/api/v1/storage/download" in download_url
    assert f"key={object_key}" in download_url

    # Verify signature extraction and validation
    import urllib.parse
    parsed = urllib.parse.urlparse(download_url)
    params = urllib.parse.parse_qs(parsed.query)
    expires = int(params["expires"][0])
    sig = params["sig"][0]

    # Valid check
    assert storage.verify_signed_url("blob_download", object_key, expires, sig) is True

    # Tampered action fails
    assert storage.verify_signed_url("wrong_action", object_key, expires, sig) is False

    # Tampered key fails
    assert storage.verify_signed_url("blob_download", "other/path.pdf", expires, sig) is False

    # Expired check fails
    expired_time = int(time.time()) - 10
    assert storage.verify_signed_url("blob_download", object_key, expired_time, sig) is False


def test_read_range_consistent_headers():
    storage = VercelBlobStorage(token="mock-token")
    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 206
        mock_resp.content = b"%PDF-1.4 header bytes"
        mock_get.return_value = mock_resp

        result = storage.read_range("evidence/doc.pdf", offset=0, length=8)
        assert result == b"%PDF-1.4"
        
        args, kwargs = mock_get.call_args
        headers = kwargs.get("headers", {})
        assert headers.get("range") == "bytes=0-7"
        assert headers.get("cache-control") == "no-cache"
        assert headers.get("pragma") == "no-cache"


def test_upload_object_private_headers():
    storage = VercelBlobStorage(token="mock-token")
    with patch("httpx.Client.put") as mock_put:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"url": "https://blob.vercel-storage.com/evidence/doc.pdf"}
        mock_put.return_value = mock_resp

        url = storage.upload_object("evidence/doc.pdf", b"pdf content", "application/pdf")
        assert url == "https://blob.vercel-storage.com/evidence/doc.pdf"

        args, kwargs = mock_put.call_args
        headers = kwargs.get("headers", {})
        assert headers.get("x-access") == "private"
        assert headers.get("content-type") == "application/pdf"
