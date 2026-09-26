import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from ..core.config import settings
from ..core.audit import audit_logger
from ..core.database import AsyncSessionLocal
from ..db.models import OutboxEventModel
from ..domain.enums import AuditEventType
from ..domain.documents import PortfolioItemDocument, PortfolioRevisionDocument, EvidenceRef
from ..repositories.portfolio import (
    PortfolioRepository,
    get_portfolio_repository,
)
from ..repositories.storage_metadata import StorageMetadataRepository
from ..repositories.upload_intent import BlobUploadIntentRepository
from ..repositories.skill_tag import SkillTagRepository
from ..repositories.validation import TeacherValidationRepository
from ..storage import get_object_storage
from ..storage.base import generate_safe_object_key, validate_upload_policy, ObjectStorage
from ..storage.validation import EvidenceFileValidator, DevelopmentNoopScanner, validate_external_link

ALLOWED_ACTIVITY_TYPES = {
    "project",
    "competition",
    "organization",
    "certification",
    "volunteering",
    "research",
    "presentation",
    "internship",
    "creative-work",
    "other",
}


class EvidenceInput(BaseModel):
    type: str  # "file" or "external_link"
    storageObjectId: Optional[str] = None
    url: Optional[str] = None
    label: Optional[str] = None
    fileName: Optional[str] = None
    fileSize: Optional[str] = None
    mimeType: Optional[str] = None


class CreatePortfolioDTO(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    activityType: str = "project"
    activityDate: Optional[str] = None
    description: str = Field(min_length=1, max_length=5000)
    canonicalTagIds: List[str] = Field(default_factory=list)
    evidence: Optional[EvidenceInput] = None


class UpdatePortfolioDTO(BaseModel):
    title: Optional[str] = Field(None, max_length=150)
    activityType: Optional[str] = None
    activityDate: Optional[str] = None
    description: Optional[str] = Field(None, max_length=5000)
    canonicalTagIds: Optional[List[str]] = None
    evidence: Optional[EvidenceInput] = None


class PortfolioService:
    def __init__(
        self,
        portfolio_repo: Optional[PortfolioRepository] = None,
        storage_meta_repo: Optional[StorageMetadataRepository] = None,
        skill_tag_repo: Optional[SkillTagRepository] = None,
        object_storage: Optional[ObjectStorage] = None,
        validation_repo: Optional[TeacherValidationRepository] = None,
        intent_repo: Optional[BlobUploadIntentRepository] = None,
    ):
        self.portfolio_repo = portfolio_repo or get_portfolio_repository()

        self.storage_meta_repo = storage_meta_repo or StorageMetadataRepository()
        self.skill_tag_repo = skill_tag_repo or SkillTagRepository()
        self.validation_repo = validation_repo or TeacherValidationRepository()
        self.intent_repo = intent_repo or BlobUploadIntentRepository()
        self.storage = object_storage or get_object_storage()
        self.scanner = DevelopmentNoopScanner()

    def _validate_activity_type(self, act_type: str) -> None:
        if act_type.strip().lower() not in ALLOWED_ACTIVITY_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "PORTFOLIO_INVALID_STATE",
                    "message": f"Tipe aktivitas '{act_type}' tidak valid. Pilihan: {', '.join(sorted(ALLOWED_ACTIVITY_TYPES))}",
                },
            )

    def _validate_activity_date(self, date_str: str) -> str:
        try:
            parsed = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "PORTFOLIO_INVALID_STATE",
                    "message": "Format tanggal aktivitas harus YYYY-MM-DD.",
                },
            )
        max_future = datetime.now(timezone.utc).date() + timedelta(days=30)
        if parsed > max_future:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "PORTFOLIO_INVALID_STATE",
                    "message": "Tanggal aktivitas tidak boleh lebih dari 30 hari ke depan.",
                },
            )
        return date_str.strip()

    async def _resolve_evidence_refs(
        self, school_id: str, student_id: str, evidence: Optional[EvidenceInput]
    ) -> List[EvidenceRef]:
        if not evidence:
            return []

        if evidence.type == "file":
            if not evidence.storageObjectId:
                return []
            storage_obj = await self.storage_meta_repo.get_storage_object(
                id=evidence.storageObjectId,
                school_id=school_id,
                owner_user_id=student_id,
            )
            if not storage_obj or storage_obj.status != "available":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "UPLOAD_NOT_AVAILABLE",
                        "message": "Berkas bukti karya belum selesai divalidasi atau tidak tersedia.",
                    },
                )
            return [
                EvidenceRef(
                    type="file",
                    storage_object_id=storage_obj.id,
                    display_name=storage_obj.original_filename,
                    file_type=storage_obj.content_type,
                    size_bytes=storage_obj.size_bytes,
                    checksum=storage_obj.checksum,
                )
            ]
        elif evidence.type == "external_link":
            if not evidence.url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "EXTERNAL_LINK_INVALID",
                        "message": "URL tautan eksternal tidak boleh kosong.",
                    },
                )
            is_valid, err = validate_external_link(evidence.url, evidence.label)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "EXTERNAL_LINK_INVALID", "message": err or "URL tautan tidak valid."},
                )
            return [
                EvidenceRef(
                    type="external_link",
                    url=evidence.url.strip(),
                    label=evidence.label.strip() if evidence.label else "Tautan Proyek",
                    display_name=evidence.label.strip() if evidence.label else evidence.url.strip(),
                    file_type="link",
                )
            ]
        return []

    async def create_draft(
        self,
        school_id: str,
        student_id: str,
        payload: CreatePortfolioDTO,
    ) -> Dict[str, Any]:
        self._validate_activity_type(payload.activityType)
        activity_date = (
            self._validate_activity_date(payload.activityDate)
            if payload.activityDate
            else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        )

        evidence_refs = await self._resolve_evidence_refs(school_id, student_id, payload.evidence)

        # In draft mode, tags can be empty or partial
        doc, rev = await self.portfolio_repo.create_portfolio(
            school_id=school_id,
            student_id=student_id,
            title=payload.title.strip(),
            activity_type=payload.activityType.strip().lower(),
            activity_date=activity_date,
            description=payload.description.strip(),
            canonical_tag_ids=payload.canonicalTagIds or [],
            evidence_refs=evidence_refs,
        )

        audit_logger.log(
            event_type=AuditEventType.PORTFOLIO_CREATED,
            safe_context=f"Student draft portfolio created (portfolio_id={doc.portfolio_id})",
            user_id=student_id,
            school_id=school_id,
            metadata={"portfolio_id": doc.portfolio_id, "revision_id": rev.revision_id},
        )
        return doc.model_dump()

    async def get_portfolio(
        self, school_id: str, student_id: str, portfolio_id: str
    ) -> Dict[str, Any]:
        item = await self.portfolio_repo.get_portfolio(school_id, student_id, portfolio_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "PORTFOLIO_NOT_FOUND",
                    "message": "Karya portofolio tidak ditemukan atau Anda tidak memiliki hak akses.",
                },
            )
        item_dict = dict(item)
        try:
            history = await self.validation_repo.get_validation_history_for_portfolio(school_id, portfolio_id)
            item_dict["validation_history"] = history
        except Exception:
            item_dict["validation_history"] = []
        return item_dict

    async def list_portfolios(
        self,
        school_id: str,
        student_id: str,
        status_filter: Optional[str] = None,
        tag: Optional[str] = None,
        activity_type: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "newest",
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        return await self.portfolio_repo.list_portfolios(
            school_id=school_id,
            student_id=student_id,
            status=status_filter,
            tag=tag,
            activity_type=activity_type,
            search=search,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
        )

    async def update_draft(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
        payload: UpdatePortfolioDTO,
    ) -> Dict[str, Any]:
        # Verify existence and editability
        existing = await self.get_portfolio(school_id, student_id, portfolio_id)
        if existing.get("status") != "draft":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PORTFOLIO_NOT_EDITABLE",
                    "message": f"Karya tidak dapat diedit karena status saat ini adalah '{existing.get('status')}'.",
                },
            )

        update_dict: Dict[str, Any] = {}
        if payload.title is not None:
            if not payload.title.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "PORTFOLIO_INVALID_STATE", "message": "Judul karya tidak boleh kosong."},
                )
            update_dict["title"] = payload.title.strip()

        if payload.activityType is not None:
            self._validate_activity_type(payload.activityType)
            update_dict["activity_type"] = payload.activityType.strip().lower()

        if payload.activityDate is not None:
            update_dict["activity_date"] = self._validate_activity_date(payload.activityDate)

        if payload.description is not None:
            if not payload.description.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "PORTFOLIO_INVALID_STATE", "message": "Deskripsi karya tidak boleh kosong."},
                )
            update_dict["description"] = payload.description.strip()

        if payload.canonicalTagIds is not None:
            update_dict["canonical_tag_ids"] = payload.canonicalTagIds

        if payload.evidence is not None:
            evidence_refs = await self._resolve_evidence_refs(school_id, student_id, payload.evidence)
            update_dict["evidence_refs"] = [e.model_dump() for e in evidence_refs]

        updated = await self.portfolio_repo.update_draft(school_id, student_id, portfolio_id, update_dict)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PORTFOLIO_NOT_FOUND", "message": "Gagal memperbarui draf karya."},
            )

        audit_logger.log(
            event_type=AuditEventType.PORTFOLIO_UPDATED,
            safe_context=f"Student draft updated (portfolio_id={portfolio_id})",
            user_id=student_id,
            school_id=school_id,
            metadata={"portfolio_id": portfolio_id},
        )
        return updated

    async def delete_draft(self, school_id: str, student_id: str, portfolio_id: str) -> bool:
        existing = await self.get_portfolio(school_id, student_id, portfolio_id)
        if existing.get("status") != "draft":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PORTFOLIO_NOT_EDITABLE",
                    "message": "Hanya karya dalam status draf yang dapat dihapus oleh siswa.",
                },
            )
        deleted = await self.portfolio_repo.delete_draft(school_id, student_id, portfolio_id)
        return deleted

    async def request_upload_intent(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
        filename: str,
        content_type: str,
        declared_size_bytes: int,
        checksum: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validates draft state, declared file policy, creates pending storage record,
        and generates a safe short-lived presigned/signed upload URL.
        """
        existing = await self.get_portfolio(school_id, student_id, portfolio_id)
        if existing.get("status") != "draft":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PORTFOLIO_NOT_EDITABLE",
                    "message": "Unggahan berkas hanya diizinkan untuk karya berstatus draf.",
                },
            )

        # Validate declared format & size limit
        try:
            validate_upload_policy(content_type=content_type, file_size_bytes=declared_size_bytes)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "UPLOAD_TYPE_NOT_ALLOWED", "message": str(e)},
            )

        # Check free-tier storage quota soft limit
        if getattr(settings, "free_tier_mode", True):
            current_usage = await self.storage_meta_repo.get_total_used_storage(school_id=school_id)
            soft_limit = getattr(settings, "storage_soft_limit_bytes", 200 * 1024 * 1024)
            if current_usage + declared_size_bytes > soft_limit:
                raise HTTPException(
                    status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                    detail={
                        "code": "STORAGE_QUOTA_REACHED",
                        "message": "Kapasitas penyimpanan sekolah telah mencapai batas kuota gratis (soft limit). Hubungi administrator.",
                    },
                )

        storage_object_id = str(uuid.uuid4())
        safe_key = generate_safe_object_key(
            school_id=school_id,
            student_id=student_id,
            portfolio_id=portfolio_id,
            original_filename=filename,
        )

        # Create pending row in PostgreSQL
        provider = settings.object_storage_provider
        bucket = settings.s3_bucket if provider == "s3" else ("vercel-blob" if provider == "vercel_blob" else "local")
        await self.storage_meta_repo.create_pending_upload(
            id=storage_object_id,
            school_id=school_id,
            owner_user_id=student_id,
            provider=provider,
            bucket=bucket,
            object_key=safe_key,
            original_filename=filename,
            content_type=content_type,
            declared_size=declared_size_bytes,
            checksum=checksum,
        )

        # Create short-lived opaque upload intent
        intent_model, intent_token = await self.intent_repo.create_intent(
            school_id=school_id,
            student_id=student_id,
            portfolio_id=portfolio_id,
            pathname=safe_key,
            expected_content_type=content_type,
            max_bytes=declared_size_bytes,
            ttl_seconds=settings.presigned_url_ttl_seconds,
        )

        upload_url = self.storage.create_upload_url(
            object_key=safe_key,
            content_type=content_type,
            expires_in=settings.presigned_url_ttl_seconds,
        )

        audit_logger.log(
            event_type=AuditEventType.EVIDENCE_UPLOAD_CREATED,
            safe_context=f"Evidence upload intent issued (storage_id={storage_object_id})",
            user_id=student_id,
            school_id=school_id,
            metadata={"storage_object_id": storage_object_id, "portfolio_id": portfolio_id},
        )

        return {
            "storageObjectId": storage_object_id,
            "uploadUrl": upload_url,
            "intentToken": intent_token,
            "pathname": safe_key,
            "expiresInSeconds": settings.presigned_url_ttl_seconds,
            "objectKey": safe_key,
        }

    async def complete_upload(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
        storage_object_id: str,
    ) -> Dict[str, Any]:
        """
        Post-upload verification:
        1. Checks storage_objects status == pending
        2. Validates actual bytes via EvidenceFileValidator (magic bytes)
        3. Runs security scanner hook
        4. Transitions pending -> available
        """
        storage_obj = await self.storage_meta_repo.get_storage_object(
            id=storage_object_id,
            school_id=school_id,
            owner_user_id=student_id,
        )
        if not storage_obj or storage_obj.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "UPLOAD_OBJECT_NOT_FOUND",
                    "message": "Data pendaftaran unggahan tidak ditemukan atau status tidak valid.",
                },
            )

        # Inspect actual binary signature (magic bytes) and size
        is_valid, err_msg, actual_size, detected_mime = EvidenceFileValidator.validate_storage_object(
            storage=self.storage,
            object_key=storage_obj.object_key,
            declared_content_type=storage_obj.content_type,
        )

        if not is_valid:
            await self.storage_meta_repo.quarantine_upload(storage_object_id)
            audit_logger.log(
                event_type=AuditEventType.EVIDENCE_UPLOAD_REJECTED,
                safe_context=f"Upload rejected due to binary validation failure: {err_msg}",
                user_id=student_id,
                school_id=school_id,
                metadata={"storage_object_id": storage_object_id},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "UPLOAD_VALIDATION_FAILED", "message": err_msg or "Validasi biner berkas gagal."},
            )

        # Run scanner hook
        scan_result = self.scanner.scan_object(self.storage, storage_obj.object_key)
        if scan_result.value != "clean":
            await self.storage_meta_repo.quarantine_upload(storage_object_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "UPLOAD_VALIDATION_FAILED", "message": "Pemeriksaan keamanan berkas gagal."},
            )

        completed = await self.storage_meta_repo.complete_upload(
            id=storage_object_id,
            school_id=school_id,
            owner_user_id=student_id,
            actual_size=actual_size or 0,
            detected_content_type=detected_mime or storage_obj.content_type,
        )

        audit_logger.log(
            event_type=AuditEventType.EVIDENCE_UPLOAD_COMPLETED,
            safe_context=f"Evidence upload verified and marked available (storage_id={storage_object_id})",
            user_id=student_id,
            school_id=school_id,
            metadata={"storage_object_id": storage_object_id, "size_bytes": actual_size},
        )

        mb_str = f"{(actual_size or 0) / (1024 * 1024):.1f} MB"
        return {
            "storageObjectId": storage_object_id,
            "status": "available",
            "fileName": completed.original_filename if completed else storage_obj.original_filename,
            "fileSize": mb_str,
            "sizeBytes": actual_size or 0,
            "mimeType": detected_mime or storage_obj.content_type,
            "evidence": {
                "type": "file",
                "storageObjectId": storage_object_id,
                "fileName": completed.original_filename if completed else storage_obj.original_filename,
                "fileSize": mb_str,
                "mimeType": detected_mime or storage_obj.content_type,
            },
        }

    async def get_evidence_download_access(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
        storage_object_id: str,
    ) -> Dict[str, Any]:
        """
        Issues short-lived presigned/signed download URL.
        Never persists URL or exposes raw bucket credentials.
        """
        # Verify portfolio exists and belongs to student
        await self.get_portfolio(school_id, student_id, portfolio_id)

        storage_obj = await self.storage_meta_repo.get_storage_object(
            id=storage_object_id,
            school_id=school_id,
            owner_user_id=student_id,
        )
        if not storage_obj or storage_obj.status != "available":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "UPLOAD_OBJECT_NOT_FOUND", "message": "Berkas bukti karya tidak ditemukan."},
            )

        download_url = self.storage.create_download_url(
            object_key=storage_obj.object_key,
            expires_in=settings.presigned_url_ttl_seconds,
        )

        return {
            "storageObjectId": storage_object_id,
            "fileName": storage_obj.original_filename,
            "contentType": storage_obj.content_type,
            "downloadUrl": download_url,
            "expiresInSeconds": settings.presigned_url_ttl_seconds,
        }

    async def submit_portfolio(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
    ) -> Dict[str, Any]:
        """
        Authoritative validation for final submission:
        - Must be in draft state
        - Title, activity, description must be complete
        - Exactly 3 to 5 unique active canonical tags
        - At least 1 valid evidence reference
        - Atomically locks revision snapshot as immutable submitted revision
        """
        existing = await self.get_portfolio(school_id, student_id, portfolio_id)
        if existing.get("status") != "draft":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PORTFOLIO_NOT_EDITABLE",
                    "message": f"Karya tidak dapat diajukan karena status saat ini adalah '{existing.get('status')}'.",
                },
            )

        # 1. Title validation
        title = existing.get("title", "").strip()
        if not title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "PORTFOLIO_INVALID_STATE", "message": "Judul karya wajib diisi sebelum pengajuan."},
            )

        # 2. Description validation
        desc = existing.get("description", "").strip()
        if len(desc) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "PORTFOLIO_INVALID_STATE",
                    "message": "Deskripsi karya minimal 10 karakter sebelum pengajuan validasi.",
                },
            )

        # 3. Canonical tags validation: strictly 3-5 tags
        tags = existing.get("canonical_tag_ids", [])
        is_tags_valid, normalized_tags, tag_err = await self.skill_tag_repo.validate_tags(tags)
        if not is_tags_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "PORTFOLIO_TAG_COUNT_INVALID" if "batas" in (tag_err or "") else "PORTFOLIO_TAG_INVALID",
                    "message": tag_err or "Tag kapabilitas tidak valid.",
                },
            )

        # 4. Evidence validation: at least 1 valid evidence
        evidence_list = existing.get("evidence_refs", [])
        if not evidence_list or len(evidence_list) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "PORTFOLIO_EVIDENCE_REQUIRED",
                    "message": "Portofolio wajib menyertakan minimal 1 bukti karya valid (berkas atau tautan eksternal).",
                },
            )

        # Verify all file evidence in list have status == available in PostgreSQL
        for ev in evidence_list:
            ev_dict = ev if isinstance(ev, dict) else ev.model_dump()
            if ev_dict.get("type") == "file":
                s_id = ev_dict.get("storage_object_id")
                if not s_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={"code": "PORTFOLIO_EVIDENCE_REQUIRED", "message": "ID objek berkas bukti tidak valid."},
                    )
                st_obj = await self.storage_meta_repo.get_storage_object(s_id, school_id, student_id)
                if not st_obj or st_obj.status != "available":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "UPLOAD_NOT_AVAILABLE",
                            "message": f"Berkas bukti '{ev_dict.get('display_name')}' tidak tersedia atau belum diverifikasi.",
                        },
                    )

        expected_version = existing.get("current_revision_number", 1)
        submission_payload = {
            "canonical_tag_ids": normalized_tags,
        }

        submitted_item = await self.portfolio_repo.atomic_submit(
            school_id=school_id,
            student_id=student_id,
            portfolio_id=portfolio_id,
            expected_revision=expected_version,
            submission_data=submission_payload,
        )

        if not submitted_item:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PORTFOLIO_NOT_EDITABLE",
                    "message": "Pengajuan gagal karena status karya telah berubah secara bersamaan.",
                },
            )

        # Outbox event for asynchronous processing (relational persistence)
        try:
            async with AsyncSessionLocal() as session:
                outbox_evt = OutboxEventModel(
                    event_type="PORTFOLIO_SUBMITTED",
                    aggregate_type="portfolio",
                    aggregate_id=portfolio_id,
                    payload_json=json.dumps({
                        "portfolio_id": portfolio_id,
                        "school_id": school_id,
                        "student_id": student_id,
                        "revision_id": submitted_item.get("current_revision_id"),
                        "version": expected_version,
                    }),
                )
                session.add(outbox_evt)
                await session.commit()
        except Exception:
            pass

        audit_logger.log(
            event_type=AuditEventType.PORTFOLIO_SUBMITTED,
            safe_context=f"Student portfolio submitted for teacher validation (portfolio_id={portfolio_id}, version={expected_version})",
            user_id=student_id,
            school_id=school_id,
            metadata={"portfolio_id": portfolio_id, "version": expected_version},
        )

        return submitted_item

    async def begin_revision(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
    ) -> Dict[str, Any]:
        """
        Creates next editable revision when teacher requests revision.
        Previous submitted revision remains completely immutable.
        """
        existing = await self.get_portfolio(school_id, student_id, portfolio_id)
        if existing.get("status") != "revision_requested":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PORTFOLIO_INVALID_STATE",
                    "message": "Pembuatan revisi baru hanya diizinkan untuk karya berstatus 'revision_requested'.",
                },
            )

        updated = await self.portfolio_repo.begin_revision(school_id, student_id, portfolio_id)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PORTFOLIO_NOT_FOUND", "message": "Gagal memulai revisi baru."},
            )

        audit_logger.log(
            event_type=AuditEventType.PORTFOLIO_REVISION_STARTED,
            safe_context=f"Student initiated next revision cycle (portfolio_id={portfolio_id}, version={updated.get('current_revision_number')})",
            user_id=student_id,
            school_id=school_id,
            metadata={"portfolio_id": portfolio_id, "new_version": updated.get("current_revision_number")},
        )
        return updated
