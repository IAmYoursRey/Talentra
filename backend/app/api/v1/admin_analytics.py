from typing import Optional
from fastapi import APIRouter, Depends, Query, Response

from ...domain.enums import UserRole
from ..dependencies import (
    require_role,
    AuthContext,
    get_identity_repo,
    IdentityRepository,
)
from ...services.school_analytics_service import SchoolAnalyticsService

router = APIRouter(prefix="/admin/analytics", tags=["School Admin - Analytics"])

_school_analytics_service: Optional[SchoolAnalyticsService] = None


def set_school_analytics_service(svc: Optional[SchoolAnalyticsService]) -> None:
    global _school_analytics_service
    _school_analytics_service = svc


def get_school_analytics_service(
    identity_repo: IdentityRepository = Depends(get_identity_repo),
) -> SchoolAnalyticsService:
    global _school_analytics_service
    if _school_analytics_service is not None:
        return _school_analytics_service
    session_factory = getattr(identity_repo, "session_factory", None)
    return SchoolAnalyticsService(session_factory=session_factory)


@router.get("/overview")
async def get_overview(
    response: Response,
    academic_year: Optional[str] = Query(None, alias="academicYear"),
    grade_level: Optional[str] = Query(None, alias="gradeLevel"),
    class_id: Optional[str] = Query(None, alias="classId"),
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: SchoolAnalyticsService = Depends(get_school_analytics_service),
):
    """
    Unified school analytics overview.
    Strictly tenant-scoped.
    """
    response.headers["Cache-Control"] = "private, no-store"
    return await service.get_overview(
        school_id=auth_ctx.school_id,
        academic_year=academic_year,
        grade_level=grade_level,
        class_id=class_id,
    )


@router.get("/talent")
async def get_talent_heatmap(
    response: Response,
    academic_year: Optional[str] = Query(None, alias="academicYear"),
    grade_level: Optional[str] = Query(None, alias="gradeLevel"),
    class_id: Optional[str] = Query(None, alias="classId"),
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: SchoolAnalyticsService = Depends(get_school_analytics_service),
):
    """
    Returns school talent coverage and mean evidence index.
    Based on teacher-approved evidence only.
    Cohorts < 5 unique students are suppressed for privacy.
    """
    response.headers["Cache-Control"] = "private, no-store"
    return await service.get_talent_heatmap(
        school_id=auth_ctx.school_id,
        academic_year=academic_year,
        grade_level=grade_level,
        class_id=class_id,
    )


@router.get("/rubrics")
async def get_rubric_aggregates(
    response: Response,
    academic_year: Optional[str] = Query(None, alias="academicYear"),
    grade_level: Optional[str] = Query(None, alias="gradeLevel"),
    class_id: Optional[str] = Query(None, alias="classId"),
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: SchoolAnalyticsService = Depends(get_school_analytics_service),
):
    """
    Returns aggregated teacher rubric observations for soft skills.
    Applies privacy suppression if unique students in cohort < 5.
    """
    response.headers["Cache-Control"] = "private, no-store"
    return await service.get_rubric_aggregates(
        school_id=auth_ctx.school_id,
        academic_year=academic_year,
        grade_level=grade_level,
        class_id=class_id,
    )


@router.get("/validation")
async def get_validation_metrics(
    response: Response,
    academic_year: Optional[str] = Query(None, alias="academicYear"),
    grade_level: Optional[str] = Query(None, alias="gradeLevel"),
    class_id: Optional[str] = Query(None, alias="classId"),
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: SchoolAnalyticsService = Depends(get_school_analytics_service),
):
    """
    Returns operational validation metrics: pending count, throughput, completion rate.
    """
    response.headers["Cache-Control"] = "private, no-store"
    return await service.get_validation_metrics(
        school_id=auth_ctx.school_id,
        academic_year=academic_year,
        grade_level=grade_level,
        class_id=class_id,
    )
