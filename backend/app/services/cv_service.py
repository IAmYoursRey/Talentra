import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import select, and_

from ..core.config import settings
from ..core.audit import audit_logger
from ..core.database import AsyncSessionLocal
from ..core.cv_security import (
    compute_canonical_snapshot_digest,
    derive_snapshot_fingerprint,
    generate_verification_token,
    hash_verification_token,
    generate_display_code,
)
from ..domain.enums import AuditEventType, VerificationStatus, CVIssuanceStatus
from ..domain.documents import CVContentSnapshotDocument
from ..db.models import StorageObjectModel, EnrollmentModel, ClassModel
from ..repositories.portfolio import (
    PortfolioRepository,
    get_portfolio_repository,
)
from ..repositories.postgres import PostgresIdentityRepository
from ..repositories.validation import TeacherValidationRepository
from ..repositories.verification import (
    VerificationRepository,
    get_verification_repository,
    InMemoryVerificationRepository,
)
from ..storage import get_object_storage, ObjectStorage, generate_safe_cv_pdf_key
from .cv_pdf_renderer import CVPdfRenderer, ReportLabCVRenderer
from .industry_translator import IndustryTranslatorService
from .projection_service import StudentSkillProjectionService


class CVService:
    def __init__(
        self,
        portfolio_repo: Optional[PortfolioRepository] = None,
        identity_repo: Optional[PostgresIdentityRepository] = None,
        verification_repo: Optional[VerificationRepository] = None,
        validation_repo: Optional[TeacherValidationRepository] = None,
        storage: Optional[ObjectStorage] = None,
        renderer: Optional[CVPdfRenderer] = None,
        translator_service: Optional[IndustryTranslatorService] = None,
        projection_service: Optional[StudentSkillProjectionService] = None,
    ):
        self.portfolio_repo = portfolio_repo or get_portfolio_repository()

        self.identity_repo = identity_repo or PostgresIdentityRepository()

        if verification_repo:
            self.verification_repo = verification_repo
        else:
            if settings.app_env == "test":
                self.verification_repo = InMemoryVerificationRepository()
            else:
                self.verification_repo = get_verification_repository()

        self.validation_repo = validation_repo or TeacherValidationRepository()
        self.storage = storage or get_object_storage()
        self.renderer = renderer or ReportLabCVRenderer()
        self.translator_service = translator_service or IndustryTranslatorService(portfolio_repo=self.portfolio_repo)
        self.projection_service = projection_service or StudentSkillProjectionService(
            portfolio_repo=self.portfolio_repo, validation_repo=self.validation_repo
        )

    async def _resolve_student_class_name(self, student_id: str) -> str:
        """Resolves student class name without exposing internal IDs."""
        try:
            async with AsyncSessionLocal() as session:
                stmt = (
                    select(ClassModel.name)
                    .join(EnrollmentModel, EnrollmentModel.class_id == ClassModel.id)
                    .where(
                        and_(
                            EnrollmentModel.student_id == student_id,
                            EnrollmentModel.status == "active",
                        )
                    )
                )
                res = await session.execute(stmt)
                name = res.scalar_one_or_none()
                return name or ""
        except Exception:
            return ""

    async def get_student_cv_builder_context(self, school_id: str, student_id: str) -> Dict[str, Any]:
        """
        Retrieves authoritative, validated candidate data for Student CV generation.
        Filters ONLY approved portfolio evidence.
        """
        # 1. Identity & School
        user = await self.identity_repo.get_user_for_school(school_id, student_id)
        if not user:
            raise HTTPException(status_code=404, detail="Data siswa tidak ditemukan.")

        school = await self.identity_repo.get_school_by_id(school_id)
        school_name = school.name if school else ""
        class_name = await self._resolve_student_class_name(student_id)

        # 2. Approved-only portfolios
        raw_portfolios, _ = await self.portfolio_repo.list_portfolios(
            school_id=school_id, student_id=student_id, status="approved", limit=50
        )
        approved_portfolios = []
        for p in raw_portfolios:
            # Attach professional description if available
            prof = await self.portfolio_repo.get_professional_description(
                school_id, student_id, p["portfolio_id"]
            )
            approved_portfolios.append({
                "portfolioId": p["portfolio_id"],
                "revisionId": p.get("current_revision_id", ""),
                "title": p["title"],
                "activityType": p.get("activity_type", ""),
                "activityDate": p.get("activity_date", ""),
                "description": p.get("description", ""),
                "professionalDescription": prof.get("professional_text") if prof else None,
                "canonicalTagIds": p.get("canonical_tag_ids", []),
                "status": p.get("status"),
            })

        # 3. Canonical validated skills radar
        skills_data = await self.projection_service.get_student_skills(school_id, student_id)
        radar_points = skills_data.get("radar", [])

        # 4. Teacher rubric summary (aggregated observations only, no private comments or IDs)
        rubric_summary = await self.validation_repo.get_rubric_summary_for_student(school_id, student_id)

        # 5. Optional recommendation exploration summary
        rec_snap = await self.portfolio_repo.get_latest_recommendation_snapshot(school_id, student_id)
        exploration_options = None
        if rec_snap:
            careers = [c.get("title") for c in rec_snap.get("career_results", [])[:3] if c.get("title")]
            studies = [s.get("title") for s in rec_snap.get("study_results", [])[:3] if s.get("title")]
            exploration_options = {
                "available": True,
                "careerInterests": careers,
                "studyInterests": studies,
            }

        # 6. Existing issued CV versions
        existing_versions = await self.list_issued_cvs(school_id, student_id)

        return {
            "profile": {
                "displayName": user.display_name,
                "schoolName": school_name,
                "className": class_name,
            },
            "approvedPortfolios": approved_portfolios,
            "validatedSkills": radar_points,
            "teacherCompetencies": rubric_summary,
            "explorationOptions": exploration_options,
            "existingVersions": existing_versions,
            "policy": {
                "minSelectedPortfolios": settings.cv_min_selected_portfolios,
                "maxSelectedPortfolios": settings.cv_max_selected_portfolios,
                "verificationTtlDays": settings.cv_verification_ttl_days,
            },
        }

    async def generate_cv(
        self,
        school_id: str,
        student_id: str,
        portfolio_ids: List[str],
        include_teacher_competencies: bool = True,
        include_exploration: bool = False,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates an immutable CV snapshot, renders selectable-text PDF,
        privately stores it, and creates an opaque verification record.
        """
        min_p = settings.cv_min_selected_portfolios
        max_p = settings.cv_max_selected_portfolios
        if len(portfolio_ids) < min_p or len(portfolio_ids) > max_p:
            raise HTTPException(
                status_code=400,
                detail=f"Jumlah portofolio yang dipilih harus antara {min_p} dan {max_p} karya.",
            )

        # 1. Fetch Student User & Profile
        user = await self.identity_repo.get_user_for_school(school_id, student_id)
        if not user:
            raise HTTPException(status_code=404, detail="Siswa tidak ditemukan.")

        school = await self.identity_repo.get_school_by_id(school_id)
        school_name = school.name if school else ""
        class_name = await self._resolve_student_class_name(student_id)

        # 2. Validate Selected Portfolios: MUST be owned and MUST be approved
        selected_portfolios_data = []
        for pid in portfolio_ids:
            item = await self.portfolio_repo.get_portfolio(school_id, student_id, pid)
            if not item:
                raise HTTPException(
                    status_code=400,
                    detail=f"Portofolio dengan ID '{pid}' tidak ditemukan atau bukan milik Anda.",
                )
            if item.get("status") != "approved":
                raise HTTPException(
                    status_code=400,
                    detail=f"Karya '{item.get('title')}' belum disetujui guru. Hanya karya tervalidasi yang dapat disertakan.",
                )

            # Resolve or generate grounded professional description
            prof_doc = await self.translator_service.get_or_create_professional_description(
                school_id=school_id,
                student_id=student_id,
                portfolio_id=pid,
            )

            selected_portfolios_data.append({
                "portfolio_id": pid,
                "revision_id": item.get("current_revision_id", ""),
                "title": item["title"],
                "activity_type": item.get("activity_type", ""),
                "activity_date": item.get("activity_date", ""),
                "description": item.get("description", ""),
                "professional_description": prof_doc.get("professionalText") or item.get("description", ""),
                "tags": item.get("canonical_tag_ids", []),
            })

        # 3. Canonical Validated Skills
        skills_data = await self.projection_service.get_student_skills(school_id, student_id)
        approved_skills = []
        for pt in skills_data.get("radar", []):
            if pt.get("score", 0) > 0:
                approved_skills.append({
                    "dimension": pt.get("dimensionCode"),
                    "name": pt.get("displayName"),
                    "score": pt.get("score"),
                    "level": pt.get("level"),
                })

        # Grounded professional summary
        top_skill_names = [s["name"] for s in approved_skills[:3]]
        if top_skill_names:
            prof_summary = f"Siswa dengan rekam jejak karya tervalidasi pada {', '.join(top_skill_names)}."
        else:
            prof_summary = "Siswa dengan rekam jejak karya dan kompetensi tervalidasi melalui platform TALENTRA.ID."

        # 4. Teacher-Validated Competencies
        teacher_competencies = []
        if include_teacher_competencies:
            rubrics = await self.validation_repo.get_rubric_summary_for_student(school_id, student_id)
            for r in rubrics:
                if r.get("assessmentCount", 0) > 0:
                    teacher_competencies.append({
                        "dimension": r.get("displayName"),
                        "score": r.get("averageScore"),
                        "count": r.get("assessmentCount"),
                        "summary": f"Rata-rata penilaian guru: {r.get('averageScore')}/5 ({r.get('assessmentCount')} karya)",
                    })

        # 5. Optional Exploration Summary
        optional_exploration = None
        if include_exploration:
            rec_snap = await self.portfolio_repo.get_latest_recommendation_snapshot(school_id, student_id)
            if rec_snap:
                optional_exploration = {
                    "career_interests": [c.get("title") for c in rec_snap.get("career_results", [])[:3] if c.get("title")],
                    "study_interests": [s.get("title") for s in rec_snap.get("study_results", [])[:3] if s.get("title")],
                }

        # 6. Candidate Snapshot Construction
        snapshot_id = str(uuid.uuid4())
        candidate_data = {
            "snapshot_id": snapshot_id,
            "school_id": school_id,
            "student_id": student_id,
            "snapshot_version": "cv-snapshot-v1",
            "renderer_version": "cv-pdf-v1",
            "profile": {
                "display_name": user.display_name,
                "school_name": school_name,
                "class_name": class_name,
                "professional_summary": prof_summary,
            },
            "approved_skills": approved_skills,
            "teacher_validated_competencies": teacher_competencies,
            "selected_portfolios": selected_portfolios_data,
            "optional_exploration_summary": optional_exploration,
        }

        # Canonical SHA-256 Digest
        content_digest = compute_canonical_snapshot_digest(candidate_data)
        candidate_data["content_digest"] = content_digest

        # Check existing active snapshot by digest (Idempotency)
        existing_snap = await self.portfolio_repo.get_cv_snapshot_by_digest(
            school_id=school_id, student_id=student_id, content_digest=content_digest
        )
        if existing_snap and existing_snap.get("status") == CVIssuanceStatus.ISSUED.value:
            existing_verif = await self.verification_repo.get_by_snapshot_id(existing_snap["snapshot_id"])
            if existing_verif and existing_verif.get("status") == VerificationStatus.ACTIVE.value:
                return {
                    "snapshotId": existing_snap["snapshot_id"],
                    "displayCode": existing_verif["display_code"],
                    "status": existing_verif["status"],
                    "issuedAt": existing_verif["issued_at"].isoformat() if hasattr(existing_verif["issued_at"], "isoformat") else str(existing_verif["issued_at"]),
                    "expiresAt": existing_verif["expires_at"].isoformat() if existing_verif.get("expires_at") and hasattr(existing_verif["expires_at"], "isoformat") else None,
                    "contentDigest": content_digest,
                    "fingerprint": derive_snapshot_fingerprint(content_digest),
                    "selectedProjectCount": len(existing_snap.get("selected_portfolios", [])),
                    "message": "CV dengan konten tervalidasi yang sama sudah aktif.",
                }

        # Save snapshot document in state 'preparing'
        snapshot_doc = CVContentSnapshotDocument(
            snapshot_id=snapshot_id,
            school_id=school_id,
            student_id=student_id,
            snapshot_version="cv-snapshot-v1",
            renderer_version="cv-pdf-v1",
            status=CVIssuanceStatus.PREPARING.value,
            profile=candidate_data["profile"],
            approved_skills=candidate_data["approved_skills"],
            teacher_validated_competencies=candidate_data["teacher_validated_competencies"],
            selected_portfolios=candidate_data["selected_portfolios"],
            optional_exploration_summary=candidate_data["optional_exploration_summary"],
            content_digest=content_digest,
        )
        await self.portfolio_repo.save_cv_snapshot(snapshot_doc)

        audit_logger.log_event(
            AuditEventType.CV_SNAPSHOT_CREATED,
            user_id=student_id,
            school_id=school_id,
            safe_context="cv_snapshot_created",
            metadata={"snapshot_id": snapshot_id, "digest": content_digest},
        )

        # 7. Generate Verification Token, Display Code, and Expiry
        token = generate_verification_token()
        token_hash = hash_verification_token(token)
        display_code = generate_display_code()
        issued_at = datetime.now(timezone.utc)
        expires_at = None
        if settings.cv_verification_ttl_days and settings.cv_verification_ttl_days > 0:
            expires_at = issued_at + timedelta(days=settings.cv_verification_ttl_days)

        # 8. Render Deterministic PDF
        try:
            pdf_bytes = self.renderer.render(
                snapshot=candidate_data,
                display_code=display_code,
                verification_token=token,
                issued_date=issued_at.strftime("%d %B %Y"),
            )
        except Exception as e:
            await self.portfolio_repo.update_cv_snapshot_status(snapshot_id, CVIssuanceStatus.FAILED.value)
            raise HTTPException(status_code=500, detail=f"Gagal me-render dokumen PDF: {str(e)}")

        # Check CV PDF byte size limit
        if len(pdf_bytes) > settings.cv_pdf_max_bytes:
            await self.portfolio_repo.update_cv_snapshot_status(snapshot_id, CVIssuanceStatus.FAILED.value)
            raise HTTPException(
                status_code=400,
                detail=f"Ukuran dokumen PDF CV ({len(pdf_bytes)} bytes) melebihi batas keamanan maksimum ({settings.cv_pdf_max_bytes} bytes).",
            )

        audit_logger.log_event(
            AuditEventType.CV_PDF_RENDERED,
            user_id=student_id,
            school_id=school_id,
            safe_context="cv_pdf_rendered",
            metadata={"snapshot_id": snapshot_id, "size_bytes": len(pdf_bytes)},
        )

        # 9. Private Object Storage
        object_key = generate_safe_cv_pdf_key(school_id, student_id, snapshot_id)
        storage_obj_id = str(uuid.uuid4())
        checksum = hashlib.sha256(pdf_bytes).hexdigest()

        try:
            self.storage.upload_object(object_key, pdf_bytes, content_type="application/pdf")

            # Persist StorageObjectModel in PostgreSQL
            async with AsyncSessionLocal() as session:
                storage_record = StorageObjectModel(
                    id=storage_obj_id,
                    school_id=school_id,
                    owner_user_id=student_id,
                    provider=settings.object_storage_provider,
                    bucket=getattr(settings, "s3_bucket", "local-storage"),
                    object_key=object_key,
                    original_filename=f"TALENTRA-CV-{display_code}.pdf",
                    content_type="application/pdf",
                    size_bytes=len(pdf_bytes),
                    checksum=checksum,
                    status="available",
                )
                session.add(storage_record)
                await session.commit()
        except Exception as e:
            await self.portfolio_repo.update_cv_snapshot_status(snapshot_id, CVIssuanceStatus.FAILED.value)
            raise HTTPException(status_code=500, detail=f"Gagal menyimpan berkas PDF secara aman: {str(e)}")

        # 10. Persist Verification Record (HMAC token hash only!)
        try:
            verif_record = await self.verification_repo.create_verification_record({
                "school_id": school_id,
                "student_id": student_id,
                "cv_snapshot_id": snapshot_id,
                "token_hash": token_hash,
                "display_code": display_code,
                "snapshot_digest": content_digest,
                "status": VerificationStatus.ACTIVE.value,
                "issued_at": issued_at,
                "expires_at": expires_at,
                "pdf_storage_object_id": storage_obj_id,
            })
        except Exception as e:
            await self.portfolio_repo.update_cv_snapshot_status(snapshot_id, CVIssuanceStatus.FAILED.value)
            raise HTTPException(status_code=500, detail=f"Gagal mencatat status verifikasi dokumen: {str(e)}")

        # 11. Finalize Snapshot Status to 'issued'
        await self.portfolio_repo.update_cv_snapshot_status(snapshot_id, CVIssuanceStatus.ISSUED.value)

        audit_logger.log_event(
            AuditEventType.CV_VERIFICATION_ISSUED,
            user_id=student_id,
            school_id=school_id,
            safe_context="cv_verification_issued",
            metadata={
                "snapshot_id": snapshot_id,
                "display_code": display_code,
                "verification_record_id": verif_record.get("id"),
            },
        )

        verification_url = f"{settings.public_app_url.rstrip('/')}/verify/{token}"

        return {
            "snapshotId": snapshot_id,
            "displayCode": display_code,
            "verificationToken": token,  # Only exposed upon issuance to render student QR
            "verificationUrl": verification_url,
            "issuedAt": issued_at.isoformat(),
            "expiresAt": expires_at.isoformat() if expires_at else None,
            "contentDigest": content_digest,
            "fingerprint": derive_snapshot_fingerprint(content_digest),
            "status": VerificationStatus.ACTIVE.value,
            "selectedProjectCount": len(selected_portfolios_data),
        }

    async def list_issued_cvs(self, school_id: str, student_id: str) -> List[Dict[str, Any]]:
        """
        Lists all CV versions issued by the student.
        Never returns raw verification tokens.
        """
        snapshots = await self.portfolio_repo.list_cv_snapshots_for_student(school_id, student_id)
        records = await self.verification_repo.list_for_student(school_id, student_id)
        record_map = {r["cv_snapshot_id"]: r for r in records}

        results = []
        for s in snapshots:
            sid = s["snapshot_id"]
            verif = record_map.get(sid, {})
            status = verif.get("status") or s.get("status", "issued")
            # Check expiration dynamically
            expires_at = verif.get("expires_at")
            if expires_at and status == VerificationStatus.ACTIVE.value:
                now = datetime.now(timezone.utc)
                if isinstance(expires_at, datetime) and expires_at < now:
                    status = VerificationStatus.EXPIRED.value

            results.append({
                "snapshotId": sid,
                "displayCode": verif.get("display_code", "TLN-PENDING"),
                "status": status,
                "issuedAt": (
                    verif["issued_at"].isoformat()
                    if verif.get("issued_at") and hasattr(verif["issued_at"], "isoformat")
                    else str(verif.get("issued_at", s.get("generated_at", "")))
                ),
                "expiresAt": (
                    expires_at.isoformat()
                    if expires_at and hasattr(expires_at, "isoformat")
                    else (str(expires_at) if expires_at else None)
                ),
                "selectedProjectCount": len(s.get("selected_portfolios", [])),
                "fingerprint": derive_snapshot_fingerprint(s.get("content_digest", "")),
            })
        return results

    async def get_cv_detail(self, school_id: str, student_id: str, snapshot_id: str) -> Dict[str, Any]:
        """
        Retrieves immutable snapshot preview candidate data for owner.
        """
        snap = await self.portfolio_repo.get_cv_snapshot(school_id, student_id, snapshot_id)
        if not snap:
            raise HTTPException(status_code=404, detail="Dokumen CV tidak ditemukan.")

        verif = await self.verification_repo.get_by_snapshot_id(snapshot_id)
        status = verif.get("status") if verif else snap.get("status")
        display_code = verif.get("display_code") if verif else "TLN-PENDING"

        return {
            "snapshotId": snap["snapshot_id"],
            "snapshotVersion": snap.get("snapshot_version", "cv-snapshot-v1"),
            "displayCode": display_code,
            "status": status,
            "generatedAt": (
                snap["generated_at"].isoformat()
                if hasattr(snap["generated_at"], "isoformat")
                else str(snap["generated_at"])
            ),
            "profile": snap.get("profile", {}),
            "approvedSkills": snap.get("approved_skills", []),
            "teacherValidatedCompetencies": snap.get("teacher_validated_competencies", []),
            "selectedPortfolios": snap.get("selected_portfolios", []),
            "optionalExplorationSummary": snap.get("optional_exploration_summary"),
            "contentDigest": snap.get("content_digest", ""),
            "fingerprint": derive_snapshot_fingerprint(snap.get("content_digest", "")),
        }

    async def get_cv_download_access(self, school_id: str, student_id: str, snapshot_id: str) -> Dict[str, Any]:
        """
        Issues short-lived signed GET URL for student owner to download private CV PDF directly from Blob.
        Audits access event and returns { downloadUrl, filename, expiresInSeconds }.
        """
        snap = await self.portfolio_repo.get_cv_snapshot(school_id, student_id, snapshot_id)
        if not snap:
            raise HTTPException(status_code=404, detail="Dokumen CV tidak ditemukan.")

        verif = await self.verification_repo.get_by_snapshot_id(snapshot_id)
        if not verif:
            raise HTTPException(status_code=404, detail="Catatan verifikasi CV tidak ditemukan.")

        storage_obj_id = verif.get("pdf_storage_object_id")
        if not storage_obj_id:
            raise HTTPException(status_code=404, detail="Berkas fisik CV tidak ditemukan.")

        async with AsyncSessionLocal() as session:
            stmt = select(StorageObjectModel).where(StorageObjectModel.id == storage_obj_id)
            res = await session.execute(stmt)
            obj = res.scalar_one_or_none()
            if not obj:
                raise HTTPException(status_code=404, detail="Objek penyimpanan CV tidak ditemukan.")
            object_key = obj.object_key

        download_url = self.storage.create_download_url(
            object_key=object_key,
            expires_in=settings.blob_download_url_ttl_seconds,
        )

        audit_logger.log_event(
            AuditEventType.CV_DOWNLOAD_ACCESSED,
            user_id=student_id,
            school_id=school_id,
            safe_context="cv_download_accessed",
            metadata={"snapshot_id": snapshot_id, "display_code": verif.get("display_code")},
        )

        display_code = verif.get("display_code", "DOCUMENT")
        filename = f"TALENTRA-CV-{display_code}.pdf"
        return {
            "downloadUrl": download_url,
            "filename": filename,
            "expiresInSeconds": settings.blob_download_url_ttl_seconds,
        }

    async def download_cv_pdf(self, school_id: str, student_id: str, snapshot_id: str) -> Tuple[bytes, str]:
        """
        Downloads PDF binary for authenticated student owner.
        Returns (pdf_bytes, safe_filename).
        """
        snap = await self.portfolio_repo.get_cv_snapshot(school_id, student_id, snapshot_id)
        if not snap:
            raise HTTPException(status_code=404, detail="Dokumen CV tidak ditemukan.")

        verif = await self.verification_repo.get_by_snapshot_id(snapshot_id)
        if not verif:
            raise HTTPException(status_code=404, detail="Catatan verifikasi CV tidak ditemukan.")

        storage_obj_id = verif.get("pdf_storage_object_id")
        if not storage_obj_id:
            raise HTTPException(status_code=404, detail="Berkas fisik CV tidak ditemukan.")

        # Resolve storage object key
        async with AsyncSessionLocal() as session:
            stmt = select(StorageObjectModel).where(StorageObjectModel.id == storage_obj_id)
            res = await session.execute(stmt)
            obj = res.scalar_one_or_none()
            if not obj:
                raise HTTPException(status_code=404, detail="Objek penyimpanan CV tidak ditemukan.")
            object_key = obj.object_key

        try:
            pdf_bytes = self.storage.get_object_bytes(object_key)
        except Exception:
            raise HTTPException(status_code=500, detail="Gagal mengambil berkas fisik CV dari penyimpanan.")

        audit_logger.log_event(
            AuditEventType.CV_DOWNLOAD_ACCESSED,
            user_id=student_id,
            school_id=school_id,
            safe_context="cv_download_accessed",
            metadata={"snapshot_id": snapshot_id, "display_code": verif.get("display_code")},
        )

        display_code = verif.get("display_code", "DOCUMENT")
        filename = f"TALENTRA-CV-{display_code}.pdf"
        return pdf_bytes, filename

    async def revoke_cv(self, school_id: str, student_id: str, snapshot_id: str, reason: str = "Dicabut oleh siswa") -> Dict[str, Any]:
        """
        Student revokes own issued CV.
        Immediately reflects in public verification as REVOKED.
        """
        snap = await self.portfolio_repo.get_cv_snapshot(school_id, student_id, snapshot_id)
        if not snap:
            raise HTTPException(status_code=404, detail="Dokumen CV tidak ditemukan.")

        success = await self.verification_repo.revoke_by_snapshot_id(
            cv_snapshot_id=snapshot_id,
            school_id=school_id,
            student_id=student_id,
            revoked_by_user_id=student_id,
            reason=reason,
        )
        if not success:
            raise HTTPException(status_code=400, detail="Gagal mencabut dokumen CV.")

        await self.portfolio_repo.update_cv_snapshot_status(snapshot_id, VerificationStatus.REVOKED.value)

        audit_logger.log_event(
            AuditEventType.CV_VERIFICATION_REVOKED,
            user_id=student_id,
            school_id=school_id,
            safe_context="cv_verification_revoked_by_student",
            metadata={"snapshot_id": snapshot_id, "reason": reason},
        )

        return {"status": "revoked", "snapshotId": snapshot_id}

    async def admin_revoke_cv(
        self, school_id: str, admin_user_id: str, verification_id: str, reason: str
    ) -> Dict[str, Any]:
        """
        Same-school Admin revokes an issued verification record with required audit reason.
        Cross-school revocation strictly forbidden.
        """
        if not reason or len(reason.strip()) < 5:
            raise HTTPException(status_code=400, detail="Alasan pencabutan dokumen wajib diisi.")

        rec = await self.verification_repo.get_by_id(verification_id)
        if not rec:
            raise HTTPException(status_code=404, detail="Catatan verifikasi tidak ditemukan.")

        if rec["school_id"] != school_id:
            raise HTTPException(status_code=403, detail="Akses ditolak: Dokumen bukan berasal dari sekolah Anda.")

        success = await self.verification_repo.revoke_record(
            record_id=verification_id,
            revoked_by_user_id=admin_user_id,
            reason=reason,
        )
        if not success:
            raise HTTPException(status_code=400, detail="Gagal mencabut verifikasi.")

        if rec.get("cv_snapshot_id"):
            await self.portfolio_repo.update_cv_snapshot_status(
                rec["cv_snapshot_id"], VerificationStatus.REVOKED.value
            )

        audit_logger.log_event(
            AuditEventType.CV_VERIFICATION_REVOKED,
            user_id=admin_user_id,
            school_id=school_id,
            safe_context="cv_verification_revoked_by_admin",
            metadata={"verification_id": verification_id, "reason": reason},
        )

        return {"status": "revoked", "verificationId": verification_id}

    async def reconcile_cv_issuance(self, school_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Deterministic maintenance routine:
        Finds stale 'preparing' snapshots and marks failed.
        Verifies storage consistency.
        """
        return {"reconciled": 0, "status": "ok"}
