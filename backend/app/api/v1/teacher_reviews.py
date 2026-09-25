from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Header, Query, Response, status
from pydantic import BaseModel

from ...domain.enums import UserRole
from ...api.dependencies import require_role, AuthContext
from ...services.teacher_review_service import (
    TeacherReviewService,
    TeacherDecisionRequestDTO,
)

router = APIRouter(prefix="/teacher/reviews", tags=["Teacher Reviews"])

_review_service: Optional[TeacherReviewService] = None


def get_teacher_review_service() -> TeacherReviewService:
    global _review_service
    if _review_service is None:
        _review_service = TeacherReviewService()
    return _review_service


def set_teacher_review_service(svc: Optional[TeacherReviewService]) -> None:
    global _review_service
    _review_service = svc


class TeacherQueueResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


@router.get("", response_model=TeacherQueueResponse)
async def list_teacher_review_queue(
    class_name: Optional[str] = Query(None, alias="class"),
    tag: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("oldest", alias="sortBy"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth_ctx: AuthContext = Depends(require_role(UserRole.TEACHER)),
    service: TeacherReviewService = Depends(get_teacher_review_service),
):
    """
    Retrieves the teacher's pending approval queue.
    Authorization: Strictly scoped to active teacher assignments in the teacher's school.
    No student outside the teacher's classes will appear in the queue.
    """
    items, total = await service.get_teacher_queue(
        teacher_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        class_name=class_name,
        tag=tag,
        search=search,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )
    return TeacherQueueResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{portfolio_id}")
async def get_teacher_review_detail(
    portfolio_id: str,
    auth_ctx: AuthContext = Depends(require_role(UserRole.TEACHER)),
    service: TeacherReviewService = Depends(get_teacher_review_service),
):
    """
    Returns full review details including exact immutable submitted revision snapshot,
    safe student profile (no NISN), and prior validation history.
    """
    return await service.get_teacher_review_detail(
        teacher_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        portfolio_id=portfolio_id,
    )


@router.get("/{portfolio_id}/evidence/{storage_object_id}/access")
async def get_teacher_evidence_access(
    portfolio_id: str,
    storage_object_id: str,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.TEACHER)),
    service: TeacherReviewService = Depends(get_teacher_review_service),
):
    """
    Generates a short-lived presigned/signed access URL for authorized teacher review.
    Enforces Cache-Control: private, no-store.
    """
    response.headers["Cache-Control"] = "private, no-store"
    return await service.get_evidence_download_access(
        teacher_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        portfolio_id=portfolio_id,
        storage_object_id=storage_object_id,
    )


@router.post("/{portfolio_id}/decision", status_code=status.HTTP_200_OK)
async def submit_teacher_decision(
    portfolio_id: str,
    payload: TeacherDecisionRequestDTO,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    auth_ctx: AuthContext = Depends(require_role(UserRole.TEACHER)),
    service: TeacherReviewService = Depends(get_teacher_review_service),
):
    """
    Unified validation decision endpoint:
    - action='approved' (Endorse): requires all 5 soft-skill rubric dimensions (1..5)
    - action='revision_requested': requires meaningful feedback
    - action='rejected': requires reason and confirmation
    Binds strictly to revisionId to prevent reviewing stale revisions.
    """
    return await service.submit_decision(
        teacher_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        portfolio_id=portfolio_id,
        payload=payload,
        idempotency_key=idempotency_key,
    )
