import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..core.database import AsyncSessionLocal
from ..db.models import (
    TeacherAssignmentModel,
    EnrollmentModel,
    UserModel,
    ClassModel,
    ValidationDecisionModel,
    RubricAssessmentModel,
    SkillTagModel,
    OutboxEventModel,
)


class TeacherValidationRepository:
    def __init__(self, session_factory: Optional[async_sessionmaker[AsyncSession]] = None):
        self.session_factory = session_factory or AsyncSessionLocal

    async def get_teacher_assigned_classes(
        self, school_id: str, teacher_id: str
    ) -> List[str]:
        """Returns list of class_ids actively assigned to the teacher."""
        async with self.session_factory() as session:
            stmt = select(TeacherAssignmentModel.class_id).where(
                and_(
                    TeacherAssignmentModel.school_id == school_id,
                    TeacherAssignmentModel.teacher_id == teacher_id,
                    TeacherAssignmentModel.active.is_(True),
                )
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_eligible_students_for_teacher(
        self, school_id: str, teacher_id: str
    ) -> List[Dict[str, Any]]:
        """
        Resolves students currently enrolled in classes assigned to this teacher.
        Returns safe summary: student_id, student_display_name, class_id, class_name.
        Never returns NISN.
        """
        class_ids = await self.get_teacher_assigned_classes(school_id, teacher_id)
        if not class_ids:
            return []

        async with self.session_factory() as session:
            stmt = (
                select(
                    EnrollmentModel.student_id,
                    UserModel.display_name,
                    EnrollmentModel.class_id,
                    ClassModel.name.label("class_name"),
                )
                .join(UserModel, EnrollmentModel.student_id == UserModel.id)
                .join(ClassModel, EnrollmentModel.class_id == ClassModel.id)
                .where(
                    and_(
                        EnrollmentModel.school_id == school_id,
                        EnrollmentModel.class_id.in_(class_ids),
                        EnrollmentModel.status == "active",
                    )
                )
            )
            result = await session.execute(stmt)
            rows = result.all()
            return [
                {
                    "student_id": r.student_id,
                    "student_display_name": r.display_name,
                    "class_id": r.class_id,
                    "class_name": r.class_name,
                }
                for r in rows
            ]

    async def is_teacher_authorized_for_student(
        self, school_id: str, teacher_id: str, student_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Authorization chain check:
        Teacher must have an active assignment to at least one class
        where the student is actively enrolled, within the same school.
        Returns (is_authorized, teacher_assignment_id).
        """
        async with self.session_factory() as session:
            stmt = (
                select(TeacherAssignmentModel.id)
                .join(
                    EnrollmentModel,
                    and_(
                        TeacherAssignmentModel.class_id == EnrollmentModel.class_id,
                        TeacherAssignmentModel.school_id == EnrollmentModel.school_id,
                    ),
                )
                .where(
                    and_(
                        TeacherAssignmentModel.school_id == school_id,
                        TeacherAssignmentModel.teacher_id == teacher_id,
                        TeacherAssignmentModel.active.is_(True),
                        EnrollmentModel.student_id == student_id,
                        EnrollmentModel.status == "active",
                    )
                )
            )
            result = await session.execute(stmt)
            assignment_id = result.scalars().first()
            if assignment_id:
                return True, assignment_id
            return False, None

    async def get_student_safe_profile(
        self, school_id: str, student_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Returns student's safe display profile and class name without national identifiers.
        """
        async with self.session_factory() as session:
            stmt = (
                select(
                    UserModel.id,
                    UserModel.display_name,
                    ClassModel.name.label("class_name"),
                )
                .outerjoin(
                    EnrollmentModel,
                    and_(
                        UserModel.id == EnrollmentModel.student_id,
                        EnrollmentModel.status == "active",
                    ),
                )
                .outerjoin(ClassModel, EnrollmentModel.class_id == ClassModel.id)
                .where(
                    and_(
                        UserModel.id == student_id,
                        UserModel.school_id == school_id,
                    )
                )
            )
            result = await session.execute(stmt)
            row = result.first()
            if not row:
                return None
            return {
                "student_id": row.id,
                "display_name": row.display_name,
                "class_name": row.class_name or "Siswa",
            }

    async def create_pending_decision(
        self,
        decision_id: str,
        school_id: str,
        portfolio_id: str,
        revision_id: str,
        student_id: str,
        teacher_id: str,
        teacher_assignment_id: Optional[str],
        action: str,
        feedback: Optional[str],
        idempotency_key_hash: Optional[str] = None,
    ) -> ValidationDecisionModel:
        now = datetime.now(timezone.utc)
        model = ValidationDecisionModel(
            id=decision_id,
            school_id=school_id,
            portfolio_id=portfolio_id,
            revision_id=revision_id,
            student_id=student_id,
            teacher_id=teacher_id,
            teacher_assignment_id=teacher_assignment_id,
            action=action,
            feedback=feedback,
            application_status="pending",
            created_at=now,
            idempotency_key_hash=idempotency_key_hash,
        )
        async with self.session_factory() as session:
            session.add(model)
            await session.commit()
            return model

    async def get_decision(self, decision_id: str) -> Optional[ValidationDecisionModel]:
        async with self.session_factory() as session:
            stmt = select(ValidationDecisionModel).where(ValidationDecisionModel.id == decision_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_applied_decision_for_revision(
        self, revision_id: str
    ) -> Optional[ValidationDecisionModel]:
        async with self.session_factory() as session:
            stmt = select(ValidationDecisionModel).where(
                and_(
                    ValidationDecisionModel.revision_id == revision_id,
                    ValidationDecisionModel.application_status == "applied",
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def apply_decision(
        self,
        decision_id: str,
        rubrics: Optional[Dict[str, int]] = None,
        outbox_event_type: Optional[str] = None,
        outbox_payload: Optional[Dict[str, Any]] = None,
    ) -> ValidationDecisionModel:
        now = datetime.now(timezone.utc)
        async with self.session_factory() as session:
            stmt = select(ValidationDecisionModel).where(ValidationDecisionModel.id == decision_id)
            result = await session.execute(stmt)
            decision = result.scalar_one()

            decision.application_status = "applied"
            decision.applied_at = now

            # If rubrics provided (mandatory for approval), persist rubric assessments
            if rubrics:
                for dim_code, score in rubrics.items():
                    rubric_model = RubricAssessmentModel(
                        id=str(uuid.uuid4()),
                        school_id=decision.school_id,
                        decision_id=decision.id,
                        portfolio_id=decision.portfolio_id,
                        revision_id=decision.revision_id,
                        student_id=decision.student_id,
                        teacher_id=decision.teacher_id,
                        dimension_code=dim_code,
                        score=score,
                        created_at=now,
                    )
                    session.add(rubric_model)

            # Persist outbox event for cross-store event coordination
            if outbox_event_type and outbox_payload:
                outbox_evt = OutboxEventModel(
                    id=str(uuid.uuid4()),
                    event_type=outbox_event_type,
                    aggregate_type="portfolio",
                    aggregate_id=decision.portfolio_id,
                    payload_json=json.dumps(outbox_payload),
                    created_at=now,
                )
                session.add(outbox_evt)

            await session.commit()
            return decision

    async def fail_decision(
        self, decision_id: str, failure_code: str
    ) -> ValidationDecisionModel:
        now = datetime.now(timezone.utc)
        async with self.session_factory() as session:
            stmt = select(ValidationDecisionModel).where(ValidationDecisionModel.id == decision_id)
            result = await session.execute(stmt)
            decision = result.scalar_one()

            decision.application_status = "failed"
            decision.failed_at = now
            decision.failure_code = failure_code
            await session.commit()
            return decision

    async def get_validation_history_for_portfolio(
        self, school_id: str, portfolio_id: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieves safe validation decision history for a portfolio item.
        Exposes decision action, timestamp, revision id, and teacher display title.
        """
        async with self.session_factory() as session:
            stmt = (
                select(
                    ValidationDecisionModel.id,
                    ValidationDecisionModel.action,
                    ValidationDecisionModel.feedback,
                    ValidationDecisionModel.revision_id,
                    ValidationDecisionModel.created_at,
                    UserModel.display_name.label("teacher_name"),
                )
                .join(UserModel, ValidationDecisionModel.teacher_id == UserModel.id)
                .where(
                    and_(
                        ValidationDecisionModel.school_id == school_id,
                        ValidationDecisionModel.portfolio_id == portfolio_id,
                        ValidationDecisionModel.application_status == "applied",
                    )
                )
                .order_by(ValidationDecisionModel.created_at.desc())
            )
            result = await session.execute(stmt)
            rows = result.all()
            return [
                {
                    "decisionId": r.id,
                    "action": r.action,
                    "feedback": r.feedback,
                    "revisionId": r.revision_id,
                    "createdAt": r.created_at.isoformat() if r.created_at else None,
                    "validatorTitle": f"Guru ({r.teacher_name})",
                }
                for r in rows
            ]

    async def get_pending_decisions_older_than(
        self, threshold_seconds: int = 60
    ) -> List[ValidationDecisionModel]:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=threshold_seconds)
        async with self.session_factory() as session:
            stmt = select(ValidationDecisionModel).where(
                and_(
                    ValidationDecisionModel.application_status == "pending",
                    ValidationDecisionModel.created_at <= cutoff,
                )
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_rubric_summary_for_student(
        self, school_id: str, student_id: str
    ) -> List[Dict[str, Any]]:
        """
        Computes average scores and counts for each of the 5 soft-skill dimensions.
        Considers ONLY applied approved decisions.
        """
        dim_labels = {
            "initiative": "Inisiatif",
            "collaboration": "Kolaborasi",
            "communication": "Komunikasi",
            "responsibility": "Tanggung Jawab",
            "resilience": "Daya Juang",
        }
        ordered_dims = ["initiative", "collaboration", "communication", "responsibility", "resilience"]

        async with self.session_factory() as session:
            stmt = (
                select(
                    RubricAssessmentModel.dimension_code,
                    func.avg(RubricAssessmentModel.score).label("avg_score"),
                    func.count(RubricAssessmentModel.id).label("count_score"),
                )
                .join(
                    ValidationDecisionModel,
                    RubricAssessmentModel.decision_id == ValidationDecisionModel.id,
                )
                .where(
                    and_(
                        RubricAssessmentModel.school_id == school_id,
                        RubricAssessmentModel.student_id == student_id,
                        ValidationDecisionModel.action == "approved",
                        ValidationDecisionModel.application_status == "applied",
                    )
                )
                .group_by(RubricAssessmentModel.dimension_code)
            )
            result = await session.execute(stmt)
            rows = {r.dimension_code: (float(r.avg_score), int(r.count_score)) for r in result.all()}

            summary = []
            for dim in ordered_dims:
                avg_val, cnt = rows.get(dim, (0.0, 0))
                summary.append({
                    "dimensionCode": dim,
                    "displayName": dim_labels[dim],
                    "averageScore": round(avg_val, 1) if cnt > 0 else 0.0,
                    "assessmentCount": cnt,
                })
            return summary

    async def get_radar_tag_mappings(self) -> Dict[str, str]:
        """
        Returns mapping from tag code and id to radar dimension code from PostgreSQL catalog.
        """
        mapping: Dict[str, str] = {}
        try:
            async with self.session_factory() as session:
                stmt = select(SkillTagModel.id, SkillTagModel.code, SkillTagModel.radar_dimension).where(
                    SkillTagModel.active.is_(True)
                )
                result = await session.execute(stmt)
                rows = result.all()
                if rows:
                    for r in rows:
                        if r.radar_dimension:
                            mapping[r.code] = r.radar_dimension
                            mapping[r.id] = r.radar_dimension
                    return mapping
        except Exception:
            pass

        # Fallback to standard canonical mapping supporting both codes and tag_ IDs
        base_map = {
            "public-speaking": "communication",
            "writing": "communication",
            "leadership": "leadership",
            "event-management": "leadership",
            "web-development": "digital-literacy",
            "data-analysis": "digital-literacy",
            "video-editing": "digital-literacy",
            "digital-literacy": "digital-literacy",
            "problem-solving": "problem-solving",
            "research": "problem-solving",
            "ui-ux": "creativity",
            "graphic-design": "creativity",
            "creativity": "creativity",
            "teamwork": "collaboration",
        }
        for code, dim in base_map.items():
            mapping[code] = dim
            mapping[f"tag_{code.replace('-', '_')}"] = dim
        return mapping
