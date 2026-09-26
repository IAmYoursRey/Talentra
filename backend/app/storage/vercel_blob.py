import os
import time
import hmac
import hashlib
from typing import Optional, Dict, Any
import httpx

from .base import ObjectStorage
from ..core.config import settings, get_internal_app_origin


class VercelBlobStorage(ObjectStorage):
    """
    Vercel Blob storage adapter implementing private blob storage.
    Enforces access='private' by default for institutional student data and generated CVs.
    Uses official @vercel/blob Node broker (/api/blob/sign) to obtain narrow presigned URLs
    for PUT, GET, HEAD, and DELETE operations without proxying large binaries through functions.
    Static token fallback is preserved strictly for local/offline testing.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = "https://blob.vercel-storage.com",
        broker_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        # Static BLOB_READ_WRITE_TOKEN fallback for local/test environments
        self.token = token or os.getenv("BLOB_READ_WRITE_TOKEN") or getattr(settings, "blob_read_write_token", None) or ""
        self.base_url = base_url.rstrip("/")
        self.broker_url = (broker_url or get_internal_app_origin()).rstrip("/")
        self.timeout = timeout
        # Dedicated BLOB_BROKER_HMAC_SECRET strictly isolated from JWT_SECRET_KEY
        self.secret = (
            getattr(settings, "blob_broker_hmac_secret", None)
            or os.getenv("BLOB_BROKER_HMAC_SECRET")
            or "talentra-blob-broker-dev-secret-32-bytes-min"
        ).encode("utf-8")

    def _broker_sign(self, action: str, object_key: str, ttl: Optional[int] = None) -> tuple[int, str]:
        """
        Signs canonical payload for internal broker authorization:
        action|cleanPathname|expires
        """
        clean_path = object_key.lstrip("/")
        expires = int(time.time()) + (ttl or settings.blob_broker_token_ttl_seconds)
        sig_data = f"{action}|{clean_path}|{expires}".encode("utf-8")
        sig = hmac.new(self.secret, sig_data, hashlib.sha256).hexdigest()
        return expires, sig

    def _get_headers(self) -> Dict[str, str]:
        headers = {}
        if self.token:
            headers["authorization"] = f"Bearer {self.token}"
        return headers

    def _get_presigned_url(self, action: str, object_key: str, valid_until_ttl: Optional[int] = None) -> str:
        """
        Requests narrow, short-lived presigned URL from trusted Next.js Blob broker.
        """
        clean_path = object_key.lstrip("/")
        expires, sig = self._broker_sign(action, clean_path)
        internal_origin = get_internal_app_origin()
        endpoint = f"{internal_origin}/api/blob/sign"
        payload = {
            "action": action,
            "pathname": clean_path,
            "expires": expires,
            "sig": sig,
            "ttl": valid_until_ttl or settings.blob_download_url_ttl_seconds,
        }
        with httpx.Client(timeout=self.timeout) as client:
            res = client.post(endpoint, json=payload)
            if res.status_code == 200:
                data = res.json()
                return data["url"]
            res.raise_for_status()
            raise RuntimeError(f"Failed to obtain presigned Blob URL: {res.text}")

    def create_upload_url(
        self,
        object_key: str,
        content_type: str,
        expires_in: Optional[int] = None,
    ) -> str:
        """
        Returns client upload initiation URL.
        """
        clean_path = object_key.lstrip("/")
        ttl = expires_in if expires_in is not None else settings.presigned_url_ttl_seconds
        expiry = int(time.time()) + ttl
        sig_data = f"upload|{clean_path}|{expiry}".encode("utf-8")
        signature = hmac.new(self.secret, sig_data, hashlib.sha256).hexdigest()
        return f"/api/blob/upload?pathname={clean_path}&expires={expiry}&sig={signature}"

    def create_download_url(
        self,
        object_key: str,
        expires_in: Optional[int] = None,
    ) -> str:
        """
        Generates a short-lived signed download URL for private blob access.
        In production, obtains a signed GET URL directly from Vercel Blob via broker.
        """
        clean_path = object_key.lstrip("/")
        ttl = expires_in if expires_in is not None else settings.blob_download_url_ttl_seconds

        # Production broker flow: return direct presigned GET URL from Vercel Blob
        if not self.token or os.getenv("VERCEL_URL") or os.getenv("VERCEL"):
            try:
                return self._get_presigned_url("get", clean_path, valid_until_ttl=ttl)
            except Exception:
                pass

        # Static token / offline fallback
        expiry = int(time.time()) + ttl
        sig_data = f"blob_download|{clean_path}|{expiry}".encode("utf-8")
        signature = hmac.new(self.secret, sig_data, hashlib.sha256).hexdigest()
        return f"/api/v1/storage/download?key={clean_path}&expires={expiry}&sig={signature}"

    def verify_signed_url(self, action: str, object_key: str, expires: int, signature: str) -> bool:
        if int(time.time()) > expires:
            return False
        clean_path = object_key.lstrip("/")
        sig_data = f"{action}|{clean_path}|{expires}".encode("utf-8")
        expected_sig = hmac.new(self.secret, sig_data, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, signature)

    def head_object(self, object_key: str) -> Optional[Dict[str, Any]]:
        clean_path = object_key.lstrip("/")
        if self.token:
            url = f"{self.base_url}/{clean_path}"
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

        # Production: Request signed HEAD URL, call Blob directly
        try:
            signed_url = self._get_presigned_url("head", clean_path)
            with httpx.Client(timeout=self.timeout) as client:
                res = client.head(signed_url)
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
        Obtains signed GET URL from broker and queries Vercel Blob directly.
        """
        clean_path = object_key.lstrip("/")
        if self.token:
            url = f"{self.base_url}/{clean_path}"
            headers = self._get_headers()
            headers["range"] = f"bytes={offset}-{offset + length - 1}"
            headers["cache-control"] = "no-cache"
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(url, headers=headers)
                if res.status_code in (200, 206):
                    return res.content[:length]
                raise FileNotFoundError(f"Storage object '{object_key}' not found or inaccessible.")

        # Production: Request signed GET URL, read byte range directly from Blob
        try:
            signed_url = self._get_presigned_url("get", clean_path)
            headers = {
                "range": f"bytes={offset}-{offset + length - 1}",
                "cache-control": "no-cache",
            }
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(signed_url, headers=headers)
                if res.status_code in (200, 206):
                    return res.content[:length]
                raise FileNotFoundError(f"Storage object '{object_key}' not found via signed URL.")
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                raise
            raise FileNotFoundError(f"Storage object '{object_key}' range read failed: {str(e)}")

    def upload_object(self, object_key: str, data: Any, content_type: Optional[str] = None) -> str:
        """
        Uploads binary payload directly to private Vercel Blob.
        In production, obtains a signed PUT URL from broker, then PUTs binary directly to Blob.
        No PDF bytes traverse Node Route Handlers.
        """
        if hasattr(data, "read"):
            data = data.read()

        clean_path = object_key.lstrip("/")

        if self.token:
            url = f"{self.base_url}/{clean_path}"
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

        # Production: Obtain signed PUT URL from broker, then direct HTTP PUT to Blob
        presigned_put_url = self._get_presigned_url("put", clean_path)
        headers = {"content-type": content_type or "application/pdf"}
        with httpx.Client(timeout=self.timeout) as client:
            res = client.put(presigned_put_url, content=data, headers=headers)
            if res.status_code in (200, 201):
                return f"https://blob.vercel-storage.com/{clean_path}"
            res.raise_for_status()
            return f"https://blob.vercel-storage.com/{clean_path}"

    def delete_object(self, object_key: str) -> bool:
        clean_path = object_key.lstrip("/")
        if self.token:
            delete_url = f"{self.base_url}/delete"
            headers = self._get_headers()
            headers["content-type"] = "application/json"
            target_url = f"{self.base_url}/{clean_path}"
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    res = client.post(delete_url, json={"urls": [target_url]}, headers=headers)
                    return res.status_code in (200, 204)
            except Exception:
                return False

        # Production: Obtain signed DELETE URL from broker, then direct DELETE to Blob
        try:
            signed_delete_url = self._get_presigned_url("delete", clean_path)
            with httpx.Client(timeout=self.timeout) as client:
                res = client.delete(signed_delete_url)
                return res.status_code in (200, 204)
        except Exception:
            return False

    def get_object_bytes(self, object_key: str) -> bytes:
        clean_path = object_key.lstrip("/")
        if self.token:
            url = f"{self.base_url}/{clean_path}"
            headers = self._get_headers()
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(url, headers=headers)
                if res.status_code == 200:
                    return res.content
                raise FileNotFoundError(f"Storage object '{object_key}' not found.")

        # Production: Obtain signed GET URL, fetch bytes directly from Blob
        signed_get_url = self._get_presigned_url("get", clean_path)
        with httpx.Client(timeout=self.timeout) as client:
            res = client.get(signed_get_url)
            if res.status_code == 200:
                return res.content
            raise FileNotFoundError(f"Storage object '{object_key}' not found via signed URL.")
