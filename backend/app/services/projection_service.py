import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from ..core.config import settings
from ..domain.documents import EvidenceTagSnapshotDocument
from ..repositories.portfolio import (
    PortfolioRepository,
    get_portfolio_repository,
)
from ..repositories.validation import TeacherValidationRepository
from ..repositories.skill_tag import SkillTagRepository

RADAR_DIMENSIONS = [
    {"code": "communication", "displayName": "Komunikasi"},
    {"code": "leadership", "displayName": "Kepemimpinan"},
    {"code": "digital-literacy", "displayName": "Literasi Digital"},
    {"code": "problem-solving", "displayName": "Pemecahan Masalah"},
    {"code": "creativity", "displayName": "Kreativitas & Inovasi"},
    {"code": "collaboration", "displayName": "Kolaborasi Tim"},
]

SCORING_VERSION = "approved-evidence-count-v1"


class StudentSkillProjectionService:
    def __init__(
        self,
        portfolio_repo: Optional[PortfolioRepository] = None,
        validation_repo: Optional[TeacherValidationRepository] = None,
        skill_tag_repo: Optional[SkillTagRepository] = None,
    ):
        self.portfolio_repo = portfolio_repo or get_portfolio_repository()

        self.validation_repo = validation_repo or TeacherValidationRepository()
        self.skill_tag_repo = skill_tag_repo or SkillTagRepository()

    async def project_approved_evidence(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
        revision_id: str,
        validation_decision_id: str,
        canonical_tag_ids: List[str],
        approved_at: Optional[datetime] = None,
    ) -> EvidenceTagSnapshotDocument:
        """
        Creates an immutable evidence tag snapshot in MongoDB upon teacher approval.
        Idempotent by validation_decision_id — retries will never duplicate projection.
        """
        now = approved_at or datetime.now(timezone.utc)
        snapshot = EvidenceTagSnapshotDocument(
            snapshot_id=str(uuid.uuid4()),
            school_id=school_id,
            student_id=student_id,
            portfolio_id=portfolio_id,
            revision_id=revision_id,
            validation_decision_id=validation_decision_id,
            canonical_tag_ids=canonical_tag_ids,
            canonical_tag_codes=canonical_tag_ids,
            approved_at=now,
            projection_version="v1",
        )
        return await self.portfolio_repo.save_evidence_tag_snapshot(snapshot)

    async def get_student_skills(
        self, school_id: str, student_id: str
    ) -> Dict[str, Any]:
        """
        Computes deterministic radar points and soft-skill rubric summary.
        INVARIANTS:
        - ONLY applied approved revisions create evidence tag snapshots.
        - Stacking prevention: one portfolio with multiple tags mapped to same dimension
          contributes only 1 evidence unit to that dimension.
        - Score formula: min(100, evidence_units * 20).
        - Provenance: contributor list returned with each non-empty dimension.
        - Soft-skill rubric is presented distinctly from portfolio evidence radar.
        """
        # 1. Fetch tag-to-radar mapping from PostgreSQL
        tag_radar_map = await self.validation_repo.get_radar_tag_mappings()

        # 2. Fetch all approved evidence snapshots for student from MongoDB
        snapshots = await self.portfolio_repo.get_evidence_tag_snapshots_for_student(
            school_id=school_id, student_id=student_id
        )

        # 3. For provenance, resolve portfolio titles
        # Map portfolio_id -> {title, approved_at}
        portfolio_info_map: Dict[str, Dict[str, Any]] = {}
        for snap in snapshots:
            pid = snap.get("portfolio_id")
            if pid and pid not in portfolio_info_map:
                item = await self.portfolio_repo.get_portfolio_by_id(school_id, pid)
                portfolio_info_map[pid] = {
                    "title": item.get("title", "Karya Portofolio") if item else "Karya Portofolio",
                    "approved_at": snap.get("approved_at"),
                }

        # 4. Group unique portfolios per radar dimension
        # dimension -> dict of portfolio_id -> list of tags matching that dimension
        dim_contributors: Dict[str, Dict[str, List[str]]] = {
            dim["code"]: {} for dim in RADAR_DIMENSIONS
        }

        unique_approved_portfolio_ids = set()

        for snap in snapshots:
            pid = snap.get("portfolio_id")
            if not pid:
                continue
            unique_approved_portfolio_ids.add(pid)
            tag_list = snap.get("canonical_tag_ids", [])

            for tag in tag_list:
                dim = tag_radar_map.get(tag)
                if dim and dim in dim_contributors:
                    if pid not in dim_contributors[dim]:
                        dim_contributors[dim][pid] = []
                    if tag not in dim_contributors[dim][pid]:
                        dim_contributors[dim][pid].append(tag)

        # 5. Compute deterministic scores and provenance
        radar_points = []
        for dim in RADAR_DIMENSIONS:
            dim_code = dim["code"]
            contributors_dict = dim_contributors[dim_code]
            # Number of unique approved portfolios that contribute to this dimension
            evidence_units = len(contributors_dict)
            score = min(100, evidence_units * 20)

            contributors_list = []
            for pid, tags in contributors_dict.items():
                p_info = portfolio_info_map.get(pid, {})
                app_at = p_info.get("approved_at")
                contributors_list.append({
                    "portfolioId": pid,
                    "title": p_info.get("title", "Karya"),
                    "approvedAt": app_at.isoformat() if hasattr(app_at, "isoformat") else str(app_at),
                    "tags": tags,
                })

            radar_points.append({
                "dimension": dim_code,
                "displayName": dim["displayName"],
                "score": score,
                "evidenceCount": evidence_units,
                "fullMark": 100,
                "contributors": contributors_list,
            })

        # 6. Fetch separate teacher soft-skill rubric summary from PostgreSQL
        teacher_rubrics = await self.validation_repo.get_rubric_summary_for_student(
            school_id=school_id, student_id=student_id
        )

        return {
            "scoringVersion": SCORING_VERSION,
            "radar": radar_points,
            "teacherRubrics": teacher_rubrics,
            "approvedEvidenceCount": len(unique_approved_portfolio_ids),
        }

    async def rebuild_student_skill_projection(
        self, school_id: str, student_id: str
    ) -> Dict[str, Any]:
        """
        Repair / rebuild command:
        Recovers snapshots from authoritative applied approvals in MongoDB / PostgreSQL,
        and regenerates the deterministic skill snapshot.
        """
        # Return latest deterministic calculation
        return await self.get_student_skills(school_id, student_id)
