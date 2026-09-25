from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Response

from ...domain.enums import UserRole
from ...api.dependencies import require_role, AuthContext
from ...services.recommendation_engine import RecommendationEngineService

router = APIRouter(prefix="/student/recommendations", tags=["Student Recommendations"])

_recommendation_service: Optional[RecommendationEngineService] = None


def get_recommendation_service() -> RecommendationEngineService:
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = RecommendationEngineService()
    return _recommendation_service


def set_recommendation_service(svc: Optional[RecommendationEngineService]) -> None:
    global _recommendation_service
    _recommendation_service = svc


@router.get("")
async def get_student_recommendations(
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: RecommendationEngineService = Depends(get_recommendation_service),
) -> Dict[str, Any]:
    """
    Retrieves evidence-based career & study exploration paths for the authenticated student.
    Strictly advisory. Consumes only teacher-approved portfolio evidence.
    No protected traits, admissions, or employability scores.
    """
    # Enforce private caching - personal student exploration data must not be cached publicly
    response.headers["Cache-Control"] = "private, no-store"

    return await service.get_or_generate_recommendation(
        school_id=auth_ctx.school_id,
        student_id=auth_ctx.user_id,
        force_refresh=False,
    )


@router.post("/refresh")
async def refresh_student_recommendations(
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: RecommendationEngineService = Depends(get_recommendation_service),
) -> Dict[str, Any]:
    """
    Explicitly recomputes recommendations and persists an immutable snapshot
    from the current teacher-approved evidence and teacher rubric observations.
    """
    response.headers["Cache-Control"] = "private, no-store"

    return await service.get_or_generate_recommendation(
        school_id=auth_ctx.school_id,
        student_id=auth_ctx.user_id,
        force_refresh=True,
    )
