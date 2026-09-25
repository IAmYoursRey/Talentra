from datetime import timedelta
import pytest
import jwt
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.rate_limiter import LoginRateLimiter
from app.core.csrf import generate_csrf_token, validate_csrf_tokens
from app.core.config import settings
from app.domain.enums import UserRole


def test_argon2id_hashing_and_verification():
    plain = "SiswaSuperDemo2026!"
    hashed = hash_password(plain)

    # Must be valid Argon2id hash string starting with $argon2id$
    assert hashed.startswith("$argon2id$")
    assert hashed != plain

    # Successful verification
    assert verify_password(plain, hashed) is True

    # Failed verification
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False


def test_jwt_create_and_decode_valid():
    user_id = "11111111-1111-1111-1111-111111111111"
    school_id = "99999999-9999-9999-9999-999999999999"
    session_id = "sess-12345"

    token, expire = create_access_token(
        user_id=user_id,
        school_id=school_id,
        role=UserRole.STUDENT,
        session_id=session_id,
    )

    assert isinstance(token, str)
    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert payload["sid"] == session_id
    assert payload["school_id"] == school_id
    assert payload["role"] == "student"
    assert payload["iss"] == settings.jwt_issuer
    assert payload["aud"] == settings.jwt_audience

    # Ensure no sensitive full identifiers are leaked in JWT payload
    for key in ["nisn", "nuptk", "nip", "npsn", "password", "email"]:
        assert key not in payload


def test_jwt_tampered_signature_rejected():
    token, _ = create_access_token(
        user_id="11111111-1111-1111-1111-111111111111",
        school_id="99999999-9999-9999-9999-999999999999",
        role=UserRole.STUDENT,
        session_id="sess-12345",
    )

    # Tamper with token
    parts = token.split(".")
    tampered_token = f"{parts[0]}.{parts[1]}.badsignature"

    with pytest.raises(ValueError, match="Invalid or expired token"):
        decode_access_token(tampered_token)


def test_jwt_expired_rejected():
    token, _ = create_access_token(
        user_id="11111111-1111-1111-1111-111111111111",
        school_id="99999999-9999-9999-9999-999999999999",
        role=UserRole.STUDENT,
        session_id="sess-12345",
        expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
    )

    with pytest.raises(ValueError, match="Invalid or expired token"):
        decode_access_token(token)


def test_rate_limiter_blocks_after_threshold():
    limiter = LoginRateLimiter(max_attempts=3, window_seconds=60)
    ident = "0071234321"

    assert limiter.is_rate_limited(ident) is False

    limiter.record_attempt(ident)
    limiter.record_attempt(ident)
    assert limiter.is_rate_limited(ident) is False

    limiter.record_attempt(ident)
    assert limiter.is_rate_limited(ident) is True

    # Other identifier is not affected
    assert limiter.is_rate_limited("198204152005011789") is False

    # Reset clears limit
    limiter.reset(ident)
    assert limiter.is_rate_limited(ident) is False


def test_csrf_token_generation_and_validation():
    token1 = generate_csrf_token()
    token2 = generate_csrf_token()

    assert len(token1) >= 32
    assert token1 != token2

    # Matching tokens
    assert validate_csrf_tokens(token1, token1) is True

    # Mismatched tokens
    assert validate_csrf_tokens(token1, token2) is False

    # Missing token
    assert validate_csrf_tokens(None, token1) is False
    assert validate_csrf_tokens(token1, None) is False
    assert validate_csrf_tokens("", token1) is False
