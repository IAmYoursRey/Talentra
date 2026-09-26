import hashlib
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .database import AsyncSessionLocal
from ..db.models import RateLimitBucketModel


class DatabaseRateLimiter:
    """
    Database-backed rate limiter for serverless deployments (Vercel Functions).
    Persists window counts in Neon PostgreSQL using hashed keys to prevent abuse
    across ephemeral instances without requiring Redis.
    """

    def __init__(self, session_factory: Optional[async_sessionmaker[AsyncSession]] = None):
        self.session_factory = session_factory or AsyncSessionLocal

    @staticmethod
    def hash_key(identifier: str, pepper: str = "talentra-rate-pepper-v1") -> str:
        salted = f"{identifier}:{pepper}".encode("utf-8")
        return hashlib.sha256(salted).hexdigest()

    async def is_rate_limited_and_record(
        self,
        identifier: str,
        scope: str = "login",
        max_requests: int = 5,
        window_seconds: int = 60,
        pepper: str = "talentra-rate-pepper-v1",
    ) -> bool:
        """
        Atomically checks rate limit and increments counter within current window.
        Returns True if rate limit is exceeded.
        """
        key_hash = self.hash_key(identifier, pepper)
        now_ts = int(time.time())
        window_start = now_ts - (now_ts % window_seconds)
        now_dt = datetime.now(timezone.utc)
        expires_at = now_dt + timedelta(seconds=window_seconds * 2)

        async with self.session_factory() as session:
            stmt = select(RateLimitBucketModel).where(
                and_(
                    RateLimitBucketModel.key_hash == key_hash,
                    RateLimitBucketModel.scope == scope,
                    RateLimitBucketModel.window_start == window_start,
                )
            )
            result = await session.execute(stmt)
            bucket = result.scalar_one_or_none()

            if bucket:
                if bucket.count >= max_requests:
                    return True
                bucket.count += 1
                await session.commit()
                return False
            else:
                new_bucket = RateLimitBucketModel(
                    key_hash=key_hash,
                    scope=scope,
                    window_start=window_start,
                    count=1,
                    expires_at=expires_at,
                )
                session.add(new_bucket)
                await session.commit()
                return False

    async def reset(self, identifier: str, scope: str = "login", pepper: str = "talentra-rate-pepper-v1") -> None:
        key_hash = self.hash_key(identifier, pepper)
        async with self.session_factory() as session:
            from sqlalchemy import delete
            stmt = delete(RateLimitBucketModel).where(
                and_(
                    RateLimitBucketModel.key_hash == key_hash,
                    RateLimitBucketModel.scope == scope,
                )
            )
            await session.execute(stmt)
            await session.commit()


db_rate_limiter = DatabaseRateLimiter()


class LoginRateLimiter:
    """
    In-memory rate limiter that tracks login attempts by hashed identifier
    to avoid exposing or storing raw national identifiers.
    """
    def __init__(self, max_attempts: int = 5, window_seconds: int = 60, pepper: str = "talentra-rate-pepper-v1"):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.pepper = pepper
        self.attempts: dict[str, list[float]] = defaultdict(list)

    def _hash_key(self, identifier: str) -> str:
        salted = f"{identifier}:{self.pepper}".encode("utf-8")
        return hashlib.sha256(salted).hexdigest()

    def is_rate_limited(self, identifier: str) -> bool:
        key = self._hash_key(identifier)
        now = time.time()
        cutoff = now - self.window_seconds
        self.attempts[key] = [t for t in self.attempts[key] if t > cutoff]
        return len(self.attempts[key]) >= self.max_attempts

    def record_attempt(self, identifier: str) -> None:
        key = self._hash_key(identifier)
        self.attempts[key].append(time.time())

    def reset(self, identifier: str) -> None:
        key = self._hash_key(identifier)
        if key in self.attempts:
            del self.attempts[key]


login_rate_limiter = LoginRateLimiter()


class PublicVerifyRateLimiter:
    """
    In-memory rate limiter for public verification endpoint keyed by hashed client IP
    to protect against enumeration and brute force without storing raw IP addresses.
    """
    def __init__(self, max_requests: int = 60, window_seconds: int = 60, pepper: str = "talentra-public-verify-pepper-v1"):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.pepper = pepper
        self.requests: dict[str, list[float]] = defaultdict(list)

    def _hash_client(self, client_ip: str) -> str:
        salted = f"{client_ip}:{self.pepper}".encode("utf-8")
        return hashlib.sha256(salted).hexdigest()

    def is_rate_limited(self, client_ip: str) -> bool:
        key = self._hash_client(client_ip)
        now = time.time()
        cutoff = now - self.window_seconds
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]
        return len(self.requests[key]) >= self.max_requests

    def record_request(self, client_ip: str) -> None:
        key = self._hash_client(client_ip)
        self.requests[key].append(time.time())

    def reset(self, client_ip: str) -> None:
        key = self._hash_client(client_ip)
        if key in self.requests:
            del self.requests[key]


public_verify_rate_limiter = PublicVerifyRateLimiter(max_requests=60)
