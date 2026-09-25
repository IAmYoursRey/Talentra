from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Response

from ...domain.enums import UserRole
from ...api.dependencies import require_role, AuthContext
from ...services.cv_service import CVService
from .student_cv import get_cv_service

router = APIRouter(prefix="/admin/cv", tags=["Admin Digital CV Management"])


class AdminRevokeRequest(BaseModel):
    reason: str = Field(..., min_length=5, description="Alasan pencabutan verifikasi CV")


@router.post("/{verification_id}/revoke")
async def admin_revoke_cv(
    verification_id: str,
    payload: AdminRevokeRequest,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: CVService = Depends(get_cv_service),
) -> Dict[str, Any]:
    """
    Same-school School Admin revokes an issued CV verification record with a mandatory reason.
    Strictly forbids cross-school revocation.
    """
    response.headers["Cache-Control"] = "private, no-store"
    return await service.admin_revoke_cv(
        school_id=auth_ctx.school_id,
        admin_user_id=auth_ctx.user_id,
        verification_id=verification_id,
        reason=payload.reason,
    )
