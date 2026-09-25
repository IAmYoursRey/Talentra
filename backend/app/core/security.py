import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from .config import settings
from ..domain.enums import UserRole

# 1. Argon2id Password Hasher
ph = PasswordHasher(
    time_cost=2,
    memory_cost=19456,  # 19 MiB
    parallelism=1,
    hash_len=32,
    salt_len=16,
)

def hash_password(password: str) -> str:
    """Hash password using Argon2id with recommended parameters."""
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against stored Argon2id hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False

# 2. JWT Encoding & Verification
def create_access_token(
    user_id: str,
    school_id: str,
    role: UserRole,
    session_id: str,
    expires_delta: timedelta | None = None,
) -> tuple[str, datetime]:
    """
    Creates minimal JWT access token containing ONLY authorization claims:
    sub = user_id
    sid = session_id
    school_id = school_id
    role = role.value
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload: dict[str, Any] = {
        "sub": user_id,
        "sid": session_id,
        "school_id": school_id,
        "role": role.value,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, expire

def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decodes and validates JWT against signature, algorithm, expiration, issuer, and audience.
    Allowed algorithm is strictly server-enforced (HS256).
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "sid", "school_id", "role", "exp", "iat", "iss", "aud"]},
        )
        return payload
    except jwt.PyJWTError as e:
        raise ValueError(f"Invalid or expired token: {str(e)}") from e

# 3. Privacy-Preserving Identifier Lookup & Token Hashing
import hmac
import hashlib
import secrets

def compute_identifier_lookup_hash(normalized_identifier: str) -> str:
    """
    Computes keyed HMAC-SHA256 digest of normalized login identifier with server pepper.
    Enables database lookup without storing or leaking raw NISN/NIP/NPSN.
    """
    key = settings.identifier_lookup_pepper.encode("utf-8")
    data = normalized_identifier.strip().encode("utf-8")
    return hmac.new(key, data, hashlib.sha256).hexdigest()

def generate_refresh_token() -> str:
    """Generates high-entropy random string for refresh token."""
    return secrets.token_urlsafe(48)

def hash_token(token: str) -> str:
    """Computes SHA-256 hash of a token for secure database storage."""
    return hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
