import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..core.database import AsyncSessionLocal
from ..db.models import StorageObjectModel


class StorageMetadataRepository:
    """
    Manages durable relational metadata for private object storage.
    Enforces tenant boundaries and ownership for all uploaded assets.
    """

    def __init__(self, session_factory: Optional[async_sessionmaker[AsyncSession]] = None):
        self.session_factory = session_factory or AsyncSessionLocal

    async def create_pending_upload(
        self,
        id: str,
        school_id: str,
        owner_user_id: str,
        provider: str,
        bucket: str,
        object_key: str,
        original_filename: str,
        content_type: str,
        declared_size: Optional[int] = None,
        checksum: Optional[str] = None,
    ) -> StorageObjectModel:
        async with self.session_factory() as session:
            model = StorageObjectModel(
                id=id,
                school_id=school_id,
                owner_user_id=owner_user_id,
                provider=provider,
                bucket=bucket,
                object_key=object_key,
                original_filename=original_filename,
                content_type=content_type,
                size_bytes=declared_size,
                checksum=checksum,
                status="pending",
                created_at=datetime.now(timezone.utc),
            )
            session.add(model)
            await session.commit()
            return model

    async def get_storage_object(
        self, id: str, school_id: str, owner_user_id: str
    ) -> Optional[StorageObjectModel]:
        """Tenant and owner scoped lookup."""
        async with self.session_factory() as session:
            stmt = select(StorageObjectModel).where(
                and_(
                    StorageObjectModel.id == id,
                    StorageObjectModel.school_id == school_id,
                    StorageObjectModel.owner_user_id == owner_user_id,
                    StorageObjectModel.deleted_at.is_(None),
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def complete_upload(
        self,
        id: str,
        school_id: str,
        owner_user_id: str,
        actual_size: int,
        detected_content_type: str,
        checksum: Optional[str] = None,
    ) -> Optional[StorageObjectModel]:
        """Transitions status from pending to available."""
        async with self.session_factory() as session:
            stmt = select(StorageObjectModel).where(
                and_(
                    StorageObjectModel.id == id,
                    StorageObjectModel.school_id == school_id,
                    StorageObjectModel.owner_user_id == owner_user_id,
                    StorageObjectModel.status == "pending",
                )
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                return None

            model.status = "available"
            model.size_bytes = actual_size
            model.content_type = detected_content_type
            if checksum:
                model.checksum = checksum
            await session.commit()
            return model

    async def quarantine_upload(self, id: str) -> bool:
        """Quarantines invalid, spoofed, or suspicious uploads."""
        async with self.session_factory() as session:
            stmt = (
                update(StorageObjectModel)
                .where(StorageObjectModel.id == id)
                .values(status="quarantined")
            )
            res = await session.execute(stmt)
            await session.commit()
            return res.rowcount > 0

    async def delete_upload(self, id: str, school_id: str, owner_user_id: str) -> Optional[str]:
        """Soft-deletes upload record and returns object_key for binary deletion."""
        async with self.session_factory() as session:
            stmt = select(StorageObjectModel).where(
                and_(
                    StorageObjectModel.id == id,
                    StorageObjectModel.school_id == school_id,
                    StorageObjectModel.owner_user_id == owner_user_id,
                )
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                return None

            object_key = model.object_key
            model.status = "deleted"
            model.deleted_at = datetime.now(timezone.utc)
            await session.commit()
            return object_key

    async def cleanup_stale_pending_uploads(self, older_than_seconds: int = 86400) -> List[str]:
        """Finds pending uploads older than TTL and marks them deleted, returning keys for blob purge."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=older_than_seconds)
        async with self.session_factory() as session:
            stmt = select(StorageObjectModel).where(
                and_(
                    StorageObjectModel.status == "pending",
                    StorageObjectModel.created_at < cutoff,
                )
            )
            result = await session.execute(stmt)
            stale_models = result.scalars().all()
            keys_to_purge = []
            for m in stale_models:
                m.status = "deleted"
                m.deleted_at = datetime.now(timezone.utc)
                keys_to_purge.append(m.object_key)
            await session.commit()
            return keys_to_purge
