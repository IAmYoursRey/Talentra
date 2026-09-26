import re
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from ..core.config import settings
from ..core.audit import audit_logger
from ..core.idempotency import idempotency_manager
from ..domain.enums import AuditEventType
from ..repositories.portfolio import PortfolioRepository, get_portfolio_repository, InMemoryPortfolioRepository
from ..repositories.validation import TeacherValidationRepository
from ..repositories.storage_metadata import StorageMetadataRepository
from ..storage import get_object_storage
from ..storage.base import ObjectStorage
from .projection_service import StudentSkillProjectionService

RUBRIC_DIMENSIONS = ["initiative", "collaboration", "communication", "responsibility", "resilience"]


class RubricInputDTO(BaseModel):
    initiative: int = Field(ge=1, le=5)
    collaboration: int = Field(ge=1, le=5)
    communication: int = Field(ge=1, le=5)
    responsibility: int = Field(ge=1, le=5)
    resilience: int = Field(ge=1, le=5)


class TeacherDecisionRequestDTO(BaseModel):
    revisionId: str = Field(min_length=1)
    action: str = Field(description="Must be 'approved', 'revision_requested', or 'rejected'")
    feedback: Optional[str] = Field(None, max_length=4000)
    rubric: Optional[RubricInputDTO] = None


class TeacherReviewService:
    def __init__(
        self,
        portfolio_repo: Optional[PortfolioRepository] = None,
        validation_repo: Optional[TeacherValidationRepository] = None,
        storage_meta_repo: Optional[StorageMetadataRepository] = None,
        object_storage: Optional[ObjectStorage] = None,
        projection_service: Optional[StudentSkillProjectionService] = None,
    ):
        self.portfolio_repo = portfolio_repo or get_portfolio_repository()

        self.validation_repo = validation_repo or TeacherValidationRepository()
        self.storage_meta_repo = storage_meta_repo or StorageMetadataRepository()
        self.storage = object_storage or get_object_storage()
        self.projection_service = projection_service or StudentSkillProjectionService(
            portfolio_repo=self.portfolio_repo,
            validation_repo=self.validation_repo,
        )

    async def get_teacher_queue(
        self,
        teacher_id: str,
        school_id: str,
        class_name: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "oldest",
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieves the teacher's pending approval queue.
        Enforces teacher assignment scope: ONLY returns submitted portfolios
        of students enrolled in classes assigned to this teacher.
        Default sort: oldest submission first so work doesn't languish.
        """
        # 1. Resolve eligible students from PostgreSQL teacher assignments & enrollments
        eligible_students = await self.validation_repo.get_eligible_students_for_teacher(
            school_id=school_id, teacher_id=teacher_id
        )
        if not eligible_students:
            return [], 0

        # Filter by class_name if specified
        if class_name and class_name != "all":
            eligible_students = [
                s for s in eligible_students
                if class_name.lower() in s["class_name"].lower()
            ]
            if not eligible_students:
                return [], 0

        student_info_map = {s["student_id"]: s for s in eligible_students}
        eligible_student_ids = list(student_info_map.keys())

        # 2. Query MongoDB for submitted portfolio items of these students
        items, total = await self.portfolio_repo.list_teacher_queue(
            school_id=school_id,
            eligible_student_ids=eligible_student_ids,
            tag=tag,
            search=search,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
        )

        # 3. Format safe response objects without exposing NISN
        formatted_items = []
        for item in items:
            s_info = student_info_map.get(item.get("student_id"), {})
            ev_refs = item.get("evidence_refs", [])
            evidence_types = list(set(
                (e.get("type") if isinstance(e, dict) else e.type) for e in ev_refs
            )) if ev_refs else []

            sub_at = item.get("submitted_at")
            formatted_items.append({
                "portfolioId": item.get("portfolio_id"),
                "revisionId": item.get("current_revision_id"),
                "studentId": item.get("student_id"),
                "studentDisplayName": s_info.get("student_display_name", "Siswa"),
                "classDisplayName": s_info.get("class_name", "Kelas"),
                "title": item.get("title"),
                "activityType": item.get("activity_type"),
                "canonicalTags": item.get("canonical_tag_ids", []),
                "submittedAt": sub_at.isoformat() if hasattr(sub_at, "isoformat") else str(sub_at) if sub_at else None,
                "evidenceTypes": evidence_types,
                "status": item.get("status"),
            })

        return formatted_items, total

    async def get_teacher_review_detail(
        self, teacher_id: str, school_id: str, portfolio_id: str
    ) -> Dict[str, Any]:
        """
        Retrieves the exact submitted revision snapshot for teacher review.
        Enforces tenant boundary and teacher assignment authorization scope.
        """
        # 1. Fetch portfolio from MongoDB
        item = await self.portfolio_repo.get_portfolio_by_id(school_id, portfolio_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PORTFOLIO_NOT_FOUND", "message": "Karya portofolio tidak ditemukan."},
            )

        student_id = item.get("student_id")

        # 2. Verify teacher assignment scope in PostgreSQL
        is_auth, _ = await self.validation_repo.is_teacher_authorized_for_student(
            school_id=school_id, teacher_id=teacher_id, student_id=student_id
        )
        if not is_auth:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "TEACHER_SCOPE_FORBIDDEN",
                    "message": "Anda tidak memiliki penugasan aktif untuk memeriksa portofolio siswa ini.",
                },
            )

        # 3. Retrieve the exact submitted revision snapshot (immutable)
        revision_id = item.get("current_revision_id")
        revision = await self.portfolio_repo.get_revision_by_id(revision_id)
        if not revision:
            # Fallback to current item snapshot if revision doc not found
            revision = {
                "revision_id": revision_id,
                "version": item.get("current_revision_number", 1),
                "title_snapshot": item.get("title"),
                "activity_type_snapshot": item.get("activity_type"),
                "description_snapshot": item.get("description"),
                "tag_snapshot": item.get("canonical_tag_ids", []),
                "evidence_refs": item.get("evidence_refs", []),
                "submitted_at": item.get("submitted_at"),
            }

        # 4. Fetch safe student profile & validation history from PostgreSQL
        student_profile = await self.validation_repo.get_student_safe_profile(school_id, student_id)
        history = await self.validation_repo.get_validation_history_for_portfolio(school_id, portfolio_id)

        # Audit log access
        audit_logger.log(
            event_type=AuditEventType.AUTH_RBAC_CHALLENGE,
            safe_context=f"Teacher opened portfolio review (portfolio_id={portfolio_id}, revision_id={revision_id})",
            user_id=teacher_id,
            school_id=school_id,
            metadata={"portfolio_id": portfolio_id, "revision_id": revision_id, "event": "VALIDATION_REVIEW_OPENED"},
        )

        sub_at = revision.get("submitted_at") or item.get("submitted_at")
        return {
            "portfolioId": item.get("portfolio_id"),
            "studentId": student_id,
            "studentDisplayName": student_profile.get("display_name", "Siswa") if student_profile else "Siswa",
            "classDisplayName": student_profile.get("class_name", "Kelas") if student_profile else "Kelas",
            "portfolio": {
                "title": item.get("title"),
                "activityType": item.get("activity_type"),
                "activityDate": item.get("activity_date"),
                "status": item.get("status"),
                "teacherFeedback": item.get("teacher_feedback"),
            },
            "revision": {
                "revisionId": revision.get("revision_id"),
                "version": revision.get("version", 1),
                "submittedAt": sub_at.isoformat() if hasattr(sub_at, "isoformat") else str(sub_at) if sub_at else None,
                "titleSnapshot": revision.get("title_snapshot", item.get("title")),
                "activityTypeSnapshot": revision.get("activity_type_snapshot", item.get("activity_type")),
                "descriptionSnapshot": revision.get("description_snapshot", item.get("description")),
                "tags": revision.get("tag_snapshot", item.get("canonical_tag_ids", [])),
                "evidence": revision.get("evidence_refs", item.get("evidence_refs", [])),
            },
            "validationHistory": history,
        }

    async def get_evidence_download_access(
        self, teacher_id: str, school_id: str, portfolio_id: str, storage_object_id: str
    ) -> Dict[str, Any]:
        """
        Authorizes teacher access to private evidence binary.
        Guarantees:
        1. Teacher belongs to same school
        2. Teacher has active assignment to student's class
        3. Evidence object belongs to reviewed revision
        4. Issues short-lived presigned/signed download URL
        """
        item = await self.portfolio_repo.get_portfolio_by_id(school_id, portfolio_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PORTFOLIO_NOT_FOUND", "message": "Karya portofolio tidak ditemukan."},
            )

        student_id = item.get("student_id")
        is_auth, _ = await self.validation_repo.is_teacher_authorized_for_student(
            school_id=school_id, teacher_id=teacher_id, student_id=student_id
        )
        if not is_auth:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "TEACHER_SCOPE_FORBIDDEN", "message": "Akses bukti karya ditolak."},
            )

        # Check evidence reference in revision
        revision_id = item.get("current_revision_id")
        revision = await self.portfolio_repo.get_revision_by_id(revision_id)
        ev_refs = (revision.get("evidence_refs") if revision else None) or item.get("evidence_refs", [])

        found = False
        for e in ev_refs:
            sid = e.get("storage_object_id") if isinstance(e, dict) else getattr(e, "storage_object_id", None)
            if sid == storage_object_id:
                found = True
                break

        if not found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "EVIDENCE_NOT_IN_REVISION", "message": "Berkas bukti bukan bagian dari revisi yang diajukan."},
            )

        storage_obj = await self.storage_meta_repo.get_storage_object(
            id=storage_object_id,
            school_id=school_id,
            owner_user_id=student_id,
        )
        if not storage_obj or storage_obj.status != "available":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "UPLOAD_OBJECT_NOT_FOUND", "message": "Berkas bukti karya tidak tersedia."},
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

    async def submit_decision(
        self,
        teacher_id: str,
        school_id: str,
        portfolio_id: str,
        payload: TeacherDecisionRequestDTO,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Unified authoritative decision endpoint for teacher review:
        Handles:
        1. approved (Endorse / ACC) -> requires complete 1-5 rubric for 5 dimensions
        2. revision_requested -> requires feedback >= 5 chars
        3. rejected -> requires reason >= 5 chars

        Enforces:
        - Revision binding (expectedRevisionId matches current_revision_id)
        - Stale revision defense (409 REVIEW_STALE_REVISION)
        - Double decision defense (409 REVIEW_ALREADY_DECIDED)
        - Idempotency key handling
        - Cross-store consistency via pending -> atomic Mongo transition -> applied
        - Approved evidence snapshot projection on approval
        """
        operation = f"teacher_decision:{portfolio_id}"
        if idempotency_key:
            cached = await idempotency_manager.get_cached_response(
                user_id=teacher_id,
                operation=operation,
                client_key=idempotency_key,
            )
            if cached:
                cached_status, cached_body = cached
                return cached_body

        # Validate action string
        action = payload.action.strip().lower()
        if action not in ("approved", "revision_requested", "rejected"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_DECISION_ACTION",
                    "message": "Aksi keputusan harus 'approved', 'revision_requested', atau 'rejected'.",
                },
            )

        # 1. Fetch item from MongoDB
        item = await self.portfolio_repo.get_portfolio_by_id(school_id, portfolio_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PORTFOLIO_NOT_FOUND", "message": "Karya portofolio tidak ditemukan."},
            )

        student_id = item.get("student_id")

        # 2. Teacher assignment scope check
        is_auth, assignment_id = await self.validation_repo.is_teacher_authorized_for_student(
            school_id=school_id, teacher_id=teacher_id, student_id=student_id
        )
        if not is_auth:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "TEACHER_SCOPE_FORBIDDEN", "message": "Anda tidak memiliki penugasan untuk kelas siswa ini."},
            )

        # 3. Status check: item MUST be in 'submitted' state
        current_status = item.get("status")
        if current_status != "submitted":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "REVIEW_ALREADY_DECIDED",
                    "message": f"Karya ini tidak dapat dinilai karena status saat ini adalah '{current_status}'.",
                },
            )

        # 4. Revision binding check: expectedRevisionId MUST match current_revision_id
        current_rev_id = item.get("current_revision_id")
        if current_rev_id != payload.revisionId:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "REVIEW_STALE_REVISION",
                    "message": "Revisi yang Anda tinjau sudah usang. Siswa telah mengajukan revisi terbaru.",
                },
            )

        # 5. Action-specific validation
        cleaned_feedback = (payload.feedback or "").strip()
        rubric_dict: Optional[Dict[str, int]] = None

        if action == "approved":
            if not payload.rubric:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "RUBRIC_REQUIRED",
                        "message": "Persetujuan portofolio mewajibkan pengisian rubrik soft-skill lengkap untuk kelima dimensi.",
                    },
                )
            rubric_data = payload.rubric.model_dump()
            for dim in RUBRIC_DIMENSIONS:
                val = rubric_data.get(dim)
                if val is None or not isinstance(val, int) or val < 1 or val > 5:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "RUBRIC_INVALID_VALUE",
                            "message": f"Nilai rubrik '{dim}' harus berupa bilangan bulat antara 1 dan 5.",
                        },
                    )
            rubric_dict = rubric_data
        elif action == "revision_requested":
            if len(cleaned_feedback) < 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "FEEDBACK_REQUIRED",
                        "message": "Catatan revisi wajib diisi dengan jelas (minimal 5 karakter) agar siswa memahami perbaikan yang diperlukan.",
                    },
                )
        elif action == "rejected":
            if len(cleaned_feedback) < 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "REJECTION_REASON_REQUIRED",
                        "message": "Alasan penolakan karya wajib diisi dengan jelas (minimal 5 karakter).",
                    },
                )

        # 6. Execute Recoverable Cross-Store Decision Workflow
        decision_id = str(uuid.uuid4())
        key_hash = None
        if idempotency_key:
            from ..core.security import compute_identifier_lookup_hash
            key_hash = compute_identifier_lookup_hash(idempotency_key)

        # Step A: Create relational validation_decisions row with status=pending
        await self.validation_repo.create_pending_decision(
            decision_id=decision_id,
            school_id=school_id,
            portfolio_id=portfolio_id,
            revision_id=payload.revisionId,
            student_id=student_id,
            teacher_id=teacher_id,
            teacher_assignment_id=assignment_id,
            action=action,
            feedback=cleaned_feedback if cleaned_feedback else None,
            idempotency_key_hash=key_hash,
        )

        # Step B: Atomic MongoDB portfolio status transition
        updated_item = await self.portfolio_repo.atomic_transition_review(
            school_id=school_id,
            portfolio_id=portfolio_id,
            expected_revision_id=payload.revisionId,
            target_status=action,
            feedback=cleaned_feedback if cleaned_feedback else None,
        )

        if not updated_item:
            # Transition failed due to concurrent modification
            await self.validation_repo.fail_decision(
                decision_id=decision_id,
                failure_code="CONCURRENT_TRANSITION_FAILED",
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "REVIEW_ALREADY_DECIDED",
                    "message": "Keputusan gagal diterapkan karena status karya telah berubah secara bersamaan.",
                },
            )

        # Step C: Mark relational decision applied & persist rubrics & outbox event
        outbox_event_map = {
            "approved": "PORTFOLIO_APPROVED",
            "revision_requested": "PORTFOLIO_REVISION_REQUESTED",
            "rejected": "PORTFOLIO_REJECTED",
        }
        outbox_payload = {
            "portfolio_id": portfolio_id,
            "revision_id": payload.revisionId,
            "student_id": student_id,
            "school_id": school_id,
            "teacher_id": teacher_id,
            "action": action,
            "decision_id": decision_id,
        }

        await self.validation_repo.apply_decision(
            decision_id=decision_id,
            rubrics=rubric_dict,
            outbox_event_type=outbox_event_map.get(action),
            outbox_payload=outbox_payload,
        )

        # Step D: On approval, create idempotent approved evidence snapshot
        if action == "approved":
            tags = updated_item.get("canonical_tag_ids", [])
            await self.projection_service.project_approved_evidence(
                school_id=school_id,
                student_id=student_id,
                portfolio_id=portfolio_id,
                revision_id=payload.revisionId,
                validation_decision_id=decision_id,
                canonical_tag_ids=tags,
                approved_at=datetime.now(timezone.utc),
            )

        # Step E: Audit logging
        audit_event_map = {
            "approved": AuditEventType.PORTFOLIO_APPROVED,
            "revision_requested": AuditEventType.PORTFOLIO_REVISION_REQUESTED,
            "rejected": AuditEventType.PORTFOLIO_REJECTED,
        }
        audit_logger.log(
            event_type=audit_event_map[action],
            safe_context=f"Teacher decision applied (portfolio_id={portfolio_id}, action={action}, decision_id={decision_id})",
            user_id=teacher_id,
            school_id=school_id,
            metadata={
                "portfolio_id": portfolio_id,
                "revision_id": payload.revisionId,
                "decision_id": decision_id,
                "action": action,
            },
        )

        response_body = {
            "decisionId": decision_id,
            "portfolioId": portfolio_id,
            "revisionId": payload.revisionId,
            "action": action,
            "status": action,
            "applicationStatus": "applied",
            "feedback": cleaned_feedback if cleaned_feedback else None,
            "decidedAt": datetime.now(timezone.utc).isoformat(),
        }

        # Step F: Cache idempotency response if key provided
        if idempotency_key:
            await idempotency_manager.store_response(
                user_id=teacher_id,
                operation=operation,
                client_key=idempotency_key,
                status_code=status.HTTP_200_OK,
                response_dict=response_body,
            )

        return response_body

    async def reconcile_validation_decisions(self, threshold_seconds: int = 60) -> int:
        """
        Maintenance command for pending decision reconciliation (Section 31):
        Inspects pending decisions older than threshold and reconciles MongoDB state.
        """
        pending_decisions = await self.validation_repo.get_pending_decisions_older_than(threshold_seconds)
        reconciled_count = 0

        for dec in pending_decisions:
            item = await self.portfolio_repo.get_portfolio_by_id(dec.school_id, dec.portfolio_id)
            if not item:
                await self.validation_repo.fail_decision(dec.id, "ORPHANED_PENDING")
                reconciled_count += 1
                continue

            current_status = item.get("status")
            if current_status == dec.action:
                # Mongo transition already succeeded; apply PostgreSQL decision
                await self.validation_repo.apply_decision(dec.id)
                reconciled_count += 1
            elif current_status == "submitted":
                # Mongo was never updated; fail the orphaned decision
                await self.validation_repo.fail_decision(dec.id, "ORPHANED_PENDING")
                reconciled_count += 1
            else:
                # Status mismatch
                await self.validation_repo.fail_decision(dec.id, "TRANSITION_MISMATCH")
                reconciled_count += 1

        return reconciled_count
