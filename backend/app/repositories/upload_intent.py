import uuid
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..core.database import AsyncSessionLocal
from ..db.models import BlobUploadIntentModel


class BlobUploadIntentRepository:
    def __init__(self, session_factory: Optional[async_sessionmaker[AsyncSession]] = None):
        self.session_factory = session_factory or AsyncSessionLocal

    @staticmethod
    def hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    async def create_intent(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
        pathname: str,
        expected_content_type: str,
        max_bytes: int,
        ttl_seconds: int = 900,
    ) -> Tuple[BlobUploadIntentModel, str]:
        raw_token = secrets.token_urlsafe(32)
        token_hash = self.hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

        async with self.session_factory() as session:
            intent = BlobUploadIntentModel(
                id=str(uuid.uuid4()),
                token_hash=token_hash,
                school_id=school_id,
                student_id=student_id,
                portfolio_id=portfolio_id,
                pathname=pathname,
                expected_content_type=expected_content_type,
                max_bytes=max_bytes,
                expires_at=expires_at,
                status="pending",
                created_at=datetime.now(timezone.utc),
            )
            session.add(intent)
            await session.commit()
            return intent, raw_token

    async def get_valid_intent(self, raw_token: str) -> Optional[BlobUploadIntentModel]:
        token_hash = self.hash_token(raw_token)
        now = datetime.now(timezone.utc)
        async with self.session_factory() as session:
            stmt = select(BlobUploadIntentModel).where(
                and_(
                    BlobUploadIntentModel.token_hash == token_hash,
                    BlobUploadIntentModel.status == "pending",
                    BlobUploadIntentModel.expires_at > now,
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def consume_intent(self, raw_token: str) -> Optional[BlobUploadIntentModel]:
        token_hash = self.hash_token(raw_token)
        now = datetime.now(timezone.utc)
        async with self.session_factory() as session:
            stmt = (
                update(BlobUploadIntentModel)
                .where(
                    and_(
                        BlobUploadIntentModel.token_hash == token_hash,
                        BlobUploadIntentModel.status == "pending",
                        BlobUploadIntentModel.expires_at > now,
                    )
                )
                .values(status="consumed", consumed_at=now)
                .returning(BlobUploadIntentModel)
            )
            result = await session.execute(stmt)
            intent = result.scalar_one_or_none()
            if not intent:
                return None
            await session.commit()
            return intent
