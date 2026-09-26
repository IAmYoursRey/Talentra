import os
import time
import hmac
import hashlib
from typing import Optional, Dict, Any
import httpx

from .base import ObjectStorage
from ..core.config import settings


class VercelBlobStorage(ObjectStorage):
    """
    Vercel Blob storage adapter implementing private blob storage.
    Enforces access='private' by default for institutional student data and generated CVs.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = "https://blob.vercel-storage.com",
        timeout: float = 30.0,
    ):
        self.token = token or os.getenv("BLOB_READ_WRITE_TOKEN") or ""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.secret = (settings.jwt_secret_key or "talentra-storage-secret").encode("utf-8")

    def _get_headers(self) -> Dict[str, str]:
        headers = {}
        if self.token:
            headers["authorization"] = f"Bearer {self.token}"
        return headers

    def create_upload_url(
        self,
        object_key: str,
        content_type: str,
        expires_in: Optional[int] = None,
    ) -> str:
        """
        Directs client upload through authorized Vercel Blob client handler route.
        """
        ttl = expires_in if expires_in is not None else settings.presigned_url_ttl_seconds
        expiry = int(time.time()) + ttl
        sig_data = f"blob_upload:{object_key}:{expiry}".encode("utf-8")
        signature = hmac.new(self.secret, sig_data, hashlib.sha256).hexdigest()
        return f"/api/blob/upload?pathname={object_key}&expires={expiry}&sig={signature}"

    def create_download_url(
        self,
        object_key: str,
        expires_in: Optional[int] = None,
    ) -> str:
        """
        Generates a short-lived signed download URL for private blob access.
        """
        ttl = expires_in if expires_in is not None else settings.presigned_url_ttl_seconds
        expiry = int(time.time()) + ttl
        sig_data = f"blob_download:{object_key}:{expiry}".encode("utf-8")
        signature = hmac.new(self.secret, sig_data, hashlib.sha256).hexdigest()
        return f"/api/v1/storage/download?key={object_key}&expires={expiry}&sig={signature}"

    def verify_signed_url(self, action: str, object_key: str, expires: int, signature: str) -> bool:
        if int(time.time()) > expires:
            return False
        sig_data = f"{action}:{object_key}:{expires}".encode("utf-8")
        expected_sig = hmac.new(self.secret, sig_data, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, signature)

    def head_object(self, object_key: str) -> Optional[Dict[str, Any]]:
        if not self.token:
            return None
        url = f"{self.base_url}/{object_key.lstrip('/')}"
        headers = self._get_headers()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.head(url, headers=headers)
                if res.status_code == 200:
                    return {
                        "size_bytes": int(res.headers.get("content-length", 0)),
                        "content_type": res.headers.get("content-type", "application/octet-stream"),
                    }
                return None
        except Exception:
            return None

    def object_exists(self, object_key: str) -> bool:
        return self.head_object(object_key) is not None

    def read_range(self, object_key: str, offset: int = 0, length: int = 4096) -> bytes:
        """
        Reads byte slice using HTTP Range header without full buffering.
        Ideal for inspecting magic bytes / file signatures on large files.
        """
        if not self.token:
            raise RuntimeError("Vercel Blob token not configured.")
        url = f"{self.base_url}/{object_key.lstrip('/')}"
        headers = self._get_headers()
        headers["range"] = f"bytes={offset}-{offset + length - 1}"
        with httpx.Client(timeout=self.timeout) as client:
            res = client.get(url, headers=headers)
            if res.status_code in (200, 206):
                return res.content[:length]
            raise FileNotFoundError(f"Storage object '{object_key}' not found or inaccessible.")

    def upload_object(self, object_key: str, data: Any, content_type: Optional[str] = None) -> str:
        """
        Uploads binary payload directly to private Vercel Blob.
        Used for small in-memory operations like ReportLab CV PDF generation.
        """
        if not self.token:
            raise RuntimeError("Vercel Blob token not configured.")
        
        # Convert stream to bytes if needed
        if hasattr(data, "read"):
            data = data.read()

        url = f"{self.base_url}/{object_key.lstrip('/')}"
        headers = self._get_headers()
        headers["x-access"] = "private"
        headers["x-add-random-suffix"] = "false"
        if content_type:
            headers["content-type"] = content_type

        with httpx.Client(timeout=self.timeout) as client:
            res = client.put(url, content=data, headers=headers)
            if res.status_code in (200, 201):
                payload = res.json()
                return payload.get("url", url)
            res.raise_for_status()
            return url

    def delete_object(self, object_key: str) -> bool:
        if not self.token:
            return False
        delete_url = f"{self.base_url}/delete"
        headers = self._get_headers()
        headers["content-type"] = "application/json"
        target_url = f"{self.base_url}/{object_key.lstrip('/')}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(delete_url, json={"urls": [target_url]}, headers=headers)
                return res.status_code in (200, 204)
        except Exception:
            return False

    def get_object_bytes(self, object_key: str) -> bytes:
        if not self.token:
            raise RuntimeError("Vercel Blob token not configured.")
        url = f"{self.base_url}/{object_key.lstrip('/')}"
        headers = self._get_headers()
        with httpx.Client(timeout=self.timeout) as client:
            res = client.get(url, headers=headers)
            if res.status_code == 200:
                return res.content
            raise FileNotFoundError(f"Storage object '{object_key}' not found.")
