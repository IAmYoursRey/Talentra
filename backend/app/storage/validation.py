import re
import urllib.parse
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Tuple

from .base import ObjectStorage, ALLOWED_CONTENT_TYPES
from ..core.config import settings


class SecurityScanStatus(str, Enum):
    CLEAN = "clean"
    INFECTED = "infected"
    UNAVAILABLE = "unavailable"


class EvidenceFileValidator:
    """
    Authoritative binary validator for student evidence files.
    Defense in depth: never trusts browser MIME or filename extensions alone.
    Inspects magic bytes and file signatures directly.
    """

    @staticmethod
    def detect_actual_mime_type(header_bytes: bytes) -> Optional[str]:
        if not header_bytes or len(header_bytes) < 4:
            return None

        # 1. PDF signature: starts with %PDF-
        if header_bytes.startswith(b"%PDF-"):
            return "application/pdf"

        # 2. PNG signature: 89 50 4E 47 0D 0A 1A 0A
        if header_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"

        # 3. JPEG signature: starts with FF D8 FF
        if header_bytes.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"

        # 4. MP4 signature: ISO Base Media format with 'ftyp' at offset 4..8
        if len(header_bytes) >= 12 and header_bytes[4:8] == b"ftyp":
            return "video/mp4"

        return None

    @classmethod
    def validate_storage_object(
        cls,
        storage: ObjectStorage,
        object_key: str,
        declared_content_type: str,
    ) -> Tuple[bool, Optional[str], Optional[int], Optional[str]]:
        """
        Inspects stored object:
        - Retrieves actual size
        - Reads initial 128 bytes to check magic bytes
        - Enforces size limit based on actual detected type
        - Detects MIME spoofing (e.g. .exe disguised as .pdf)

        Returns: (is_valid, error_message, actual_size_bytes, detected_mime_type)
        """
        head = storage.head_object(object_key)
        if not head:
            return False, f"Berkas dengan kunci '{object_key}' tidak ditemukan di penyimpanan.", None, None

        actual_size = head.get("size_bytes", 0)

        # Read first 128 bytes for magic signature inspection
        try:
            sample_bytes = storage.read_range(object_key, offset=0, length=128)
        except Exception as e:
            return False, f"Gagal membaca header berkas untuk validasi keamanan: {str(e)}", actual_size, None

        detected_mime = cls.detect_actual_mime_type(sample_bytes)
        if not detected_mime:
            return (
                False,
                "Tanda tangan biner (magic bytes) berkas tidak valid atau format tidak diizinkan. "
                "Hanya berkas PDF asli, gambar JPG/PNG asli, dan video MP4 asli yang diterima.",
                actual_size,
                None,
            )

        # Check declared vs detected MIME match
        cleaned_declared = declared_content_type.strip().lower()
        if cleaned_declared != detected_mime:
            return (
                False,
                f"Ketidakcocokan format berkas terdeteksi: tipe dideklarasikan '{cleaned_declared}' "
                f"tetapi konten biner adalah '{detected_mime}'. Pengunggahan ditolak demi keamanan.",
                actual_size,
                detected_mime,
            )

        # Enforce actual size limits
        max_allowed = ALLOWED_CONTENT_TYPES.get(detected_mime)
        if max_allowed and actual_size > max_allowed:
            max_mb = max_allowed // (1024 * 1024)
            return (
                False,
                f"Ukuran berkas aktual ({actual_size / (1024 * 1024):.2f} MB) melebihi batas "
                f"maksimal {max_mb} MB untuk tipe {detected_mime}.",
                actual_size,
                detected_mime,
            )

        return True, None, actual_size, detected_mime


class EvidenceSecurityScanner(ABC):
    @abstractmethod
    def scan_object(self, storage: ObjectStorage, object_key: str) -> SecurityScanStatus:
        pass


class DevelopmentNoopScanner(EvidenceSecurityScanner):
    """
    Development/test scanner.
    Explicitly marked: DOES NOT REPLACE REAL ANTIVIRUS IN PRODUCTION.
    Production systems must bind to ClamAV or cloud security scanner API.
    """

    def scan_object(self, storage: ObjectStorage, object_key: str) -> SecurityScanStatus:
        # Development pass-through
        return SecurityScanStatus.CLEAN


def validate_external_link(url: str, label: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validates external evidence URLs against SSRF and script injection vectors:
    - Must be HTTPS scheme
    - No localhost, 127.0.0.1, or private IP addresses
    - No embedded credentials (username:password@host)
    - Reasonable length constraints
    """
    if not url or not url.strip():
        return False, "URL tautan eksternal tidak boleh kosong."

    clean_url = url.strip()
    if len(clean_url) > 500:
        return False, "Panjang URL tautan eksternal melebihi batas maksimal 500 karakter."

    if label and len(label.strip()) > 120:
        return False, "Label tautan eksternal melebihi batas maksimal 120 karakter."

    parsed = urllib.parse.urlparse(clean_url)

    # 1. Strictly HTTPS scheme only
    if parsed.scheme.lower() != "https":
        return False, "Tautan eksternal wajib menggunakan protokol aman 'https://'."

    # 2. Host presence check
    hostname = parsed.hostname
    if not hostname:
        return False, "Alamat domain tautan eksternal tidak valid."

    hostname_lower = hostname.lower()

    # 3. SSRF vector prevention: localhost, loopback, private ranges
    forbidden_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
    if hostname_lower in forbidden_hosts or hostname_lower.endswith(".localhost"):
        return False, "Tautan ke alamat lokal/loopback tidak diizinkan."

    # Prevent IPv4 private addresses (10.x, 172.16-31.x, 192.168.x, 169.254.x)
    if re.match(r"^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|169\.254\.)", hostname_lower):
        return False, "Tautan ke alamat jaringan privat tidak diizinkan."

    # 4. Embedded credentials prevention
    if parsed.username or parsed.password:
        return False, "Tautan eksternal tidak boleh menyertakan kredensial pengguna (user:password)."

    # 5. Dangerous characters
    if any(c in clean_url for c in ["<", ">", '"', "'", "`"]):
        return False, "URL tautan eksternal mengandung karakter tidak valid."

    return True, None
