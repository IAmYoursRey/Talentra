from typing import Optional
from fastapi import APIRouter, Depends

from ...domain.enums import UserRole
from ...api.dependencies import require_role, AuthContext
from ...services.projection_service import StudentSkillProjectionService

router = APIRouter(prefix="/student/skills", tags=["Student Skills"])

_projection_service: Optional[StudentSkillProjectionService] = None


def get_projection_service() -> StudentSkillProjectionService:
    global _projection_service
    if _projection_service is None:
        _projection_service = StudentSkillProjectionService()
    return _projection_service


def set_projection_service(svc: Optional[StudentSkillProjectionService]) -> None:
    global _projection_service
    _projection_service = svc


@router.get("")
async def get_student_skills(
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: StudentSkillProjectionService = Depends(get_projection_service),
):
    """
    Retrieves the authenticated student's validated skill radar and soft-skill rubric summary.
    All scores are calculated deterministically strictly from teacher-approved portfolio revisions.
    Pending, submitted, revision_requested, and rejected evidence contribute zero.
    """
    return await service.get_student_skills(
        school_id=auth_ctx.school_id,
        student_id=auth_ctx.user_id,
    )
