from datetime import datetime, timezone
from typing import Dict, Any, Optional

from ..core.config import settings
from ..core.audit import audit_logger
from ..core.cv_security import hash_verification_token, derive_snapshot_fingerprint
from ..domain.enums import AuditEventType, VerificationStatus
from ..repositories.portfolio import (
    PortfolioRepository,
    get_portfolio_repository,
)
from ..repositories.verification import (
    VerificationRepository,
    get_verification_repository,
    InMemoryVerificationRepository,
)


class PublicVerificationService:
    def __init__(
        self,
        verification_repo: Optional[VerificationRepository] = None,
        portfolio_repo: Optional[PortfolioRepository] = None,
    ):
        if verification_repo:
            self.verification_repo = verification_repo
        else:
            if settings.app_env == "test":
                self.verification_repo = InMemoryVerificationRepository()
            else:
                self.verification_repo = get_verification_repository()

        self.portfolio_repo = portfolio_repo or get_portfolio_repository()

    async def verify_public_token(self, raw_token: str) -> Dict[str, Any]:
        """
        Public verification boundary.
        Hashes the token, looks up record, and returns privacy-safe verification status.
        Generic responses prevent token enumeration.
        """
        if not raw_token or len(raw_token.strip()) < 16:
            return {
                "status": "invalid",
                "message": "Dokumen tidak ditemukan atau tautan verifikasi tidak valid.",
            }

        token_hash = hash_verification_token(raw_token.strip())
        record = await self.verification_repo.get_by_token_hash(token_hash)
        if not record:
            return {
                "status": "invalid",
                "message": "Dokumen tidak ditemukan atau tautan verifikasi tidak valid.",
            }

        display_code = record.get("display_code", "TLN-UNKNOWN")
        record_status = record.get("status", VerificationStatus.ACTIVE.value)

        # Audit check (No raw token logged!)
        audit_logger.log_event(
            AuditEventType.CV_PUBLIC_VERIFICATION_CHECKED,
            school_id=record.get("school_id"),
            safe_context="cv_public_verification_checked",
            metadata={
                "verification_record_id": record.get("id"),
                "display_code": display_code,
                "status": record_status,
            },
        )

        # Check Revoked
        if record_status == VerificationStatus.REVOKED.value:
            revoked_at_iso = None
            if record.get("revoked_at") and hasattr(record["revoked_at"], "isoformat"):
                revoked_at_iso = record["revoked_at"].isoformat()
            return {
                "status": "revoked",
                "displayCode": display_code,
                "message": "Dokumen tidak lagi berlaku. Keabsahan dokumen ini telah dicabut.",
                "revokedAt": revoked_at_iso,
            }

        # Check Expired
        now = datetime.now(timezone.utc)
        expires_at = record.get("expires_at")
        if record_status == VerificationStatus.EXPIRED.value or (
            expires_at and isinstance(expires_at, datetime) and expires_at < now
        ):
            return {
                "status": "expired",
                "displayCode": display_code,
                "message": "Masa verifikasi dokumen ini telah berakhir.",
                "expiresAt": expires_at.isoformat() if hasattr(expires_at, "isoformat") else str(expires_at),
            }

        # Active - Resolve Snapshot Content
        snapshot_id = record.get("cv_snapshot_id")
        snapshot = await self.portfolio_repo.get_cv_snapshot_by_id(snapshot_id)
        if not snapshot:
            return {
                "status": "invalid",
                "message": "Dokumen tidak ditemukan atau data snapshot tidak tersedia.",
            }

        profile = snapshot.get("profile", {})
        published_portfolios = []
        for p in snapshot.get("selected_portfolios", []):
            published_portfolios.append({
                "title": p.get("title", ""),
                "activityType": p.get("activity_type", ""),
                "activityDate": p.get("activity_date", ""),
                "description": p.get("professional_description") or p.get("description", ""),
                "tags": p.get("tags", []),
            })

        published_skills = []
        for s in snapshot.get("approved_skills", []):
            published_skills.append({
                "name": s.get("name") or s.get("dimension", ""),
                "score": s.get("score", 0),
                "level": s.get("level", ""),
            })

        digest = record.get("snapshot_digest", "")

        return {
            "status": "verified",
            "displayCode": display_code,
            "studentDisplayName": profile.get("display_name", "Siswa TALENTRA"),
            "schoolDisplayName": profile.get("school_name", ""),
            "issuedAt": (
                record["issued_at"].isoformat()
                if hasattr(record["issued_at"], "isoformat")
                else str(record.get("issued_at"))
            ),
            "expiresAt": (
                expires_at.isoformat()
                if expires_at and hasattr(expires_at, "isoformat")
                else None
            ),
            "snapshotDigestShort": derive_snapshot_fingerprint(digest),
            "selectedPortfolioSummaries": published_portfolios,
            "validatedSkillSummary": published_skills,
            "verificationStatement": (
                "Dokumen ini diterbitkan dari rekam jejak karya yang telah divalidasi "
                "melalui platform TALENTRA.ID."
            ),
        }
