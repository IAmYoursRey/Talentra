import uuid
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from abc import ABC, abstractmethod

from ..core.mongodb import mongo_manager
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
        self.items: Dict[str, Dict[str, Any]] = {}
        self.revisions: Dict[str, Dict[str, Any]] = {}
        self.snapshots: Dict[str, Dict[str, Any]] = {}
        self.recommendation_snapshots: Dict[str, Dict[str, Any]] = {}
        self.professional_descriptions: Dict[str, Dict[str, Any]] = {}
        self.cv_snapshots: Dict[str, Dict[str, Any]] = {}


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

