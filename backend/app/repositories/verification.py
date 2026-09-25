import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

from sqlalchemy import select, update, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..core.database import AsyncSessionLocal
from ..db.models import VerificationRecordModel
from ..domain.enums import VerificationStatus


class VerificationRepository(ABC):
    @abstractmethod
    async def create_verification_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates an immutable verification record for an issued CV snapshot."""
        pass

    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> Optional[Dict[str, Any]]:
        """Finds verification record by HMAC digest of the public token."""
        pass

    @abstractmethod
    async def get_by_display_code(self, display_code: str) -> Optional[Dict[str, Any]]:
        """Finds verification record by human-readable display code."""
        pass

    @abstractmethod
    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Finds verification record by internal UUID."""
        pass

    @abstractmethod
    async def get_by_snapshot_id(self, cv_snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Finds verification record associated with a given snapshot."""
        pass

    @abstractmethod
    async def list_for_student(self, school_id: str, student_id: str) -> List[Dict[str, Any]]:
        """Lists all verification records issued for a given student."""
        pass

    @abstractmethod
    async def revoke_record(
        self, record_id: str, revoked_by_user_id: str, reason: str
    ) -> bool:
        """Revokes an issued verification record."""
        pass

    @abstractmethod
    async def revoke_by_snapshot_id(
        self, cv_snapshot_id: str, school_id: str, student_id: str, revoked_by_user_id: str, reason: str
    ) -> bool:
        """Revokes verification record for a snapshot by student owner."""
        pass


class PostgresVerificationRepository(VerificationRepository):
    def __init__(self, session_factory: Optional[async_sessionmaker[AsyncSession]] = None):
        self.session_factory = session_factory or AsyncSessionLocal

    def _model_to_dict(self, model: VerificationRecordModel) -> Dict[str, Any]:
        return {
            "id": model.id,
            "school_id": model.school_id,
            "student_id": model.student_id,
            "cv_snapshot_id": model.cv_snapshot_id,
            "token_hash": model.token_hash,
            "display_code": model.display_code,
            "snapshot_digest": model.snapshot_digest,
            "status": model.status,
            "issued_at": model.issued_at,
            "expires_at": model.expires_at,
            "revoked_at": model.revoked_at,
            "revoked_by_user_id": model.revoked_by_user_id,
            "revocation_reason": model.revocation_reason,
            "pdf_storage_object_id": model.pdf_storage_object_id,
            "created_at": model.created_at,
        }

    async def create_verification_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        async with self.session_factory() as session:
            model = VerificationRecordModel(
                id=record_data.get("id") or str(uuid.uuid4()),
                school_id=record_data["school_id"],
                student_id=record_data["student_id"],
                cv_snapshot_id=record_data["cv_snapshot_id"],
                token_hash=record_data["token_hash"],
                display_code=record_data["display_code"],
                snapshot_digest=record_data["snapshot_digest"],
                status=record_data.get("status", VerificationStatus.ACTIVE.value),
                issued_at=record_data.get("issued_at") or datetime.now(timezone.utc),
                expires_at=record_data.get("expires_at"),
                revoked_at=record_data.get("revoked_at"),
                revoked_by_user_id=record_data.get("revoked_by_user_id"),
                revocation_reason=record_data.get("revocation_reason"),
                pdf_storage_object_id=record_data.get("pdf_storage_object_id"),
                created_at=datetime.now(timezone.utc),
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._model_to_dict(model)

    async def get_by_token_hash(self, token_hash: str) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(VerificationRecordModel).where(VerificationRecordModel.token_hash == token_hash)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._model_to_dict(model) if model else None

    async def get_by_display_code(self, display_code: str) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(VerificationRecordModel).where(VerificationRecordModel.display_code == display_code)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._model_to_dict(model) if model else None

    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(VerificationRecordModel).where(VerificationRecordModel.id == record_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._model_to_dict(model) if model else None

    async def get_by_snapshot_id(self, cv_snapshot_id: str) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(VerificationRecordModel).where(VerificationRecordModel.cv_snapshot_id == cv_snapshot_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._model_to_dict(model) if model else None

    async def list_for_student(self, school_id: str, student_id: str) -> List[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = (
                select(VerificationRecordModel)
                .where(
                    and_(
                        VerificationRecordModel.school_id == school_id,
                        VerificationRecordModel.student_id == student_id,
                    )
                )
                .order_by(desc(VerificationRecordModel.issued_at))
            )
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._model_to_dict(m) for m in models]

    async def revoke_record(
        self, record_id: str, revoked_by_user_id: str, reason: str
    ) -> bool:
        async with self.session_factory() as session:
            now = datetime.now(timezone.utc)
            stmt = (
                update(VerificationRecordModel)
                .where(VerificationRecordModel.id == record_id)
                .values(
                    status=VerificationStatus.REVOKED.value,
                    revoked_at=now,
                    revoked_by_user_id=revoked_by_user_id,
                    revocation_reason=reason,
                )
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def revoke_by_snapshot_id(
        self, cv_snapshot_id: str, school_id: str, student_id: str, revoked_by_user_id: str, reason: str
    ) -> bool:
        async with self.session_factory() as session:
            now = datetime.now(timezone.utc)
            stmt = (
                update(VerificationRecordModel)
                .where(
                    and_(
                        VerificationRecordModel.cv_snapshot_id == cv_snapshot_id,
                        VerificationRecordModel.school_id == school_id,
                        VerificationRecordModel.student_id == student_id,
                    )
                )
                .values(
                    status=VerificationStatus.REVOKED.value,
                    revoked_at=now,
                    revoked_by_user_id=revoked_by_user_id,
                    revocation_reason=reason,
                )
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0


class InMemoryVerificationRepository(VerificationRepository):
    def __init__(self):
        self.records: Dict[str, Dict[str, Any]] = {}

    async def create_verification_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        rid = record_data.get("id") or str(uuid.uuid4())
        record = dict(record_data)
        record["id"] = rid
        record.setdefault("status", VerificationStatus.ACTIVE.value)
        record.setdefault("issued_at", datetime.now(timezone.utc))
        record.setdefault("created_at", datetime.now(timezone.utc))
        self.records[rid] = record
        return dict(record)

    async def get_by_token_hash(self, token_hash: str) -> Optional[Dict[str, Any]]:
        for r in self.records.values():
            if r.get("token_hash") == token_hash:
                return dict(r)
        return None

    async def get_by_display_code(self, display_code: str) -> Optional[Dict[str, Any]]:
        for r in self.records.values():
            if r.get("display_code") == display_code:
                return dict(r)
        return None

    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        r = self.records.get(record_id)
        return dict(r) if r else None

    async def get_by_snapshot_id(self, cv_snapshot_id: str) -> Optional[Dict[str, Any]]:
        for r in self.records.values():
            if r.get("cv_snapshot_id") == cv_snapshot_id:
                return dict(r)
        return None

    async def list_for_student(self, school_id: str, student_id: str) -> List[Dict[str, Any]]:
        matches = [
            dict(r)
            for r in self.records.values()
            if r.get("school_id") == school_id and r.get("student_id") == student_id
        ]
        matches.sort(
            key=lambda x: x.get("issued_at") or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return matches

    async def revoke_record(
        self, record_id: str, revoked_by_user_id: str, reason: str
    ) -> bool:
        r = self.records.get(record_id)
        if r:
            r["status"] = VerificationStatus.REVOKED.value
            r["revoked_at"] = datetime.now(timezone.utc)
            r["revoked_by_user_id"] = revoked_by_user_id
            r["revocation_reason"] = reason
            return True
        return False

    async def revoke_by_snapshot_id(
        self, cv_snapshot_id: str, school_id: str, student_id: str, revoked_by_user_id: str, reason: str
    ) -> bool:
        for r in self.records.values():
            if (
                r.get("cv_snapshot_id") == cv_snapshot_id
                and r.get("school_id") == school_id
                and r.get("student_id") == student_id
            ):
                r["status"] = VerificationStatus.REVOKED.value
                r["revoked_at"] = datetime.now(timezone.utc)
                r["revoked_by_user_id"] = revoked_by_user_id
                r["revocation_reason"] = reason
                return True
        return False


_global_verification_repo: Optional[VerificationRepository] = None

def get_verification_repository() -> VerificationRepository:
    global _global_verification_repo
    if _global_verification_repo is None:
        _global_verification_repo = PostgresVerificationRepository()
    return _global_verification_repo

def set_verification_repository(repo: VerificationRepository) -> None:
    global _global_verification_repo
    _global_verification_repo = repo
