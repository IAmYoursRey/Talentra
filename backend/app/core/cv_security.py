import json
import secrets
import hashlib
import hmac
from typing import Any, Dict
from datetime import datetime
from ..core.config import settings


SAFE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def _json_serial(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def canonicalize_data(data: Any) -> Any:
    """Recursively sort dict keys and normalize lists to ensure deterministic serialization."""
    if isinstance(data, dict):
        return {k: canonicalize_data(v) for k, v in sorted(data.items())}
    elif isinstance(data, list):
        return [canonicalize_data(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    return data


def compute_canonical_snapshot_digest(snapshot_data: Dict[str, Any]) -> str:
    """
    Computes a deterministic SHA-256 digest of the CV content snapshot.
    Excludes non-content operational fields (like status, generated_at if variable, or internal DB IDs).
    Content included:
    - student_id, school_id
    - snapshot_version, renderer_version
    - profile (displayName, schoolName, professionalSummary)
    - approved_skills
    - teacher_validated_competencies
    - selected_portfolios
    - optional_exploration_summary
    """
    canonical_payload = {
        "snapshot_version": snapshot_data.get("snapshot_version", "cv-snapshot-v1"),
        "renderer_version": snapshot_data.get("renderer_version", "cv-pdf-v1"),
        "school_id": snapshot_data.get("school_id", ""),
        "student_id": snapshot_data.get("student_id", ""),
        "profile": snapshot_data.get("profile", {}),
        "approved_skills": snapshot_data.get("approved_skills", []),
        "teacher_validated_competencies": snapshot_data.get("teacher_validated_competencies", []),
        "selected_portfolios": snapshot_data.get("selected_portfolios", []),
        "optional_exploration_summary": snapshot_data.get("optional_exploration_summary"),
    }
    
    canonical_repr = canonicalize_data(canonical_payload)
    serialized = json.dumps(canonical_repr, sort_keys=True, separators=(",", ":"), default=_json_serial)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def derive_snapshot_fingerprint(snapshot_digest: str) -> str:
    """
    Derives an informational short fingerprint from the SHA-256 digest for display comparison.
    Format: 4-4-4 hex uppercase (e.g. 8B4F-91C2-0DEA).
    """
    clean = snapshot_digest.upper()
    if len(clean) < 12:
        clean = clean.ljust(12, "0")
    return f"{clean[0:4]}-{clean[4:8]}-{clean[8:12]}"


def generate_verification_token() -> str:
    """
    Generates a cryptographically secure, high-entropy URL-safe token (32 bytes = 256 bits).
    Token is returned only once to the client for the QR code and verification URL.
    Database stores only HMAC hash.
    """
    return secrets.token_urlsafe(32)


def hash_verification_token(token: str, pepper: str | None = None) -> str:
    """
    Computes an HMAC-SHA256 digest of the raw bearer token using the server pepper.
    Raw tokens are never persisted in the database.
    """
    pep = pepper if pepper is not None else settings.cv_verification_token_pepper
    return hmac.new(pep.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def generate_display_code() -> str:
    """
    Generates a human-readable, non-sensitive document display code.
    Format: TLN-XXXX-XXXX using unambiguous characters.
    """
    part1 = "".join(secrets.choice(SAFE_ALPHABET) for _ in range(4))
    part2 = "".join(secrets.choice(SAFE_ALPHABET) for _ in range(4))
    return f"TLN-{part1}-{part2}"
