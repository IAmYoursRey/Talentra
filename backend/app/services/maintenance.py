import logging
from typing import List, Optional
from ..repositories.storage_metadata import StorageMetadataRepository
from ..storage import get_object_storage
from ..storage.base import ObjectStorage
from ..core.audit import audit_logger
from ..domain.enums import AuditEventType

logger = logging.getLogger(__name__)


async def cleanup_stale_uploads(
    older_than_seconds: int = 86400,
    storage_meta_repo: Optional[StorageMetadataRepository] = None,
    object_storage: Optional[ObjectStorage] = None,
) -> List[str]:
    """
    Deterministic maintenance task:
    1. Finds pending storage_objects rows older than TTL.
    2. Marks them as deleted in PostgreSQL.
    3. Purges corresponding binary blobs from ObjectStorage if present.
    4. Records safe audit entry without sensitive metadata.
    """
    repo = storage_meta_repo or StorageMetadataRepository()
    storage = object_storage or get_object_storage()

    keys_to_purge = await repo.cleanup_stale_pending_uploads(older_than_seconds=older_than_seconds)
    purged_keys: List[str] = []

    for key in keys_to_purge:
        try:
            if storage.object_exists(key):
                storage.delete_object(key)
            purged_keys.append(key)
        except Exception as e:
            logger.warning(f"Failed to delete stale storage object blob {key}: {e}")

    if purged_keys:
        audit_logger.log(
            event_type=AuditEventType.EVIDENCE_DELETED,
            safe_context=f"Cleaned up {len(purged_keys)} stale uncompleted upload(s)",
            metadata={"purged_count": len(purged_keys)},
        )

    return purged_keys
