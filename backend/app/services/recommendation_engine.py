import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from ..core.audit import audit_logger
from ..core.config import settings
from ..domain.enums import AuditEventType
from ..domain.documents import RecommendationSnapshotDocument
from ..domain.models import CareerPath, StudyPath
from ..repositories.catalog import CareerCatalogRepository
from ..repositories.portfolio import PortfolioRepository, MongoPortfolioRepository, InMemoryPortfolioRepository
from .projection_service import StudentSkillProjectionService

SCORING_VERSION = "recommendation-v1"
CATALOG_VERSION = "career-catalog-v1"
MAPPING_VERSION = "mapping-v1"


class RecommendationEngineService:
    """
    Deterministic, evidence-based career & study exploration engine.
    INVARIANTS:
    - Advisory only ("bidang yang dapat dieksplorasi"). No admission/employability prediction.
    - Zero protected or sensitive demographic traits.
    - Consumes ONLY teacher-approved evidence snapshots and official rubric observations.
    - Proof-of-work primary (60% radar + 20% tags), rubric secondary (20%).
    - Missing rubric policy: re-normalizes available components (75% radar, 25% tags).
    - Missing evidence is NOT negative ability ("belum cukup bukti tervalidasi").
    - Longitudinal consistency & repetition caps prevent gaming.
    - Confidence is distinct from match score (measures evidence volume & breadth, not probability).
    - Deterministic tie-breaking: matchScore desc, confidence desc, code asc.
    - Immutable snapshots in MongoDB with staleness fingerprinting.
    """

    def __init__(
        self,
        portfolio_repo: Optional[PortfolioRepository] = None,
        catalog_repo: Optional[CareerCatalogRepository] = None,
        projection_service: Optional[StudentSkillProjectionService] = None,
    ):
        if portfolio_repo:
            self.portfolio_repo = portfolio_repo
        else:
            if settings.app_env == "test":
                self.portfolio_repo = InMemoryPortfolioRepository()
            else:
                self.portfolio_repo = MongoPortfolioRepository()

        self.catalog_repo = catalog_repo or CareerCatalogRepository()
        self.projection_service = projection_service or StudentSkillProjectionService(portfolio_repo=self.portfolio_repo)

    def _compute_source_fingerprint(
        self,
        snapshots: List[Dict[str, Any]],
        rubrics: Dict[str, Any],
        catalog_version: str,
    ) -> str:
        """
        Creates a deterministic hash representing the exact approved evidence and rubric state.
        If this hash matches the latest snapshot, the snapshot is fresh.
        """
        snapshot_ids = sorted([str(s.get("snapshot_id") or s.get("validation_decision_id")) for s in snapshots])
        rubric_tokens = sorted([f"{k}:{v.get('score', 0)}" for k, v in rubrics.items()]) if isinstance(rubrics, dict) else []
        raw = f"{catalog_version}|{','.join(snapshot_ids)}|{','.join(rubric_tokens)}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _calculate_evidence_confidence(
        self,
        approved_snapshots: List[Dict[str, Any]],
        radar_points: List[Dict[str, Any]],
        rubrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculates deterministic evidence sufficiency (quantity, breadth, longitudinal consistency).
        Independent of match score.
        Levels:
          0-24: limited (Bukti Terbatas)
          25-49: developing (Bukti Berkembang)
          50-74: moderate (Bukti Cukup)
          75-100: strong (Bukti Kuat)
        """
        approved_count = len(approved_snapshots)
        if approved_count == 0:
            return {
                "score": 0,
                "level": "limited",
                "label": "Bukti Terbatas",
                "approvedPortfolioCount": 0,
                "distinctDimensionCount": 0,
                "timeSpanMonths": 0,
                "distinctPeriodBuckets": 0,
                "activePeriodCount": 0,
                "rubricAssessmentCount": 0,
            }

        # 1. Distinct skill dimensions with >0 score
        distinct_dims = sum(1 for p in radar_points if p.get("score", 0) > 0)

        # 2. Longitudinal period bucketing & time span
        dates = []
        period_buckets = set()
        for snap in approved_snapshots:
            dt = snap.get("approved_at")
            if dt:
                if isinstance(dt, str):
                    try:
                        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                    except Exception:
                        dt = None
                if dt:
                    dates.append(dt)
                    # Bucket by half-year period: YYYY-H1 or YYYY-H2
                    half = "H1" if dt.month <= 6 else "H2"
                    period_buckets.add(f"{dt.year}-{half}")

        time_span_months = 0
        if dates:
            min_d, max_d = min(dates), max(dates)
            time_span_months = max(1, (max_d.year - min_d.year) * 12 + (max_d.month - min_d.month) + 1)

        rubric_count = len(rubrics) if isinstance(rubrics, dict) else 0

        # Weights: count (max 30), diversity (max 25), longitudinal (max 25), rubrics (max 20)
        c_count = min(30, approved_count * 6)
        c_div = min(25, distinct_dims * 5)
        c_long = min(25, len(period_buckets) * 12.5)
        c_rub = min(20, rubric_count * 4)

        total_confidence = int(min(100, round(c_count + c_div + c_long + c_rub)))

        # Prompt 35 policy:
        # 1 approved portfolio: show early signals only, confidence = limited (< 25)
        # 2-3 approved portfolios: developing (< 50)
        # Larger longitudinal set: may reach moderate/strong
        if approved_count == 1:
            total_confidence = min(24, total_confidence)
        elif approved_count <= 3:
            total_confidence = min(49, total_confidence)

        if total_confidence < 25:
            level = "limited"
            label = "Bukti Terbatas"
        elif total_confidence < 50:
            level = "developing"
            label = "Bukti Berkembang"
        elif total_confidence < 75:
            level = "moderate"
            label = "Bukti Cukup"
        else:
            level = "strong"
            label = "Bukti Kuat"

        return {
            "score": total_confidence,
            "level": level,
            "label": label,
            "approvedPortfolioCount": approved_count,
            "distinctDimensionCount": distinct_dims,
            "timeSpanMonths": time_span_months,
            "distinctPeriodBuckets": len(period_buckets),
            "activePeriodCount": len(period_buckets),
            "rubricAssessmentCount": rubric_count,
        }

    def _match_path(
        self,
        path: Any,
        radar_scores: Dict[str, float],
        tag_scores: Dict[str, float],
        rubric_score: Optional[float],
        supporting_portfolios_by_tag: Dict[str, List[Dict[str, Any]]],
        supporting_portfolios_by_dim: Dict[str, List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """
        Computes deterministic matchScore and explanation for a single CareerPath or StudyPath.
        """
        radar_w = path.radar_weights
        tag_w = path.tag_weights

        # 1. Radar match (0-100)
        radar_match = 0.0
        for dim, weight in radar_w.items():
            radar_match += weight * radar_scores.get(dim, 0.0)

        # 2. Tag match (0-100)
        tag_match = 0.0
        for tag, weight in tag_w.items():
            tag_match += weight * tag_scores.get(tag, 0.0)

        # 3. Rubric match and missing data re-normalization
        has_rubric = rubric_score is not None
        if has_rubric:
            rubric_val = float(rubric_score)
            overall_match = 0.60 * radar_match + 0.20 * tag_match + 0.20 * rubric_val
            components = {
                "evidenceRadar": round(radar_match, 1),
                "canonicalTags": round(tag_match, 1),
                "teacherRubric": round(rubric_val, 1),
                "radarMatch": round(radar_match, 1),
                "tagMatch": round(tag_match, 1),
                "rubricMatch": round(rubric_val, 1),
            }
        else:
            # Re-normalize when teacher rubric is absent (Radar = 75%, Tags = 25%)
            overall_match = 0.75 * radar_match + 0.25 * tag_match
            components = {
                "evidenceRadar": round(radar_match, 1),
                "canonicalTags": round(tag_match, 1),
                "teacherRubric": None,
                "radarMatch": round(radar_match, 1),
                "tagMatch": round(tag_match, 1),
                "rubricMatch": 0,
            }

        final_match_score = int(min(100, max(0, round(overall_match))))

        # 4. Resolve supporting dimensions and tags
        supporting_dims = []
        for dim, w in sorted(radar_w.items(), key=lambda x: x[1], reverse=True):
            s = radar_scores.get(dim, 0.0)
            if s > 0:
                supporting_dims.append({"dimension": dim, "score": round(s, 1), "weight": w})

        supporting_tags = []
        for tag, w in sorted(tag_w.items(), key=lambda x: x[1], reverse=True):
            if tag_scores.get(tag, 0.0) > 0:
                supporting_tags.append(tag)

        # 5. Supporting portfolios (provenance)
        supporting_pids = set()
        supporting_portfolio_list = []
        for tag in supporting_tags:
            for p in supporting_portfolios_by_tag.get(tag, []):
                pid = p.get("portfolioId")
                if pid and pid not in supporting_pids:
                    supporting_pids.add(pid)
                    supporting_portfolio_list.append(p)

        for dim_obj in supporting_dims:
            d = dim_obj["dimension"]
            for p in supporting_portfolios_by_dim.get(d, []):
                pid = p.get("portfolioId")
                if pid and pid not in supporting_pids:
                    supporting_pids.add(pid)
                    supporting_portfolio_list.append(p)

        # 6. Structured explanation rationale
        if final_match_score > 0 and (supporting_dims or supporting_tags):
            dim_names = ", ".join([d["dimension"].replace("-", " ").title() for d in supporting_dims[:2]])
            tag_names = ", ".join(supporting_tags[:2]) if supporting_tags else ""
            if tag_names:
                rationale = (
                    f"Rekomendasi eksplorasi ini didukung oleh capaian tervalidasi pada dimensi {dim_names}, "
                    f"serta bukti karya portofolio dengan tag kompetensi {tag_names}."
                )
            else:
                rationale = (
                    f"Rekomendasi eksplorasi ini didukung oleh bukti karya tervalidasi pada dimensi {dim_names}."
                )
        else:
            rationale = "Belum cukup bukti karya tervalidasi yang selaras dengan bidang keahlian ini."

        return {
            "id": path.id,
            "code": path.code,
            "title": path.title,
            "cluster": path.cluster,
            "description": path.description,
            "matchScore": final_match_score,
            "components": components,
            "supportingDimensions": supporting_dims,
            "supportingTags": supporting_tags,
            "evidenceCount": len(supporting_portfolio_list),
            "supportingPortfolios": supporting_portfolio_list,
            "suggestedPathways": path.suggested_pathways,
            "rationale": rationale,
        }

    async def get_student_recommendations(
        self,
        school_id: str,
        student_id: str,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Main recommendation exploration service.
        Returns top 3 career paths, top 3 study paths, evidence confidence, and provenance.
        """
        # 1. Fetch student's Phase 5 skill projection (deterministic radar + rubrics)
        skill_data = await self.projection_service.get_student_skills(school_id, student_id)
        radar_points = skill_data.get("radar", [])
        teacher_rubrics = skill_data.get("teacherRubrics", {})

        # 2. Fetch approved evidence snapshots from MongoDB
        approved_snapshots = await self.portfolio_repo.get_evidence_tag_snapshots_for_student(
            school_id=school_id, student_id=student_id
        )

        # 2a. Prompt 35 & 36 Empty State Gate:
        # If student has zero approved evidence, return advisory onboarding state with empty career & study paths.
        if len(approved_snapshots) == 0:
            now = datetime.now(timezone.utc)
            return {
                "snapshotId": None,
                "scoringVersion": SCORING_VERSION,
                "catalogVersion": CATALOG_VERSION,
                "mappingVersion": MAPPING_VERSION,
                "generatedAt": now.isoformat(),
                "isStale": False,
                "evidenceConfidence": {
                    "score": 0,
                    "level": "limited",
                    "label": "Bukti Terbatas",
                    "approvedPortfolioCount": 0,
                    "distinctDimensionCount": 0,
                    "timeSpanMonths": 0,
                    "distinctPeriodBuckets": 0,
                    "activePeriodCount": 0,
                    "rubricAssessmentCount": 0,
                },
                "careerPaths": [],
                "studyPaths": [],
                "disclaimer": (
                    "Belum cukup bukti tervalidasi untuk membentuk rekomendasi. "
                    "Tambahkan karya dan tunggu validasi guru agar TALENTRA dapat menunjukkan bidang yang dapat kamu eksplorasi."
                ),
            }

        # 3. Calculate fingerprint for staleness
        fingerprint = self._compute_source_fingerprint(
            approved_snapshots, teacher_rubrics, CATALOG_VERSION
        )

        # 4. Check existing snapshot if not forcing refresh
        if not force_refresh:
            latest_snap = await self.portfolio_repo.get_latest_recommendation_snapshot(
                school_id=school_id, student_id=student_id
            )
            if latest_snap and latest_snap.get("source_fingerprint") == fingerprint:
                return {
                    "snapshotId": latest_snap.get("snapshot_id"),
                    "scoringVersion": latest_snap.get("scoring_version", SCORING_VERSION),
                    "catalogVersion": latest_snap.get("catalog_version", CATALOG_VERSION),
                    "mappingVersion": latest_snap.get("mapping_version", MAPPING_VERSION),
                    "generatedAt": (
                        latest_snap["generated_at"].isoformat()
                        if hasattr(latest_snap["generated_at"], "isoformat")
                        else str(latest_snap["generated_at"])
                    ),
                    "isStale": False,
                    "evidenceConfidence": latest_snap.get("evidence_confidence", {}),
                    "careerPaths": latest_snap.get("career_results", []),
                    "studyPaths": latest_snap.get("study_results", []),
                    "disclaimer": (
                        "Rekomendasi ini bersifat eksploratif dan memandu eksplorasi minat/karier siswa "
                        "berdasarkan karya yang telah divalidasi guru pembimbing sekolah. "
                        "Rekomendasi ini bukan penentu mutlak seleksi penerimaan atau kelulusan."
                    ),
                }

        # 5. Extract feature vectors
        radar_scores: Dict[str, float] = {p["dimension"]: float(p["score"]) for p in radar_points}

        # Tag counts with repetition cap (max 2 evidence units per tag per period)
        # Period bucketing to prevent spamming identical works in short window
        tag_period_counts: Dict[str, Dict[str, int]] = {}
        tag_evidence_units: Dict[str, int] = {}
        supporting_portfolios_by_tag: Dict[str, List[Dict[str, Any]]] = {}

        # Preload portfolio titles for provenance
        portfolio_info_cache: Dict[str, Dict[str, Any]] = {}
        for snap in approved_snapshots:
            pid = snap.get("portfolio_id")
            if pid and pid not in portfolio_info_cache:
                item = await self.portfolio_repo.get_portfolio_by_id(school_id, pid)
                portfolio_info_cache[pid] = {
                    "portfolioId": pid,
                    "title": item.get("title", "Karya Portofolio") if item else "Karya Portofolio",
                    "approvedAt": (
                        snap["approved_at"].isoformat()
                        if hasattr(snap["approved_at"], "isoformat")
                        else str(snap.get("approved_at"))
                    ),
                    "tags": snap.get("canonical_tag_ids", []),
                }

        for snap in approved_snapshots:
            pid = snap.get("portfolio_id")
            dt = snap.get("approved_at")
            period = "default"
            if dt:
                if isinstance(dt, str):
                    try:
                        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                    except Exception:
                        dt = None
                if dt:
                    half = "H1" if dt.month <= 6 else "H2"
                    period = f"{dt.year}-{half}"

            p_item = portfolio_info_cache.get(pid)

            for tag in snap.get("canonical_tag_ids", []):
                if tag not in tag_period_counts:
                    tag_period_counts[tag] = {}
                    tag_evidence_units[tag] = 0
                    supporting_portfolios_by_tag[tag] = []

                current_p_count = tag_period_counts[tag].get(period, 0)
                # Repetition cap: max 2 units per tag per period bucket
                if current_p_count < 2:
                    tag_period_counts[tag][period] = current_p_count + 1
                    tag_evidence_units[tag] += 1

                if p_item and p_item not in supporting_portfolios_by_tag[tag]:
                    supporting_portfolios_by_tag[tag].append(p_item)

        # Scale tag scores: min(100, units * 20)
        tag_scores: Dict[str, float] = {
            tag: float(min(100, units * 20)) for tag, units in tag_evidence_units.items()
        }

        # Supporting portfolios by dimension
        supporting_portfolios_by_dim: Dict[str, List[Dict[str, Any]]] = {}
        for p in radar_points:
            d = p["dimension"]
            supporting_portfolios_by_dim[d] = p.get("contributors", [])

        # Rubric average score
        rubric_avg: Optional[float] = None
        if teacher_rubrics and isinstance(teacher_rubrics, dict):
            rub_scores = []
            for item in teacher_rubrics.values():
                sc = item.get("score") if isinstance(item, dict) else item
                if sc is not None and isinstance(sc, (int, float)):
                    # Scale 1-5 to 0-100: (score - 1) * 25
                    rub_scores.append((float(sc) - 1.0) * 25.0)
            if rub_scores:
                rubric_avg = sum(rub_scores) / len(rub_scores)

        # 6. Calculate evidence confidence
        confidence = self._calculate_evidence_confidence(approved_snapshots, radar_points, teacher_rubrics)

        # 7. Evaluate Career Paths
        career_paths = await self.catalog_repo.get_active_career_paths()
        matched_careers = []
        for cp in career_paths:
            res = self._match_path(
                cp,
                radar_scores,
                tag_scores,
                rubric_avg,
                supporting_portfolios_by_tag,
                supporting_portfolios_by_dim,
            )
            matched_careers.append(res)

        # Deterministic tie-breaking: matchScore desc, confidence desc, code asc
        matched_careers.sort(
            key=lambda x: (x["matchScore"], confidence["score"], -ord(x["code"][0]) if x["code"] else 0, x["code"]),
            reverse=True,
        )
        # Fix exact deterministic tie-break ordering:
        matched_careers.sort(
            key=lambda x: (-x["matchScore"], -confidence["score"], x["code"])
        )

        # 8. Evaluate Study Paths
        study_paths = await self.catalog_repo.get_active_study_paths()
        matched_studies = []
        for sp in study_paths:
            res = self._match_path(
                sp,
                radar_scores,
                tag_scores,
                rubric_avg,
                supporting_portfolios_by_tag,
                supporting_portfolios_by_dim,
            )
            matched_studies.append(res)

        matched_studies.sort(
            key=lambda x: (-x["matchScore"], -confidence["score"], x["code"])
        )

        # Top 3 paths
        top_careers = matched_careers[:3]
        top_studies = matched_studies[:3]

        # 9. Save immutable Recommendation Snapshot to MongoDB
        snapshot_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        all_supporting_ids = list(set(
            [p["portfolioId"] for c in top_careers for p in c.get("supportingPortfolios", [])] +
            [p["portfolioId"] for s in top_studies for p in s.get("supportingPortfolios", [])]
        ))

        snapshot_doc = RecommendationSnapshotDocument(
            snapshot_id=snapshot_id,
            school_id=school_id,
            student_id=student_id,
            source_fingerprint=fingerprint,
            catalog_version=CATALOG_VERSION,
            scoring_version=SCORING_VERSION,
            mapping_version=MAPPING_VERSION,
            generated_at=now,
            evidence_confidence=confidence,
            career_results=matched_careers,
            study_results=matched_studies,
            supporting_approval_ids=all_supporting_ids,
        )
        await self.portfolio_repo.save_recommendation_snapshot(snapshot_doc)

        # 10. Audit event
        audit_event_type = (
            AuditEventType.RECOMMENDATION_REFRESHED if force_refresh else AuditEventType.RECOMMENDATION_GENERATED
        )
        audit_logger.log_event(
            audit_event_type,
            user_id=student_id,
            school_id=school_id,
            safe_context="student_recommendation_generated",
            metadata={
                "snapshot_id": snapshot_id,
                "confidence_level": confidence["level"],
                "approved_evidence_count": len(approved_snapshots),
                "catalog_version": CATALOG_VERSION,
            },
        )

        return {
            "snapshotId": snapshot_id,
            "scoringVersion": SCORING_VERSION,
            "catalogVersion": CATALOG_VERSION,
            "mappingVersion": MAPPING_VERSION,
            "generatedAt": now.isoformat(),
            "isStale": False,
            "evidenceConfidence": confidence,
            "careerPaths": matched_careers,
            "studyPaths": matched_studies,
            "disclaimer": (
                "Rekomendasi ini bersifat panduan eksploratif berdasarkan karya yang telah divalidasi guru pembimbing sekolah. "
                "Rekomendasi ini bukan penentu mutlak kelulusan, seleksi masuk perguruan tinggi, atau penerimaan kerja."
            ),
        }

    get_or_generate_recommendation = get_student_recommendations
