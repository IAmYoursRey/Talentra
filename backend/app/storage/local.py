import os
import time
import hmac
import hashlib
from typing import Optional, Dict, Any
from .base import ObjectStorage
from ..core.config import settings


class LocalObjectStorage(ObjectStorage):
    """
    Local filesystem storage adapter for development and testing.
    Simulates presigned upload/download URLs using signed tokens.
    """
    def __init__(self, base_dir: Optional[str] = None, base_directory: Optional[str] = None):
        target_dir = base_dir or base_directory or settings.local_storage_path
        self.base_dir = os.path.abspath(target_dir)
        os.makedirs(self.base_dir, exist_ok=True)
        self.secret = settings.jwt_secret_key.encode("utf-8")

    def _get_full_path(self, object_key: str) -> str:
        # Prevent directory traversal attacks
        clean_key = os.path.normpath(object_key).lstrip(r"\/")
        full_path = os.path.join(self.base_dir, clean_key)
        if not full_path.startswith(self.base_dir):
            raise ValueError("Invalid storage key path traversal attempt.")
        return full_path

    def _sign_url(self, action: str, object_key: str, expires_in: int) -> str:
        expiry = int(time.time()) + expires_in
        sig_data = f"{action}:{object_key}:{expiry}".encode("utf-8")
        signature = hmac.new(self.secret, sig_data, hashlib.sha256).hexdigest()
        return f"/api/v1/storage/{action}?key={object_key}&expires={expiry}&sig={signature}"

    def create_upload_url(
        self,
        object_key: str,
        content_type: str,
        expires_in: Optional[int] = None,
        expires_in_seconds: Optional[int] = None,
    ) -> str:
        ttl = expires_in if expires_in is not None else (expires_in_seconds or settings.presigned_url_ttl_seconds)
        return self._sign_url("upload", object_key, ttl)

    def create_download_url(
        self,
        object_key: str,
        expires_in: Optional[int] = None,
        expires_in_seconds: Optional[int] = None,
    ) -> str:
        ttl = expires_in if expires_in is not None else (expires_in_seconds or settings.presigned_url_ttl_seconds)
        return self._sign_url("download", object_key, ttl)

    def verify_signed_url(self, action: str, object_key: str, expires: int, signature: str) -> bool:
        if int(time.time()) > expires:
            return False
        sig_data = f"{action}:{object_key}:{expires}".encode("utf-8")
        expected_sig = hmac.new(self.secret, sig_data, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, signature)

    def head_object(self, object_key: str) -> Optional[Dict[str, Any]]:
        path = self._get_full_path(object_key)
        if not os.path.exists(path):
            return None
        stat = os.stat(path)
        return {
            "size_bytes": stat.st_size,
            "modified_at": stat.st_mtime,
        }

    def delete_object(self, object_key: str) -> bool:
        path = self._get_full_path(object_key)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except OSError:
                return False
        return False

    def write_bytes(self, object_key: str, data: bytes) -> str:
        """Helper for test suites to simulate uploaded bytes."""
        path = self._get_full_path(object_key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return path

    def write_object(self, object_key: str, data: bytes, content_type: Optional[str] = None) -> str:
        return self.write_bytes(object_key, data)

    def read_range(self, object_key: str, offset: int = 0, length: int = 4096) -> bytes:
        path = self._get_full_path(object_key)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Storage object '{object_key}' not found.")
        with open(path, "rb") as f:
            f.seek(offset)
            return f.read(length)

    def upload_object(self, object_key: str, data: Any, content_type: Optional[str] = None) -> str:
        if hasattr(data, "read"):
            data_bytes = data.read()
        elif isinstance(data, (bytes, bytearray)):
            data_bytes = bytes(data)
        else:
            data_bytes = str(data).encode("utf-8")
        return self.write_bytes(object_key, data_bytes)

    def object_exists(self, object_key: str) -> bool:
        path = self._get_full_path(object_key)
        return os.path.exists(path)

    def get_object_bytes(self, object_key: str) -> bytes:
        path = self._get_full_path(object_key)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Storage object '{object_key}' not found.")
        with open(path, "rb") as f:
            return f.read()

