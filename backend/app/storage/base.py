import re
import uuid
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ..core.config import settings


ALLOWED_CONTENT_TYPES = {
    "application/pdf": settings.max_pdf_upload_bytes,
    "image/jpeg": settings.max_image_upload_bytes,
    "image/png": settings.max_image_upload_bytes,
    "video/mp4": settings.max_video_upload_bytes,
}


def validate_upload_policy(
    content_type: str,
    size_bytes: Optional[int] = None,
    file_size_bytes: Optional[int] = None,
) -> None:
    """
    Validates MIME type against allowed formats and checks size limit.
    Phase 4 will enforce binary content header inspection.
    """
    cleaned_type = content_type.strip().lower()
    if cleaned_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(
            f"Tipe file '{content_type}' tidak diizinkan. "
            "Format yang diterima: PDF (dokumen), JPG/PNG (gambar), dan MP4 (video)."
        )

    effective_size = size_bytes if size_bytes is not None else file_size_bytes
    max_bytes = ALLOWED_CONTENT_TYPES[cleaned_type]
    if effective_size is not None and effective_size > max_bytes:
        max_mb = max_bytes // (1024 * 1024)
        raise ValueError(
            f"Ukuran file melebihi batas maksimal {max_mb} MB untuk tipe '{cleaned_type}'."
        )


def generate_safe_object_key(
    school_id: str,
    student_id: str,
    portfolio_id: str,
    extension: Optional[str] = None,
    original_filename: Optional[str] = None,
) -> str:
    """
    Generates an internal UUID-based object key.
    Strictly forbids national identifiers (NISN, NIP, NPSN) in the key path.
    """
    ext = extension
    if not ext and original_filename:
        # Extract extension safely
        import os
        _, ext = os.path.splitext(original_filename)
        ext = ext.lstrip(".")

    if not ext:
        ext = "bin"

    # Sanitize extension
    ext_clean = re.sub(r"[^a-zA-Z0-9]", "", ext).lower()
    if not ext_clean:
        ext_clean = "bin"

    random_blob_id = str(uuid.uuid4())
    return f"schools/{school_id}/students/{student_id}/portfolio/{portfolio_id}/{random_blob_id}.{ext_clean}"


def generate_safe_cv_pdf_key(school_id: str, student_id: str, snapshot_id: str) -> str:
    """
    Generates an internal UUID-based object key for CV PDF storage.
    Strictly forbids national identifiers or student names in the key path.
    """
    random_blob_id = str(uuid.uuid4())
    return f"schools/{school_id}/students/{student_id}/cv/{snapshot_id}/{random_blob_id}.pdf"


class ObjectStorage(ABC):
    """
    Provider-neutral storage abstraction supporting S3-compatible production
    and local filesystem development/testing.
    """
    @abstractmethod
    def create_upload_url(
        self,
        object_key: str,
        content_type: str,
        expires_in: Optional[int] = None,
    ) -> str:
        """Generates a short-lived presigned URL for direct client upload."""
        pass

    @abstractmethod
    def create_download_url(
        self,
        object_key: str,
        expires_in: Optional[int] = None,
    ) -> str:
        """Generates a short-lived presigned URL for private download."""
        pass

    @abstractmethod
    def head_object(self, object_key: str) -> Optional[Dict[str, Any]]:
        """Retrieves object metadata (size, content_type) if it exists."""
        pass

    @abstractmethod
    def delete_object(self, object_key: str) -> bool:
        """Deletes object from storage."""
        pass

    @abstractmethod
    def read_range(self, object_key: str, offset: int = 0, length: int = 4096) -> bytes:
        """Reads a byte slice from object for inspection without full memory buffering."""
        pass

    @abstractmethod
    def upload_object(self, object_key: str, data: Any, content_type: Optional[str] = None) -> str:
        """Uploads an object directly from binary stream or bytes."""
        pass

    @abstractmethod
    def object_exists(self, object_key: str) -> bool:
        """Checks if an object exists in storage."""
        pass

    @abstractmethod
    def get_object_bytes(self, object_key: str) -> bytes:
        """Retrieves full object bytes."""
        pass
