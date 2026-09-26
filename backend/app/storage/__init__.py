from .base import ObjectStorage, validate_upload_policy, generate_safe_object_key, generate_safe_cv_pdf_key
from .local import LocalObjectStorage
from .s3 import S3ObjectStorage
from .vercel_blob import VercelBlobStorage
from ..core.config import settings

def get_object_storage() -> ObjectStorage:
    if settings.object_storage_provider == "vercel_blob":
        return VercelBlobStorage()
    elif settings.object_storage_provider == "s3":
        return S3ObjectStorage()
    return LocalObjectStorage()

__all__ = [
    "ObjectStorage",
    "LocalObjectStorage",
    "S3ObjectStorage",
    "VercelBlobStorage",
    "get_object_storage",
    "validate_upload_policy",
    "generate_safe_object_key",
    "generate_safe_cv_pdf_key",
]
