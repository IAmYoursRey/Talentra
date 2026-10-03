import uuid
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from abc import ABC, abstractmethod
from sqlalchemy import select, update, delete, desc, asc, and_, or_, func

from ..core.mongodb import mongo_manager
from ..core.database import AsyncSessionLocal
from ..core.config import settings
from ..db.models import (
    PortfolioItemModel,
    PortfolioRevisionModel,
    EvidenceTagSnapshotModel,
    RecommendationSnapshotModel,
    DerivedProfessionalDescriptionModel,
    CVContentSnapshotModel,
)
from ..domain.documents import (
    PortfolioItemDocument,
    PortfolioRevisionDocument,
    EvidenceRef,
    EvidenceTagSnapshotDocument,
    RecommendationSnapshotDocument,
    DerivedProfessionalDescriptionDocument,
    CVContentSnapshotDocument,
)


class PortfolioRepository(ABC):
    @abstractmethod
    async def create_portfolio(
        self,
        school_id: str,
        student_id: str,
        title: str,
        activity_type: str,
        activity_date: str,
        description: str,
        canonical_tag_ids: List[str],
        evidence_refs: List[EvidenceRef],
    ) -> Tuple[PortfolioItemDocument, PortfolioRevisionDocument]:
        pass

    @abstractmethod
    async def get_portfolio(
        self, school_id: str, student_id: str, portfolio_id: str
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_portfolio_by_id(
        self, school_id: str, portfolio_id: str
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_revision_by_id(
        self, revision_id: str
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def list_portfolios(
        self,
        school_id: str,
        student_id: str,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        activity_type: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "newest",
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        pass

    @abstractmethod
    async def list_teacher_queue(
        self,
        school_id: str,
        eligible_student_ids: List[str],
        tag: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "oldest",
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        pass

    @abstractmethod
    async def update_draft(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
        update_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def atomic_submit(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
        expected_revision: int,
        submission_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def atomic_transition_review(
        self,
        school_id: str,
        portfolio_id: str,
        expected_revision_id: str,
        target_status: str,
        feedback: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def begin_revision(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def delete_draft(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
    ) -> bool:
        pass

    @abstractmethod
    async def save_evidence_tag_snapshot(
        self, snapshot: EvidenceTagSnapshotDocument
    ) -> EvidenceTagSnapshotDocument:
        pass

    @abstractmethod
    async def get_evidence_tag_snapshots_for_student(
        self, school_id: str, student_id: str
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_evidence_tag_snapshots_for_cohort(
        self, school_id: str, student_ids: List[str]
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def delete_evidence_tag_snapshots_for_student(
        self, school_id: str, student_id: str
    ) -> int:
        pass

    @abstractmethod
    async def get_snapshot_by_decision_id(
        self, decision_id: str
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def save_recommendation_snapshot(
        self, snapshot: RecommendationSnapshotDocument
    ) -> RecommendationSnapshotDocument:
        pass

    @abstractmethod
    async def get_latest_recommendation_snapshot(
        self, school_id: str, student_id: str
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def save_professional_description(
        self, doc: DerivedProfessionalDescriptionDocument
    ) -> DerivedProfessionalDescriptionDocument:
        pass

    @abstractmethod
    async def get_professional_description(
        self, school_id: str, student_id: str, portfolio_id: str
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def save_cv_snapshot(
        self, snapshot: CVContentSnapshotDocument
    ) -> CVContentSnapshotDocument:
        pass

    @abstractmethod
    async def get_cv_snapshot(
        self, school_id: str, student_id: str, snapshot_id: str
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_cv_snapshot_by_id(
        self, snapshot_id: str
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def list_cv_snapshots_for_student(
        self, school_id: str, student_id: str
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def update_cv_snapshot_status(
        self, snapshot_id: str, status: str
    ) -> bool:
        pass

    @abstractmethod
    async def get_cv_snapshot_by_digest(
        self, school_id: str, student_id: str, content_digest: str
    ) -> Optional[Dict[str, Any]]:
        pass


class PostgresPortfolioRepository(PortfolioRepository):
    """
    Authoritative single-store PostgreSQL repository (optimized for Neon Serverless).
    Preserves strict tenant isolation, immutable revision snapshots, and approved-only evidence contracts.
    """

    def __init__(self, session_factory=None):
        self.session_factory = session_factory or AsyncSessionLocal

    @staticmethod
    def _item_to_dict(model: PortfolioItemModel) -> Dict[str, Any]:
        return {
            "portfolio_id": model.id,
            "id": model.id,
            "school_id": model.school_id,
            "student_id": model.student_id,
            "title": model.title,
            "activity_type": model.activity_type,
            "activity_date": model.activity_date,
            "description": model.description,
            "canonical_tag_ids": list(model.canonical_tag_ids or []),
            "evidence_refs": list(model.evidence_refs or []),
            "status": model.status,
            "current_revision_id": model.current_revision_id,
            "current_revision": model.current_revision,
            "current_revision_number": model.current_revision_number,
            "teacher_feedback": model.teacher_feedback,
            "submitted_at": model.submitted_at,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    @staticmethod
    def _revision_to_dict(model: PortfolioRevisionModel) -> Dict[str, Any]:
        return {
            "revision_id": model.id,
            "id": model.id,
            "portfolio_id": model.portfolio_id,
            "school_id": model.school_id,
            "student_id": model.student_id,
            "version": model.version,
            "title_snapshot": model.title_snapshot,
            "activity_type_snapshot": model.activity_type_snapshot,
            "description_snapshot": model.description_snapshot,
            "tag_snapshot": list(model.tag_snapshot or []),
            "evidence_refs": list(model.evidence_refs or []),
            "submitted_at": model.submitted_at,
            "created_at": model.created_at,
        }

    @staticmethod
    def _snapshot_to_dict(model: EvidenceTagSnapshotModel) -> Dict[str, Any]:
        return {
            "snapshot_id": model.id,
            "id": model.id,
            "school_id": model.school_id,
            "student_id": model.student_id,
            "portfolio_id": model.portfolio_id,
            "revision_id": model.revision_id,
            "validation_decision_id": model.validation_decision_id,
            "canonical_tag_ids": list(model.canonical_tag_ids or []),
            "canonical_tag_codes": list(model.canonical_tag_codes or []),
            "approved_at": model.approved_at,
            "projection_version": model.projection_version,
            "created_at": model.created_at,
        }

    @staticmethod
    def _recommendation_to_dict(model: RecommendationSnapshotModel) -> Dict[str, Any]:
        return {
            "snapshot_id": model.id,
            "id": model.id,
            "school_id": model.school_id,
            "student_id": model.student_id,
            "source_fingerprint": model.source_fingerprint,
            "catalog_version": model.catalog_version,
            "scoring_version": model.scoring_version,
            "mapping_version": model.mapping_version,
            "evidence_confidence": dict(model.evidence_confidence or {}),
            "career_results": list(model.career_results or []),
            "study_results": list(model.study_results or []),
            "supporting_approval_ids": list(model.supporting_approval_ids or []),
            "generated_at": model.generated_at,
        }

    @staticmethod
    def _description_to_dict(model: DerivedProfessionalDescriptionModel) -> Dict[str, Any]:
        return {
            "document_id": model.id,
            "id": model.id,
            "school_id": model.school_id,
            "student_id": model.student_id,
            "portfolio_id": model.portfolio_id,
            "revision_id": model.revision_id,
            "source_hash": model.source_hash,
            "original_title": model.original_title,
            "professional_text": model.professional_text,
            "translator_version": model.translator_version,
            "mode": model.mode,
            "generated_at": model.generated_at,
        }

    @staticmethod
    def _cv_snapshot_to_dict(model: CVContentSnapshotModel) -> Dict[str, Any]:
        return {
            "snapshot_id": model.id,
            "id": model.id,
            "school_id": model.school_id,
            "student_id": model.student_id,
            "snapshot_version": model.snapshot_version,
            "renderer_version": model.renderer_version,
            "status": model.status,
            "profile": dict(model.profile or {}),
            "approved_skills": list(model.approved_skills or []),
            "teacher_validated_competencies": list(model.teacher_validated_competencies or []),
            "selected_portfolios": list(model.selected_portfolios or []),
            "optional_exploration_summary": dict(model.optional_exploration_summary) if model.optional_exploration_summary else None,
            "content_digest": model.content_digest,
            "pdf_storage_key": model.pdf_storage_key,
            "generated_at": model.generated_at,
        }

    async def create_portfolio(
        self,
        school_id: str,
        student_id: str,
        title: str,
        activity_type: str,
        activity_date: str,
        description: str,
        canonical_tag_ids: List[str],
        evidence_refs: List[EvidenceRef],
    ) -> Tuple[PortfolioItemDocument, PortfolioRevisionDocument]:
        portfolio_id = str(uuid.uuid4())
        revision_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        doc = PortfolioItemDocument(
            portfolio_id=portfolio_id,
            school_id=school_id,
            student_id=student_id,
            title=title,
            activity_type=activity_type,
            activity_date=activity_date,
            description=description,
            canonical_tag_ids=canonical_tag_ids,
            evidence_refs=evidence_refs,
            status="draft",
            current_revision_id=revision_id,
            current_revision_number=1,
            current_revision=1,
            created_at=now,
            updated_at=now,
        )

        rev = PortfolioRevisionDocument(
            revision_id=revision_id,
            portfolio_id=portfolio_id,
            school_id=school_id,
            student_id=student_id,
            version=1,
            title_snapshot=title,
            activity_type_snapshot=activity_type,
            description_snapshot=description,
            tag_snapshot=canonical_tag_ids,
            evidence_refs=evidence_refs,
            created_at=now,
        )

        ev_dicts = [ref.model_dump() if hasattr(ref, "model_dump") else dict(ref) for ref in evidence_refs]

        item_model = PortfolioItemModel(
            id=portfolio_id,
            school_id=school_id,
            student_id=student_id,
            title=title,
            activity_type=activity_type,
            activity_date=activity_date,
            description=description,
            canonical_tag_ids=list(canonical_tag_ids),
            evidence_refs=ev_dicts,
            status="draft",
            current_revision_id=revision_id,
            current_revision=1,
            current_revision_number=1,
            created_at=now,
            updated_at=now,
        )

        rev_model = PortfolioRevisionModel(
            id=revision_id,
            portfolio_id=portfolio_id,
            school_id=school_id,
            student_id=student_id,
            version=1,
            title_snapshot=title,
            activity_type_snapshot=activity_type,
            description_snapshot=description,
            tag_snapshot=list(canonical_tag_ids),
            evidence_refs=ev_dicts,
            created_at=now,
        )

        async with self.session_factory() as session:
            session.add(item_model)
            session.add(rev_model)
            await session.commit()

        return doc, rev

    async def get_portfolio(
        self, school_id: str, student_id: str, portfolio_id: str
    ) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(PortfolioItemModel).where(
                PortfolioItemModel.id == portfolio_id,
                PortfolioItemModel.school_id == school_id,
                PortfolioItemModel.student_id == student_id,
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            return self._item_to_dict(model) if model else None

    async def get_portfolio_by_id(
        self, school_id: str, portfolio_id: str
    ) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(PortfolioItemModel).where(
                PortfolioItemModel.id == portfolio_id,
                PortfolioItemModel.school_id == school_id,
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            return self._item_to_dict(model) if model else None

    async def get_revision_by_id(
        self, revision_id: str
    ) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(PortfolioRevisionModel).where(PortfolioRevisionModel.id == revision_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            return self._revision_to_dict(model) if model else None

    async def list_portfolios(
        self,
        school_id: str,
        student_id: str,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        activity_type: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "newest",
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        async with self.session_factory() as session:
            conditions = [
                PortfolioItemModel.school_id == school_id,
                PortfolioItemModel.student_id == student_id,
            ]
            if status and status != "all":
                conditions.append(PortfolioItemModel.status == status)
            if activity_type and activity_type != "all":
                conditions.append(PortfolioItemModel.activity_type == activity_type)
            if search and search.strip():
                term = f"%{search.strip().lower()}%"
                conditions.append(
                    or_(
                        func.lower(PortfolioItemModel.title).like(term),
                        func.lower(PortfolioItemModel.description).like(term),
                    )
                )

            stmt = select(PortfolioItemModel).where(and_(*conditions))
            if sort_by == "newest":
                stmt = stmt.order_by(desc(PortfolioItemModel.created_at))
            else:
                stmt = stmt.order_by(asc(PortfolioItemModel.created_at))

            res = await session.execute(stmt)
            all_items = res.scalars().all()

            if tag and tag != "all":
                filtered = [m for m in all_items if tag in (m.canonical_tag_ids or [])]
            else:
                filtered = list(all_items)

            total = len(filtered)
            paged = filtered[offset : offset + limit]
            return [self._item_to_dict(m) for m in paged], total

    async def list_teacher_queue(
        self,
        school_id: str,
        eligible_student_ids: List[str],
        tag: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "oldest",
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        if not eligible_student_ids:
            return [], 0

        async with self.session_factory() as session:
            conditions = [
                PortfolioItemModel.school_id == school_id,
                PortfolioItemModel.student_id.in_(eligible_student_ids),
                PortfolioItemModel.status == "submitted",
            ]
            if search and search.strip():
                term = f"%{search.strip().lower()}%"
                conditions.append(
                    or_(
                        func.lower(PortfolioItemModel.title).like(term),
                        func.lower(PortfolioItemModel.description).like(term),
                    )
                )

            stmt = select(PortfolioItemModel).where(and_(*conditions))
            if sort_by == "oldest":
                stmt = stmt.order_by(asc(PortfolioItemModel.submitted_at))
            else:
                stmt = stmt.order_by(desc(PortfolioItemModel.submitted_at))

            res = await session.execute(stmt)
            all_items = res.scalars().all()

            if tag and tag != "all":
                filtered = [m for m in all_items if tag in (m.canonical_tag_ids or [])]
            else:
                filtered = list(all_items)

            total = len(filtered)
            paged = filtered[offset : offset + limit]
            return [self._item_to_dict(m) for m in paged], total

    async def update_draft(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
        update_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(PortfolioItemModel).where(
                PortfolioItemModel.id == portfolio_id,
                PortfolioItemModel.school_id == school_id,
                PortfolioItemModel.student_id == student_id,
                PortfolioItemModel.status == "draft",
            )
            res = await session.execute(stmt)
            item = res.scalar_one_or_none()
            if not item:
                return None

            for key, val in update_data.items():
                if key == "evidence_refs" and val is not None:
                    item.evidence_refs = [r.model_dump() if hasattr(r, "model_dump") else dict(r) for r in val]
                elif hasattr(item, key):
                    setattr(item, key, val)

            item.updated_at = datetime.now(timezone.utc)
            await session.commit()
            return self._item_to_dict(item)

    async def atomic_submit(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
        expected_revision: int,
        submission_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        async with self.session_factory() as session:
            stmt = select(PortfolioItemModel).where(
                PortfolioItemModel.id == portfolio_id,
                PortfolioItemModel.school_id == school_id,
                PortfolioItemModel.student_id == student_id,
                PortfolioItemModel.status.in_(["draft", "revision_requested"]),
            )
            res = await session.execute(stmt)
            item = res.scalar_one_or_none()
            if not item:
                return None

            new_revision_id = str(uuid.uuid4())
            new_rev_number = item.current_revision_number + 1

            for key, val in submission_data.items():
                if key == "evidence_refs" and val is not None:
                    item.evidence_refs = [r.model_dump() if hasattr(r, "model_dump") else dict(r) for r in val]
                elif hasattr(item, key):
                    setattr(item, key, val)

            item.status = "submitted"
            item.current_revision_id = new_revision_id
            item.current_revision_number = new_rev_number
            item.submitted_at = now
            item.updated_at = now

            rev_model = PortfolioRevisionModel(
                id=new_revision_id,
                portfolio_id=portfolio_id,
                school_id=school_id,
                student_id=student_id,
                version=new_rev_number,
                title_snapshot=item.title,
                activity_type_snapshot=item.activity_type,
                description_snapshot=item.description,
                tag_snapshot=list(item.canonical_tag_ids or []),
                evidence_refs=list(item.evidence_refs or []),
                submitted_at=now,
                created_at=now,
            )
            session.add(rev_model)
            await session.commit()
            return self._item_to_dict(item)

    async def atomic_transition_review(
        self,
        school_id: str,
        portfolio_id: str,
        expected_revision_id: str,
        target_status: str,
        feedback: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        async with self.session_factory() as session:
            stmt = select(PortfolioItemModel).where(
                PortfolioItemModel.id == portfolio_id,
                PortfolioItemModel.school_id == school_id,
                PortfolioItemModel.current_revision_id == expected_revision_id,
                PortfolioItemModel.status == "submitted",
            )
            res = await session.execute(stmt)
            item = res.scalar_one_or_none()
            if not item:
                return None

            item.status = target_status
            item.teacher_feedback = feedback
            item.updated_at = now
            await session.commit()
            return self._item_to_dict(item)

    async def begin_revision(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
    ) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(PortfolioItemModel).where(
                PortfolioItemModel.id == portfolio_id,
                PortfolioItemModel.school_id == school_id,
                PortfolioItemModel.student_id == student_id,
                PortfolioItemModel.status == "revision_requested",
            )
            res = await session.execute(stmt)
            item = res.scalar_one_or_none()
            if not item:
                return None

            item.status = "draft"
            item.updated_at = datetime.now(timezone.utc)
            await session.commit()
            return self._item_to_dict(item)

    async def delete_draft(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(PortfolioItemModel).where(
                PortfolioItemModel.id == portfolio_id,
                PortfolioItemModel.school_id == school_id,
                PortfolioItemModel.student_id == student_id,
                PortfolioItemModel.status == "draft",
            )
            res = await session.execute(stmt)
            item = res.scalar_one_or_none()
            if not item:
                return False

            await session.delete(item)
            await session.commit()
            return True

    async def save_evidence_tag_snapshot(
        self, snapshot: EvidenceTagSnapshotDocument
    ) -> EvidenceTagSnapshotDocument:
        model = EvidenceTagSnapshotModel(
            id=snapshot.snapshot_id,
            school_id=snapshot.school_id,
            student_id=snapshot.student_id,
            portfolio_id=snapshot.portfolio_id,
            revision_id=snapshot.revision_id,
            validation_decision_id=snapshot.validation_decision_id,
            canonical_tag_ids=list(snapshot.canonical_tag_ids),
            canonical_tag_codes=list(snapshot.canonical_tag_codes),
            approved_at=snapshot.approved_at,
            projection_version=snapshot.projection_version,
            created_at=datetime.now(timezone.utc),
        )
        async with self.session_factory() as session:
            session.add(model)
            await session.commit()
        return snapshot

    async def get_evidence_tag_snapshots_for_student(
        self, school_id: str, student_id: str
    ) -> List[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(EvidenceTagSnapshotModel).where(
                EvidenceTagSnapshotModel.school_id == school_id,
                EvidenceTagSnapshotModel.student_id == student_id,
            ).order_by(asc(EvidenceTagSnapshotModel.approved_at))
            res = await session.execute(stmt)
            return [self._snapshot_to_dict(m) for m in res.scalars().all()]

    async def get_evidence_tag_snapshots_for_cohort(
        self, school_id: str, student_ids: List[str]
    ) -> List[Dict[str, Any]]:
        if not student_ids:
            return []
        async with self.session_factory() as session:
            stmt = select(EvidenceTagSnapshotModel).where(
                EvidenceTagSnapshotModel.school_id == school_id,
                EvidenceTagSnapshotModel.student_id.in_(student_ids),
            ).order_by(asc(EvidenceTagSnapshotModel.approved_at))
            res = await session.execute(stmt)
            return [self._snapshot_to_dict(m) for m in res.scalars().all()]

    async def delete_evidence_tag_snapshots_for_student(
        self, school_id: str, student_id: str
    ) -> int:
        async with self.session_factory() as session:
            stmt = delete(EvidenceTagSnapshotModel).where(
                EvidenceTagSnapshotModel.school_id == school_id,
                EvidenceTagSnapshotModel.student_id == student_id,
            )
            res = await session.execute(stmt)
            await session.commit()
            return res.rowcount or 0

    async def get_snapshot_by_decision_id(
        self, decision_id: str
    ) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(EvidenceTagSnapshotModel).where(
                EvidenceTagSnapshotModel.validation_decision_id == decision_id
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            return self._snapshot_to_dict(model) if model else None

    async def save_recommendation_snapshot(
        self, snapshot: RecommendationSnapshotDocument
    ) -> RecommendationSnapshotDocument:
        model = RecommendationSnapshotModel(
            id=snapshot.snapshot_id,
            school_id=snapshot.school_id,
            student_id=snapshot.student_id,
            source_fingerprint=snapshot.source_fingerprint,
            catalog_version=snapshot.catalog_version,
            scoring_version=snapshot.scoring_version,
            mapping_version=snapshot.mapping_version,
            evidence_confidence=dict(snapshot.evidence_confidence),
            career_results=list(snapshot.career_results),
            study_results=list(snapshot.study_results),
            supporting_approval_ids=list(snapshot.supporting_approval_ids),
            generated_at=snapshot.generated_at,
        )
        async with self.session_factory() as session:
            session.add(model)
            await session.commit()
        return snapshot

    async def get_latest_recommendation_snapshot(
        self, school_id: str, student_id: str
    ) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(RecommendationSnapshotModel).where(
                RecommendationSnapshotModel.school_id == school_id,
                RecommendationSnapshotModel.student_id == student_id,
            ).order_by(desc(RecommendationSnapshotModel.generated_at)).limit(1)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            return self._recommendation_to_dict(model) if model else None

    async def save_professional_description(
        self, doc: DerivedProfessionalDescriptionDocument
    ) -> DerivedProfessionalDescriptionDocument:
        async with self.session_factory() as session:
            stmt = select(DerivedProfessionalDescriptionModel).where(
                DerivedProfessionalDescriptionModel.portfolio_id == doc.portfolio_id,
                DerivedProfessionalDescriptionModel.school_id == doc.school_id,
                DerivedProfessionalDescriptionModel.student_id == doc.student_id,
            )
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                existing.revision_id = doc.revision_id
                existing.source_hash = doc.source_hash
                existing.original_title = doc.original_title
                existing.professional_text = doc.professional_text
                existing.translator_version = doc.translator_version
                existing.mode = doc.mode
                existing.generated_at = doc.generated_at
            else:
                model = DerivedProfessionalDescriptionModel(
                    id=doc.document_id,
                    school_id=doc.school_id,
                    student_id=doc.student_id,
                    portfolio_id=doc.portfolio_id,
                    revision_id=doc.revision_id,
                    source_hash=doc.source_hash,
                    original_title=doc.original_title,
                    professional_text=doc.professional_text,
                    translator_version=doc.translator_version,
                    mode=doc.mode,
                    generated_at=doc.generated_at,
                )
                session.add(model)
            await session.commit()
        return doc

    async def get_professional_description(
        self, school_id: str, student_id: str, portfolio_id: str
    ) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(DerivedProfessionalDescriptionModel).where(
                DerivedProfessionalDescriptionModel.portfolio_id == portfolio_id,
                DerivedProfessionalDescriptionModel.school_id == school_id,
                DerivedProfessionalDescriptionModel.student_id == student_id,
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            return self._description_to_dict(model) if model else None

    async def save_cv_snapshot(
        self, snapshot: CVContentSnapshotDocument
    ) -> CVContentSnapshotDocument:
        model = CVContentSnapshotModel(
            id=snapshot.snapshot_id,
            school_id=snapshot.school_id,
            student_id=snapshot.student_id,
            snapshot_version=snapshot.snapshot_version,
            renderer_version=snapshot.renderer_version,
            status=snapshot.status,
            profile=dict(snapshot.profile),
            approved_skills=list(snapshot.approved_skills),
            teacher_validated_competencies=list(snapshot.teacher_validated_competencies),
            selected_portfolios=list(snapshot.selected_portfolios),
            optional_exploration_summary=dict(snapshot.optional_exploration_summary) if snapshot.optional_exploration_summary else None,
            content_digest=snapshot.content_digest,
            pdf_storage_key=None,
            generated_at=snapshot.generated_at,
        )
        async with self.session_factory() as session:
            session.add(model)
            await session.commit()
        return snapshot

    async def get_cv_snapshot(
        self, school_id: str, student_id: str, snapshot_id: str
    ) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(CVContentSnapshotModel).where(
                CVContentSnapshotModel.id == snapshot_id,
                CVContentSnapshotModel.school_id == school_id,
                CVContentSnapshotModel.student_id == student_id,
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            return self._cv_snapshot_to_dict(model) if model else None

    async def get_cv_snapshot_by_id(
        self, snapshot_id: str
    ) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(CVContentSnapshotModel).where(
                CVContentSnapshotModel.id == snapshot_id
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            return self._cv_snapshot_to_dict(model) if model else None

    async def list_cv_snapshots_for_student(
        self, school_id: str, student_id: str
    ) -> List[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(CVContentSnapshotModel).where(
                CVContentSnapshotModel.school_id == school_id,
                CVContentSnapshotModel.student_id == student_id,
            ).order_by(desc(CVContentSnapshotModel.generated_at))
            res = await session.execute(stmt)
            return [self._cv_snapshot_to_dict(m) for m in res.scalars().all()]

    async def update_cv_snapshot_status(
        self, snapshot_id: str, status: str
    ) -> bool:
        async with self.session_factory() as session:
            stmt = select(CVContentSnapshotModel).where(CVContentSnapshotModel.id == snapshot_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return False
            model.status = status
            await session.commit()
            return True

    async def get_cv_snapshot_by_digest(
        self, school_id: str, student_id: str, content_digest: str
    ) -> Optional[Dict[str, Any]]:
        async with self.session_factory() as session:
            stmt = select(CVContentSnapshotModel).where(
                CVContentSnapshotModel.school_id == school_id,
                CVContentSnapshotModel.student_id == student_id,
                CVContentSnapshotModel.content_digest == content_digest,
                CVContentSnapshotModel.status != "revoked",
            ).order_by(desc(CVContentSnapshotModel.generated_at)).limit(1)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            return self._cv_snapshot_to_dict(model) if model else None



class MongoPortfolioRepository(PortfolioRepository):
    """
    Production repository using official PyMongo Async API.
    All queries strictly carry school_id + student_id tenant & ownership bounds.
    """

    def __init__(self):
        self._manager = mongo_manager

    @property
    def db(self):
        return self._manager.get_db()

    async def create_portfolio(
        self,
        school_id: str,
        student_id: str,
        title: str,
        activity_type: str,
        activity_date: str,
        description: str,
        canonical_tag_ids: List[str],
        evidence_refs: List[EvidenceRef],
    ) -> Tuple[PortfolioItemDocument, PortfolioRevisionDocument]:
        portfolio_id = str(uuid.uuid4())
        revision_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        doc = PortfolioItemDocument(
            portfolio_id=portfolio_id,
            school_id=school_id,
            student_id=student_id,
            title=title,
            activity_type=activity_type,
            activity_date=activity_date,
            description=description,
            canonical_tag_ids=canonical_tag_ids,
            evidence_refs=evidence_refs,
            status="draft",
            current_revision_id=revision_id,
            current_revision_number=1,
            created_at=now,
            updated_at=now,
        )

        rev = PortfolioRevisionDocument(
            revision_id=revision_id,
            portfolio_id=portfolio_id,
            school_id=school_id,
            student_id=student_id,
            version=1,
            title_snapshot=title,
            activity_type_snapshot=activity_type,
            description_snapshot=description,
            tag_snapshot=canonical_tag_ids,
            evidence_refs=evidence_refs,
            created_at=now,
        )

        await self.db["portfolio_items"].insert_one(doc.model_dump())
        await self.db["portfolio_revisions"].insert_one(rev.model_dump())
        return doc, rev

    async def get_portfolio(
        self, school_id: str, student_id: str, portfolio_id: str
    ) -> Optional[Dict[str, Any]]:
        query = {
            "portfolio_id": portfolio_id,
            "school_id": school_id,
            "student_id": student_id,
        }
        res = await self.db["portfolio_items"].find_one(query, {"_id": 0})
        return res

    async def list_portfolios(
        self,
        school_id: str,
        student_id: str,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        activity_type: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "newest",
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        flt: Dict[str, Any] = {
            "school_id": school_id,
            "student_id": student_id,
        }
        if status and status != "all":
            flt["status"] = status
        if tag and tag != "all":
            flt["canonical_tag_ids"] = tag
        if activity_type and activity_type != "all":
            flt["activity_type"] = activity_type
        if search and search.strip():
            escaped = re.escape(search.strip())
            flt["$or"] = [
                {"title": {"$regex": escaped, "$options": "i"}},
                {"description": {"$regex": escaped, "$options": "i"}},
            ]

        sort_dir = -1 if sort_by == "newest" else 1
        cursor = (
            self.db["portfolio_items"]
            .find(flt, {"_id": 0})
            .sort("created_at", sort_dir)
            .skip(offset)
            .limit(limit)
        )
        items = await cursor.to_list(length=limit)
        total_count = await self.db["portfolio_items"].count_documents(flt)
        return items, total_count

    async def update_draft(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
        update_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        flt = {
            "portfolio_id": portfolio_id,
            "school_id": school_id,
            "student_id": student_id,
            "status": "draft",
        }
        update_payload = dict(update_data)
        update_payload["updated_at"] = datetime.now(timezone.utc)

        res = await self.db["portfolio_items"].find_one_and_update(
            flt,
            {"$set": update_payload},
            projection={"_id": 0},
            return_document=True,
        )
        return res

    async def atomic_submit(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
        expected_revision: int,
        submission_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        flt = {
            "portfolio_id": portfolio_id,
            "school_id": school_id,
            "student_id": student_id,
            "status": "draft",
            "current_revision_number": expected_revision,
        }

        update_payload = dict(submission_data)
        update_payload.update({
            "status": "submitted",
            "submitted_at": now,
            "updated_at": now,
        })

        # Atomically update item to submitted
        res = await self.db["portfolio_items"].find_one_and_update(
            flt,
            {"$set": update_payload},
            projection={"_id": 0},
            return_document=True,
        )
        if not res:
            return None

        # Lock the corresponding revision snapshot as submitted (immutable)
        rev_id = res.get("current_revision_id")
        await self.db["portfolio_revisions"].update_one(
            {"revision_id": rev_id},
            {
                "$set": {
                    "submitted_at": now,
                    "title_snapshot": res.get("title", ""),
                    "activity_type_snapshot": res.get("activity_type", ""),
                    "description_snapshot": res.get("description", ""),
                    "tag_snapshot": res.get("canonical_tag_ids", []),
                    "evidence_refs": [e.model_dump() if hasattr(e, "model_dump") else e for e in res.get("evidence_refs", [])],
                }
            },
        )
        return res

    async def begin_revision(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Creates revision N+1 when portfolio is in revision_requested state.
        Preserves previous submitted revision completely immutable.
        """
        now = datetime.now(timezone.utc)
        item = await self.db["portfolio_items"].find_one(
            {
                "portfolio_id": portfolio_id,
                "school_id": school_id,
                "student_id": student_id,
                "status": "revision_requested",
            },
            {"_id": 0},
        )
        if not item:
            return None

        new_version = item.get("current_revision_number", 1) + 1
        new_revision_id = str(uuid.uuid4())

        # Create new revision draft record
        new_rev = PortfolioRevisionDocument(
            revision_id=new_revision_id,
            portfolio_id=portfolio_id,
            school_id=school_id,
            student_id=student_id,
            version=new_version,
            title_snapshot=item.get("title", ""),
            activity_type_snapshot=item.get("activity_type", ""),
            description_snapshot=item.get("description", ""),
            tag_snapshot=item.get("canonical_tag_ids", []),
            evidence_refs=item.get("evidence_refs", []),
            created_at=now,
        )
        await self.db["portfolio_revisions"].insert_one(new_rev.model_dump())

        # Update item pointer to new revision, setting status to draft
        res = await self.db["portfolio_items"].find_one_and_update(
            {"portfolio_id": portfolio_id},
            {
                "$set": {
                    "status": "draft",
                    "current_revision_id": new_revision_id,
                    "current_revision_number": new_version,
                    "updated_at": now,
                }
            },
            projection={"_id": 0},
            return_document=True,
        )
        return res

    async def delete_draft(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
    ) -> bool:
        res = await self.db["portfolio_items"].delete_one({
            "portfolio_id": portfolio_id,
            "school_id": school_id,
            "student_id": student_id,
            "status": "draft",
        })
        return res.deleted_count > 0

    async def get_revision(
        self, school_id: str, portfolio_id: str, version: int
    ) -> Optional[Dict[str, Any]]:
        rev = await self.db["portfolio_revisions"].find_one(
            {
                "portfolio_id": portfolio_id,
                "school_id": school_id,
                "version": version,
            },
            {"_id": 0},
        )
        return rev

    async def get_portfolio_by_id(
        self, school_id: str, portfolio_id: str
    ) -> Optional[Dict[str, Any]]:
        query = {
            "portfolio_id": portfolio_id,
            "school_id": school_id,
        }
        return await self.db["portfolio_items"].find_one(query, {"_id": 0})

    async def get_revision_by_id(
        self, revision_id: str
    ) -> Optional[Dict[str, Any]]:
        return await self.db["portfolio_revisions"].find_one(
            {"revision_id": revision_id}, {"_id": 0}
        )

    async def list_teacher_queue(
        self,
        school_id: str,
        eligible_student_ids: List[str],
        tag: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "oldest",
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        if not eligible_student_ids:
            return [], 0

        flt: Dict[str, Any] = {
            "school_id": school_id,
            "student_id": {"$in": eligible_student_ids},
            "status": "submitted",
        }
        if tag and tag != "all":
            flt["canonical_tag_ids"] = tag
        if search and search.strip():
            escaped = re.escape(search.strip())
            flt["$or"] = [
                {"title": {"$regex": escaped, "$options": "i"}},
                {"description": {"$regex": escaped, "$options": "i"}},
            ]

        sort_dir = 1 if sort_by == "oldest" else -1
        cursor = (
            self.db["portfolio_items"]
            .find(flt, {"_id": 0})
            .sort("submitted_at", sort_dir)
            .skip(offset)
            .limit(limit)
        )
        items = await cursor.to_list(length=limit)
        total = await self.db["portfolio_items"].count_documents(flt)
        return items, total

    async def atomic_transition_review(
        self,
        school_id: str,
        portfolio_id: str,
        expected_revision_id: str,
        target_status: str,
        feedback: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        flt = {
            "portfolio_id": portfolio_id,
            "school_id": school_id,
            "status": "submitted",
            "current_revision_id": expected_revision_id,
        }
        update_doc: Dict[str, Any] = {
            "$set": {
                "status": target_status,
                "teacher_feedback": feedback,
                "updated_at": now,
            }
        }
        res = await self.db["portfolio_items"].find_one_and_update(
            flt,
            update_doc,
            projection={"_id": 0},
            return_document=True,
        )
        return res

    async def save_evidence_tag_snapshot(
        self, snapshot: EvidenceTagSnapshotDocument
    ) -> EvidenceTagSnapshotDocument:
        existing = await self.db["evidence_tag_snapshots"].find_one(
            {"validation_decision_id": snapshot.validation_decision_id},
            {"_id": 0},
        )
        if existing:
            return EvidenceTagSnapshotDocument(**existing)
        await self.db["evidence_tag_snapshots"].insert_one(snapshot.model_dump())
        return snapshot

    async def get_evidence_tag_snapshots_for_student(
        self, school_id: str, student_id: str
    ) -> List[Dict[str, Any]]:
        cursor = self.db["evidence_tag_snapshots"].find(
            {"school_id": school_id, "student_id": student_id},
            {"_id": 0},
        ).sort("approved_at", -1)
        return await cursor.to_list(length=1000)

    async def get_evidence_tag_snapshots_for_cohort(
        self, school_id: str, student_ids: List[str]
    ) -> List[Dict[str, Any]]:
        cursor = self.db["evidence_tag_snapshots"].find(
            {"school_id": school_id, "student_id": {"$in": student_ids}},
            {"_id": 0},
        ).sort("approved_at", -1)
        return await cursor.to_list(length=10000)

    async def delete_evidence_tag_snapshots_for_student(
        self, school_id: str, student_id: str
    ) -> int:
        res = await self.db["evidence_tag_snapshots"].delete_many(
            {"school_id": school_id, "student_id": student_id}
        )
        return res.deleted_count

    async def get_snapshot_by_decision_id(
        self, decision_id: str
    ) -> Optional[Dict[str, Any]]:
        return await self.db["evidence_tag_snapshots"].find_one(
            {"validation_decision_id": decision_id},
            {"_id": 0},
        )

    async def save_recommendation_snapshot(
        self, snapshot: RecommendationSnapshotDocument
    ) -> RecommendationSnapshotDocument:
        await self.db["recommendation_snapshots"].insert_one(snapshot.model_dump())
        return snapshot

    async def get_latest_recommendation_snapshot(
        self, school_id: str, student_id: str
    ) -> Optional[Dict[str, Any]]:
        return await self.db["recommendation_snapshots"].find_one(
            {"school_id": school_id, "student_id": student_id},
            {"_id": 0},
            sort=[("generated_at", -1)],
        )

    async def save_professional_description(
        self, doc: DerivedProfessionalDescriptionDocument
    ) -> DerivedProfessionalDescriptionDocument:
        # Upsert by (school_id, student_id, portfolio_id)
        await self.db["derived_professional_descriptions"].update_one(
            {
                "school_id": doc.school_id,
                "student_id": doc.student_id,
                "portfolio_id": doc.portfolio_id,
            },
            {"$set": doc.model_dump()},
            upsert=True,
        )
        return doc

    async def get_professional_description(
        self, school_id: str, student_id: str, portfolio_id: str
    ) -> Optional[Dict[str, Any]]:
        return await self.db["derived_professional_descriptions"].find_one(
            {
                "school_id": school_id,
                "student_id": student_id,
                "portfolio_id": portfolio_id,
            },
            {"_id": 0},
        )

    async def save_cv_snapshot(
        self, snapshot: CVContentSnapshotDocument
    ) -> CVContentSnapshotDocument:
        await self.db["cv_content_snapshots"].insert_one(snapshot.model_dump())
        return snapshot

    async def get_cv_snapshot(
        self, school_id: str, student_id: str, snapshot_id: str
    ) -> Optional[Dict[str, Any]]:
        return await self.db["cv_content_snapshots"].find_one(
            {
                "school_id": school_id,
                "student_id": student_id,
                "snapshot_id": snapshot_id,
            },
            {"_id": 0},
        )

    async def get_cv_snapshot_by_id(
        self, snapshot_id: str
    ) -> Optional[Dict[str, Any]]:
        return await self.db["cv_content_snapshots"].find_one(
            {"snapshot_id": snapshot_id},
            {"_id": 0},
        )

    async def list_cv_snapshots_for_student(
        self, school_id: str, student_id: str
    ) -> List[Dict[str, Any]]:
        cursor = self.db["cv_content_snapshots"].find(
            {"school_id": school_id, "student_id": student_id},
            {"_id": 0},
        ).sort("generated_at", -1)
        return await cursor.to_list(length=100)

    async def update_cv_snapshot_status(
        self, snapshot_id: str, status: str
    ) -> bool:
        res = await self.db["cv_content_snapshots"].update_one(
            {"snapshot_id": snapshot_id},
            {"$set": {"status": status}},
        )
        return res.modified_count > 0

    async def get_cv_snapshot_by_digest(
        self, school_id: str, student_id: str, content_digest: str
    ) -> Optional[Dict[str, Any]]:
        return await self.db["cv_content_snapshots"].find_one(
            {
                "school_id": school_id,
                "student_id": student_id,
                "content_digest": content_digest,
            },
            {"_id": 0},
            sort=[("generated_at", -1)],
        )




class InMemoryPortfolioRepository(PortfolioRepository):
    """
    In-memory portfolio repository for testing and environments where MongoDB daemon is not running.
    Maintains identical behavioral contracts, tenant bounds, and revision immutability.
    """

    def __init__(self):
        now = datetime(2026, 9, 25, 10, 0, tzinfo=timezone.utc)
        self.items: Dict[str, Dict[str, Any]] = {
            "prt_001": {
                "portfolio_id": "prt_001",
                "school_id": "sch_smk1_cimahi",
                "student_id": "usr_std_001",
                "title": "Aplikasi Web E-Commerce Koperasi Sekolah",
                "activity_type": "project",
                "activity_date": "2026-08-15",
                "description": "Mengembangkan aplikasi toko digital untuk koperasi siswa dengan integrasi katalog produk.",
                "canonical_tag_ids": ["web-development", "digital-literacy"],
                "evidence_refs": [{"id": "ev_001", "type": "link", "url": "https://github.com/alya/koperasi-web", "title": "Repository GitHub"}],
                "status": "approved",
                "current_revision_id": "rev_001",
                "current_revision_number": 1,
                "created_at": now,
                "updated_at": now,
                "submitted_at": now,
            },
            "prt_002": {
                "portfolio_id": "prt_002",
                "school_id": "sch_smk1_cimahi",
                "student_id": "usr_std_001",
                "title": "Sistem Manajemen Perpustakaan Digital",
                "activity_type": "project",
                "activity_date": "2026-09-10",
                "description": "Platform peminjaman buku berbasis QR code dan dashboard statistik peminjaman.",
                "canonical_tag_ids": ["web-development", "problem-solving"],
                "evidence_refs": [{"id": "ev_002", "type": "link", "url": "https://github.com/alya/perpus-digital", "title": "Repository GitHub"}],
                "status": "submitted",
                "current_revision_id": "rev_002",
                "current_revision_number": 1,
                "created_at": now,
                "updated_at": now,
                "submitted_at": now,
            },
            "prt_003": {
                "portfolio_id": "prt_003",
                "school_id": "sch_smk1_cimahi",
                "student_id": "usr_std_001",
                "title": "Redesain UI Portal Siswa SMK",
                "activity_type": "assignment",
                "activity_date": "2026-09-20",
                "description": "Desain antarmuka modern mobile-first dengan Figma dan prototipe interaktif.",
                "canonical_tag_ids": ["ui-ux", "creativity"],
                "evidence_refs": [{"id": "ev_003", "type": "link", "url": "https://figma.com/design/portal-siswa", "title": "Figma Prototype"}],
                "status": "draft",
                "current_revision_id": "rev_003",
                "current_revision_number": 1,
                "created_at": now,
                "updated_at": now,
            },
        }
        self.revisions: Dict[str, Dict[str, Any]] = {
            "rev_001": {
                "revision_id": "rev_001",
                "portfolio_id": "prt_001",
                "school_id": "sch_smk1_cimahi",
                "student_id": "usr_std_001",
                "version": 1,
                "title_snapshot": "Aplikasi Web E-Commerce Koperasi Sekolah",
                "activity_type_snapshot": "project",
                "description_snapshot": "Mengembangkan aplikasi toko digital untuk koperasi siswa dengan integrasi katalog produk.",
                "tag_snapshot": ["web-development", "digital-literacy"],
                "evidence_refs": [{"id": "ev_001", "type": "link", "url": "https://github.com/alya/koperasi-web", "title": "Repository GitHub"}],
                "created_at": now,
            },
            "rev_002": {
                "revision_id": "rev_002",
                "portfolio_id": "prt_002",
                "school_id": "sch_smk1_cimahi",
                "student_id": "usr_std_001",
                "version": 1,
                "title_snapshot": "Sistem Manajemen Perpustakaan Digital",
                "activity_type_snapshot": "project",
                "description_snapshot": "Platform peminjaman buku berbasis QR code dan dashboard statistik peminjaman.",
                "tag_snapshot": ["web-development", "problem-solving"],
                "evidence_refs": [{"id": "ev_002", "type": "link", "url": "https://github.com/alya/perpus-digital", "title": "Repository GitHub"}],
                "created_at": now,
            },
            "rev_003": {
                "revision_id": "rev_003",
                "portfolio_id": "prt_003",
                "school_id": "sch_smk1_cimahi",
                "student_id": "usr_std_001",
                "version": 1,
                "title_snapshot": "Redesain UI Portal Siswa SMK",
                "activity_type_snapshot": "assignment",
                "description_snapshot": "Desain antarmuka modern mobile-first dengan Figma dan prototipe interaktif.",
                "tag_snapshot": ["ui-ux", "creativity"],
                "evidence_refs": [{"id": "ev_003", "type": "link", "url": "https://figma.com/design/portal-siswa", "title": "Figma Prototype"}],
                "created_at": now,
            },
        }
        self.snapshots: Dict[str, Dict[str, Any]] = {
            "snap_ev_001": {
                "snapshot_id": "snap_ev_001",
                "school_id": "sch_smk1_cimahi",
                "student_id": "usr_std_001",
                "portfolio_id": "prt_001",
                "revision_id": "rev_001",
                "validation_decision_id": "dec_001",
                "canonical_tag_ids": ["web-development", "digital-literacy"],
                "canonical_tag_codes": ["web-development", "digital-literacy"],
                "approved_at": now,
                "projection_version": "v1",
            }
        }
        self.recommendation_snapshots: Dict[str, Dict[str, Any]] = {}
        self.professional_descriptions: Dict[str, Dict[str, Any]] = {}
        self.cv_snapshots: Dict[str, Dict[str, Any]] = {
            "snap_demo_001": {
                "snapshot_id": "snap_demo_001",
                "school_id": "sch_smk1_cimahi",
                "student_id": "usr_std_001",
                "profile": {
                    "display_name": "Alya Rahma",
                    "school_name": "SMK Negeri 1 Cimahi",
                    "class_name": "XII RPL 1",
                    "professional_summary": "Siswa Rekayasa Perangkat Lunak dengan keahlian pengembangan aplikasi web responsif dan integrasi sistem.",
                },
                "approved_skills": [
                    {"name": "Web Development", "score": 92, "level": "Tingkat Mahir"},
                    {"name": "Database Management", "score": 85, "level": "Tingkat Mahir"},
                    {"name": "UI/UX Design", "score": 78, "level": "Tingkat Menengah"},
                ],
                "selected_portfolios": [
                    {
                        "portfolio_id": "prt_001",
                        "title": "Aplikasi Web E-Commerce Koperasi Sekolah",
                        "activity_type": "project",
                        "activity_date": "2026-08-15",
                        "professional_description": "Mengembangkan aplikasi toko digital untuk koperasi siswa dengan integrasi katalog produk.",
                        "tags": ["Web Development", "Database Management"],
                    }
                ],
                "content_digest": "TLN-A1B2-C3D4",
                "status": "issued",
                "generated_at": datetime(2026, 9, 25, 10, 0, tzinfo=timezone.utc),
            }
        }


    async def create_portfolio(
        self,
        school_id: str,
        student_id: str,
        title: str,
        activity_type: str,
        activity_date: str,
        description: str,
        canonical_tag_ids: List[str],
        evidence_refs: List[EvidenceRef],
    ) -> Tuple[PortfolioItemDocument, PortfolioRevisionDocument]:
        portfolio_id = str(uuid.uuid4())
        revision_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        doc = PortfolioItemDocument(
            portfolio_id=portfolio_id,
            school_id=school_id,
            student_id=student_id,
            title=title,
            activity_type=activity_type,
            activity_date=activity_date,
            description=description,
            canonical_tag_ids=canonical_tag_ids,
            evidence_refs=evidence_refs,
            status="draft",
            current_revision_id=revision_id,
            current_revision_number=1,
            created_at=now,
            updated_at=now,
        )

        rev = PortfolioRevisionDocument(
            revision_id=revision_id,
            portfolio_id=portfolio_id,
            school_id=school_id,
            student_id=student_id,
            version=1,
            title_snapshot=title,
            activity_type_snapshot=activity_type,
            description_snapshot=description,
            tag_snapshot=canonical_tag_ids,
            evidence_refs=evidence_refs,
            created_at=now,
        )

        self.items[portfolio_id] = doc.model_dump()
        self.revisions[revision_id] = rev.model_dump()
        return doc, rev

    async def get_portfolio(
        self, school_id: str, student_id: str, portfolio_id: str
    ) -> Optional[Dict[str, Any]]:
        item = self.items.get(portfolio_id)
        if item and item.get("school_id") == school_id and item.get("student_id") == student_id:
            return dict(item)
        return None

    async def list_portfolios(
        self,
        school_id: str,
        student_id: str,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        activity_type: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "newest",
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        matches = []
        for item in self.items.values():
            if item.get("school_id") != school_id or item.get("student_id") != student_id:
                continue
            if status and status != "all" and item.get("status") != status:
                continue
            if tag and tag != "all" and tag not in item.get("canonical_tag_ids", []):
                continue
            if activity_type and activity_type != "all" and item.get("activity_type") != activity_type:
                continue
            if search and search.strip():
                query = search.strip().lower()
                if (
                    query not in item.get("title", "").lower()
                    and query not in item.get("description", "").lower()
                ):
                    continue
            matches.append(dict(item))

        # Sort
        matches.sort(
            key=lambda x: x.get("created_at"),
            reverse=(sort_by == "newest"),
        )
        total = len(matches)
        sliced = matches[offset : offset + limit]
        return sliced, total

    async def update_draft(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
        update_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        item = self.items.get(portfolio_id)
        if not item:
            return None
        if item.get("school_id") != school_id or item.get("student_id") != student_id:
            return None
        if item.get("status") != "draft":
            return None

        item.update(update_data)
        item["updated_at"] = datetime.now(timezone.utc)
        return dict(item)

    async def atomic_submit(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
        expected_revision: int,
        submission_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        item = self.items.get(portfolio_id)
        if not item:
            return None
        if item.get("school_id") != school_id or item.get("student_id") != student_id:
            return None
        if item.get("status") != "draft":
            return None
        if item.get("current_revision_number") != expected_revision:
            return None

        now = datetime.now(timezone.utc)
        item.update(submission_data)
        item["status"] = "submitted"
        item["submitted_at"] = now
        item["updated_at"] = now

        # Update revision snapshot
        rev_id = item.get("current_revision_id")
        rev = self.revisions.get(rev_id)
        if rev:
            rev["submitted_at"] = now
            rev["title_snapshot"] = item.get("title", "")
            rev["activity_type_snapshot"] = item.get("activity_type", "")
            rev["description_snapshot"] = item.get("description", "")
            rev["tag_snapshot"] = list(item.get("canonical_tag_ids", []))
            rev["evidence_refs"] = list(item.get("evidence_refs", []))

        return dict(item)

    async def begin_revision(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
    ) -> Optional[Dict[str, Any]]:
        item = self.items.get(portfolio_id)
        if not item:
            return None
        if item.get("school_id") != school_id or item.get("student_id") != student_id:
            return None
        if item.get("status") != "revision_requested":
            return None

        now = datetime.now(timezone.utc)
        new_version = item.get("current_revision_number", 1) + 1
        new_rev_id = str(uuid.uuid4())

        new_rev = PortfolioRevisionDocument(
            revision_id=new_rev_id,
            portfolio_id=portfolio_id,
            school_id=school_id,
            student_id=student_id,
            version=new_version,
            title_snapshot=item.get("title", ""),
            activity_type_snapshot=item.get("activity_type", ""),
            description_snapshot=item.get("description", ""),
            tag_snapshot=item.get("canonical_tag_ids", []),
            evidence_refs=item.get("evidence_refs", []),
            created_at=now,
        )
        self.revisions[new_rev_id] = new_rev.model_dump()

        item["status"] = "draft"
        item["current_revision_id"] = new_rev_id
        item["current_revision_number"] = new_version
        item["updated_at"] = now
        return dict(item)

    async def delete_draft(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
    ) -> bool:
        item = self.items.get(portfolio_id)
        if not item:
            return False
        if item.get("school_id") != school_id or item.get("student_id") != student_id:
            return False
        if item.get("status") != "draft":
            return False

        del self.items[portfolio_id]
        return True

    async def get_revision(self, school_id: str, portfolio_id: str, version: int) -> Optional[Dict[str, Any]]:
        for rev in self.revisions.values():
            if rev.get("portfolio_id") == portfolio_id and rev.get("version") == version:
                return dict(rev)
        return None

    async def set_status_for_testing(self, school_id: str, portfolio_id: str, status: str) -> None:
        item = self.items.get(portfolio_id)
        if item:
            item["status"] = status

    async def get_portfolio_by_id(
        self, school_id: str, portfolio_id: str
    ) -> Optional[Dict[str, Any]]:
        item = self.items.get(portfolio_id)
        if item and item.get("school_id") == school_id:
            return dict(item)
        return None

    async def get_revision_by_id(
        self, revision_id: str
    ) -> Optional[Dict[str, Any]]:
        rev = self.revisions.get(revision_id)
        if rev:
            return dict(rev)
        return None

    async def list_teacher_queue(
        self,
        school_id: str,
        eligible_student_ids: List[str],
        tag: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "oldest",
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        if not eligible_student_ids:
            return [], 0

        eligible_set = set(eligible_student_ids)
        matches = []
        for item in self.items.values():
            if item.get("school_id") != school_id:
                continue
            if item.get("student_id") not in eligible_set:
                continue
            if item.get("status") != "submitted":
                continue
            if tag and tag != "all" and tag not in item.get("canonical_tag_ids", []):
                continue
            if search and search.strip():
                query = search.strip().lower()
                if (
                    query not in item.get("title", "").lower()
                    and query not in item.get("description", "").lower()
                ):
                    continue
            matches.append(dict(item))

        def get_sort_key(x):
            sub = x.get("submitted_at")
            if sub is None:
                return datetime.min.replace(tzinfo=timezone.utc)
            return sub

        matches.sort(
            key=get_sort_key,
            reverse=(sort_by != "oldest"),
        )
        total = len(matches)
        sliced = matches[offset : offset + limit]
        return sliced, total

    async def atomic_transition_review(
        self,
        school_id: str,
        portfolio_id: str,
        expected_revision_id: str,
        target_status: str,
        feedback: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        item = self.items.get(portfolio_id)
        if not item:
            return None
        if item.get("school_id") != school_id:
            return None
        if item.get("status") != "submitted":
            return None
        if item.get("current_revision_id") != expected_revision_id:
            return None

        now = datetime.now(timezone.utc)
        item["status"] = target_status
        item["teacher_feedback"] = feedback
        item["updated_at"] = now
        return dict(item)

    async def save_evidence_tag_snapshot(
        self, snapshot: EvidenceTagSnapshotDocument
    ) -> EvidenceTagSnapshotDocument:
        # Check idempotency by validation_decision_id
        for existing in self.snapshots.values():
            if existing.get("validation_decision_id") == snapshot.validation_decision_id:
                return EvidenceTagSnapshotDocument(**existing)
        data = snapshot.model_dump()
        self.snapshots[snapshot.snapshot_id] = data
        return snapshot

    async def get_evidence_tag_snapshots_for_student(
        self, school_id: str, student_id: str
    ) -> List[Dict[str, Any]]:
        matches = [
            dict(s)
            for s in self.snapshots.values()
            if s.get("school_id") == school_id and s.get("student_id") == student_id
        ]
        matches.sort(
            key=lambda x: x.get("approved_at") or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return matches

    async def get_evidence_tag_snapshots_for_cohort(
        self, school_id: str, student_ids: List[str]
    ) -> List[Dict[str, Any]]:
        id_set = set(student_ids)
        matches = [
            dict(s)
            for s in self.snapshots.values()
            if s.get("school_id") == school_id and s.get("student_id") in id_set
        ]
        matches.sort(
            key=lambda x: x.get("approved_at") or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return matches

    async def delete_evidence_tag_snapshots_for_student(
        self, school_id: str, student_id: str
    ) -> int:
        to_del = [
            sid
            for sid, s in self.snapshots.items()
            if s.get("school_id") == school_id and s.get("student_id") == student_id
        ]
        for sid in to_del:
            del self.snapshots[sid]
        return len(to_del)

    async def get_snapshot_by_decision_id(
        self, decision_id: str
    ) -> Optional[Dict[str, Any]]:
        for s in self.snapshots.values():
            if s.get("validation_decision_id") == decision_id:
                return dict(s)
        return None

    async def save_recommendation_snapshot(
        self, snapshot: RecommendationSnapshotDocument
    ) -> RecommendationSnapshotDocument:
        self.recommendation_snapshots[snapshot.snapshot_id] = snapshot.model_dump()
        return snapshot

    async def get_latest_recommendation_snapshot(
        self, school_id: str, student_id: str
    ) -> Optional[Dict[str, Any]]:
        matches = [
            dict(s)
            for s in self.recommendation_snapshots.values()
            if s.get("school_id") == school_id and s.get("student_id") == student_id
        ]
        if not matches:
            return None
        matches.sort(
            key=lambda x: x.get("generated_at") or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return matches[0]

    async def save_professional_description(
        self, doc: DerivedProfessionalDescriptionDocument
    ) -> DerivedProfessionalDescriptionDocument:
        key = f"{doc.school_id}_{doc.student_id}_{doc.portfolio_id}"
        self.professional_descriptions[key] = doc.model_dump()
        return doc

    async def get_professional_description(
        self, school_id: str, student_id: str, portfolio_id: str
    ) -> Optional[Dict[str, Any]]:
        key = f"{school_id}_{student_id}_{portfolio_id}"
        val = self.professional_descriptions.get(key)
        return dict(val) if val else None

    async def save_portfolio(self, item: Dict[str, Any]) -> None:
        self.items[item["portfolio_id"]] = dict(item)

    async def save_approved_snapshot(self, snapshot: Dict[str, Any]) -> None:
        sid = snapshot.get("snapshot_id") or str(uuid.uuid4())
        self.snapshots[sid] = dict(snapshot)

    async def save_cv_snapshot(
        self, snapshot: CVContentSnapshotDocument
    ) -> CVContentSnapshotDocument:
        self.cv_snapshots[snapshot.snapshot_id] = snapshot.model_dump()
        return snapshot

    async def get_cv_snapshot(
        self, school_id: str, student_id: str, snapshot_id: str
    ) -> Optional[Dict[str, Any]]:
        val = self.cv_snapshots.get(snapshot_id)
        if val and val.get("school_id") == school_id and val.get("student_id") == student_id:
            return dict(val)
        return None

    async def get_cv_snapshot_by_id(
        self, snapshot_id: str
    ) -> Optional[Dict[str, Any]]:
        val = self.cv_snapshots.get(snapshot_id)
        return dict(val) if val else None

    async def list_cv_snapshots_for_student(
        self, school_id: str, student_id: str
    ) -> List[Dict[str, Any]]:
        matches = [
            dict(s)
            for s in self.cv_snapshots.values()
            if s.get("school_id") == school_id and s.get("student_id") == student_id
        ]
        matches.sort(
            key=lambda x: x.get("generated_at") or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return matches

    async def update_cv_snapshot_status(
        self, snapshot_id: str, status: str
    ) -> bool:
        if snapshot_id in self.cv_snapshots:
            self.cv_snapshots[snapshot_id]["status"] = status
            return True
        return False

    async def get_cv_snapshot_by_digest(
        self, school_id: str, student_id: str, content_digest: str
    ) -> Optional[Dict[str, Any]]:
        matches = [
            dict(s)
            for s in self.cv_snapshots.values()
            if s.get("school_id") == school_id
            and s.get("student_id") == student_id
            and s.get("content_digest") == content_digest
        ]
        if not matches:
            return None
        matches.sort(
            key=lambda x: x.get("generated_at") or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return matches[0]


_in_memory_portfolio_repo_instance: Optional[InMemoryPortfolioRepository] = None


def get_portfolio_repository() -> PortfolioRepository:
    """
    Factory resolving the authoritative portfolio repository.
    Returns InMemoryPortfolioRepository in test / in_memory mode.
    Returns PostgresPortfolioRepository for production / PostgreSQL (Neon).
    """
    global _in_memory_portfolio_repo_instance
    if settings.app_env == "test" or settings.repository_backend == "in_memory":
        if _in_memory_portfolio_repo_instance is None:
            _in_memory_portfolio_repo_instance = InMemoryPortfolioRepository()
        return _in_memory_portfolio_repo_instance
    return PostgresPortfolioRepository()


