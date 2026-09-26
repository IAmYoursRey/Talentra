from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Header, Response, Query, status
from fastapi.responses import RedirectResponse

from ...domain.enums import UserRole
from ...api.dependencies import require_role, AuthContext
from ...services.cv_service import CVService

router = APIRouter(prefix="/student/cv", tags=["Student Digital CV"])

_cv_service: Optional[CVService] = None


def get_cv_service() -> CVService:
    global _cv_service
    if _cv_service is None:
        _cv_service = CVService()
    return _cv_service


def set_cv_service(svc: Optional[CVService]) -> None:
    global _cv_service
    _cv_service = svc


class GenerateCVRequest(BaseModel):
    portfolioIds: List[str] = Field(..., min_length=1, max_length=8)
    includeTeacherCompetencies: bool = True
    includeExploration: bool = False


class RevokeCVRequest(BaseModel):
    reason: Optional[str] = "Dicabut oleh siswa"


@router.get("")
async def get_student_cv_context(
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: CVService = Depends(get_cv_service),
) -> Dict[str, Any]:
    """
    Retrieves candidate data for CV generation and list of previously issued CV versions.
    Includes ONLY teacher-approved portfolio items.
    """
    response.headers["Cache-Control"] = "private, no-store"
    return await service.get_student_cv_builder_context(
        school_id=auth_ctx.school_id, student_id=auth_ctx.user_id
    )


@router.post("")
async def generate_student_cv(
    payload: GenerateCVRequest,
    response: Response,
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: CVService = Depends(get_cv_service),
) -> Dict[str, Any]:
    """
    Generates an immutable CV snapshot, renders selectable-text PDF,
    privately stores the document, and creates an opaque verification record with QR token.
    """
    response.headers["Cache-Control"] = "private, no-store"
    return await service.generate_cv(
        school_id=auth_ctx.school_id,
        student_id=auth_ctx.user_id,
        portfolio_ids=payload.portfolioIds,
        include_teacher_competencies=payload.includeTeacherCompetencies,
        include_exploration=payload.includeExploration,
        idempotency_key=x_idempotency_key,
    )


@router.get("/{snapshot_id}")
async def get_cv_detail(
    snapshot_id: str,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: CVService = Depends(get_cv_service),
) -> Dict[str, Any]:
    """
    Retrieves full point-in-time snapshot details for the student owner.
    """
    response.headers["Cache-Control"] = "private, no-store"
    return await service.get_cv_detail(
        school_id=auth_ctx.school_id, student_id=auth_ctx.user_id, snapshot_id=snapshot_id
    )


@router.get("/{snapshot_id}/access")
async def get_cv_download_access(
    snapshot_id: str,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: CVService = Depends(get_cv_service),
) -> Dict[str, Any]:
    """
    Issues short-lived signed GET URL for student to download private CV PDF directly from Blob.
    Never caches response.
    """
    response.headers["Cache-Control"] = "private, no-store"
    return await service.get_cv_download_access(
        school_id=auth_ctx.school_id, student_id=auth_ctx.user_id, snapshot_id=snapshot_id
    )


@router.get("/{snapshot_id}/download")
async def download_cv_pdf(
    snapshot_id: str,
    redirect: bool = Query(True),
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: CVService = Depends(get_cv_service),
):
    """
    Enforces student ownership and audits download access.
    In cloud/Blob mode, issues 307 temporary redirect to the signed GET URL.
    """
    from ...storage.vercel_blob import VercelBlobStorage
    if isinstance(service.storage, VercelBlobStorage) and redirect:
        access_info = await service.get_cv_download_access(
            school_id=auth_ctx.school_id, student_id=auth_ctx.user_id, snapshot_id=snapshot_id
        )
        if access_info.get("downloadUrl", "").startswith("http"):
            return RedirectResponse(
                url=access_info["downloadUrl"],
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Cache-Control": "private, no-store"},
            )

    pdf_bytes, filename = await service.download_cv_pdf(
        school_id=auth_ctx.school_id, student_id=auth_ctx.user_id, snapshot_id=snapshot_id
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/{snapshot_id}/revoke")
async def revoke_student_cv(
    snapshot_id: str,
    payload: RevokeCVRequest,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: CVService = Depends(get_cv_service),
) -> Dict[str, Any]:
    """
    Student revokes own issued CV.
    Public verification will immediately reflect the REVOKED status.
    """
    response.headers["Cache-Control"] = "private, no-store"
    return await service.revoke_cv(
        school_id=auth_ctx.school_id,
        student_id=auth_ctx.user_id,
        snapshot_id=snapshot_id,
        reason=payload.reason or "Dicabut oleh siswa",
    )
