import re
from .enums import IdentifierType

class NormalizedIdentifierResult:
    def __init__(self, raw: str, normalized: str, identifier_type: IdentifierType, masked: str):
        self.raw = raw
        self.normalized = normalized
        self.identifier_type = identifier_type
        self.masked = masked

def normalize_login_identifier(raw_identifier: str) -> NormalizedIdentifierResult:
    """
    Validates and normalizes login identifiers for Indonesian school users:
    - NISN: exactly 10 numeric digits. Leading zeroes MUST be preserved as string.
    - NUPTK: exactly 16 numeric digits.
    - NIP: exactly 18 numeric digits.
    - NPSN: exactly 8 alphanumeric characters (not restricted to numeric).
    """
    cleaned = raw_identifier.strip()
    
    # 1. Check Student NISN: 10 digits
    if re.fullmatch(r"^\d{10}$", cleaned):
        masked = f"NISN: *******{cleaned[-3:]}"
        return NormalizedIdentifierResult(
            raw=raw_identifier,
            normalized=cleaned,
            identifier_type=IdentifierType.NISN,
            masked=masked,
        )
    
    # 2. Check Teacher NUPTK: 16 digits
    if re.fullmatch(r"^\d{16}$", cleaned):
        masked = f"NUPTK: *************{cleaned[-3:]}"
        return NormalizedIdentifierResult(
            raw=raw_identifier,
            normalized=cleaned,
            identifier_type=IdentifierType.NUPTK,
            masked=masked,
        )
        
    # 3. Check Teacher NIP: 18 digits
    if re.fullmatch(r"^\d{18}$", cleaned):
        masked = f"NIP: ***************{cleaned[-3:]}"
        return NormalizedIdentifierResult(
            raw=raw_identifier,
            normalized=cleaned,
            identifier_type=IdentifierType.NIP,
            masked=masked,
        )

    # 4. Check School Admin NPSN: exactly 8 alphanumeric characters (upper normalized)
    upper_cleaned = cleaned.upper()
    if re.fullmatch(r"^[A-Z0-9]{8}$", upper_cleaned):
        masked = f"NPSN: *****{upper_cleaned[-3:]}"
        return NormalizedIdentifierResult(
            raw=raw_identifier,
            normalized=upper_cleaned,
            identifier_type=IdentifierType.NPSN,
            masked=masked,
        )

    # 5. Check Email address: standard RFC-compliant user@domain format
    if re.fullmatch(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", cleaned):
        lower_cleaned = cleaned.lower()
        parts = lower_cleaned.split("@")
        masked = f"EMAIL: *******{parts[0][-4:] if len(parts[0]) >= 4 else parts[0]}@{parts[1]}"
        return NormalizedIdentifierResult(
            raw=raw_identifier,
            normalized=lower_cleaned,
            identifier_type=IdentifierType.EMAIL,
            masked=masked,
        )

    # If it does not match any official format, raise ValueError with generic feedback
    raise ValueError("Format ID pengguna tidak valid. Masukkan email, 10 digit NISN, 16/18 digit NUPTK/NIP, atau 8 karakter NPSN.")

def mask_identifier(identifier: str, id_type: IdentifierType) -> str:
    """Helper to mask an identifier safely without exposing full digits."""
    cleaned = identifier.strip()
    if id_type == IdentifierType.EMAIL:
        parts = cleaned.split("@")
        if len(parts) == 2:
            return f"EMAIL: *******{parts[0][-4:] if len(parts[0]) >= 4 else parts[0]}@{parts[1]}"
    suffix = cleaned[-3:] if len(cleaned) >= 3 else cleaned
    return f"{id_type.value}: *******{suffix}"
