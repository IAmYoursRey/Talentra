import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .database import AsyncSessionLocal
from ..db.models import IdempotencyKeyModel


class IdempotencyManager:
    def __init__(self, session_factory: Optional[async_sessionmaker[AsyncSession]] = None):
        self.session_factory = session_factory or AsyncSessionLocal

    @staticmethod
    def compute_key_hash(user_id: str, operation: str, client_key: str) -> str:
        data = f"{user_id}:{operation}:{client_key.strip()}".encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    async def get_cached_response(
        self, user_id: str, operation: str, client_key: str = "", key: Optional[str] = None
    ) -> Optional[Tuple[int, Dict[str, Any]]]:
        effective_key = key or client_key
        key_hash = self.compute_key_hash(user_id, operation, effective_key)
        now = datetime.now(timezone.utc)
        try:
            async with self.session_factory() as session:
                stmt = select(IdempotencyKeyModel).where(
                    IdempotencyKeyModel.key_hash == key_hash,
                    IdempotencyKeyModel.user_id == user_id,
                    IdempotencyKeyModel.operation == operation,
                    IdempotencyKeyModel.expires_at > now,
                )
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model and model.response_payload:
                    payload = json.loads(model.response_payload)
                    return model.status_code or 200, payload
        except Exception:
            pass
        return None

    async def store_response(
        self,
        user_id: str,
        operation: str,
        client_key: str = "",
        status_code: int = 200,
        response_dict: Optional[Dict[str, Any]] = None,
        key: Optional[str] = None,
        response_body: Optional[Dict[str, Any]] = None,
        ttl_seconds: int = 86400,
    ) -> None:
        effective_key = key or client_key
        effective_body = response_dict if response_dict is not None else (response_body or {})
        key_hash = self.compute_key_hash(user_id, operation, effective_key)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)
        try:
            async with self.session_factory() as session:
                model = IdempotencyKeyModel(
                    key_hash=key_hash,
                    user_id=user_id,
                    operation=operation,
                    status_code=status_code,
                    response_payload=json.dumps(response_dict, default=str),
                    expires_at=expires_at,
                    created_at=now,
                )
                session.add(model)
                await session.commit()
        except Exception:
            pass


idempotency_manager = IdempotencyManager()
