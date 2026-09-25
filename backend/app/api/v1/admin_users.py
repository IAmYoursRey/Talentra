from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status

from ...domain.enums import UserRole
from ...schemas.admin import CreateStudentRequest, CreateTeacherRequest, UpdateUserRequest
from ..dependencies import (
    require_role,
    verify_csrf_token,
    AuthContext,
    get_session_repo,
    get_identity_repo,
    SessionRepository,
    IdentityRepository,
)
from ...services.admin_user_service import AdminUserService
from ...repositories.admin_user import AdminUserRepository

router = APIRouter(prefix="/admin/users", tags=["School Admin - Users"])

_admin_user_service: Optional[AdminUserService] = None


def set_admin_user_service(svc: Optional[AdminUserService]) -> None:
    global _admin_user_service
    _admin_user_service = svc


def get_admin_user_service(
    session_repo: SessionRepository = Depends(get_session_repo),
    identity_repo: IdentityRepository = Depends(get_identity_repo),
) -> AdminUserService:
    global _admin_user_service
    if _admin_user_service is not None:
        return _admin_user_service
    session_factory = getattr(identity_repo, "session_factory", None)
    admin_repo = AdminUserRepository(session_factory=session_factory)
    return AdminUserService(admin_user_repo=admin_repo, session_repo=session_repo)


@router.get("")
async def list_users(
    response: Response,
    role: Optional[str] = Query(None, description="Role filter: student or teacher"),
    status: Optional[str] = Query(None, description="Status filter: active or disabled"),
    class_id: Optional[str] = Query(None, alias="classId", description="Class UUID filter"),
    grade_level: Optional[str] = Query(None, alias="gradeLevel", description="Grade level filter"),
    search: Optional[str] = Query(None, description="Search query for name or email"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminUserService = Depends(get_admin_user_service),
):
    """
    Lists users for the school tenant.
    Never returns password hashes or raw official national identifiers.
    """
    response.headers["Cache-Control"] = "private, no-store"
    items, total = await service.list_users(
        school_id=auth_ctx.school_id,
        role=role,
        status=status,
        class_id=class_id,
        grade_level=grade_level,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/students", status_code=status.HTTP_201_CREATED)
async def create_student(
    payload: CreateStudentRequest,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminUserService = Depends(get_admin_user_service),
    _csrf: None = Depends(verify_csrf_token),
):
    """
    Creates a student account with keyed HMAC lookup and temporary password.
    Temporary password is returned only ONCE.
    """
    response.headers["Cache-Control"] = "private, no-store"
    return await service.create_student(
        admin_user_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        display_name=payload.displayName,
        nisn=payload.nisn,
        grade_level=str(payload.gradeLevel),
        class_id=payload.classId,
    )


@router.post("/teachers", status_code=status.HTTP_201_CREATED)
async def create_teacher(
    payload: CreateTeacherRequest,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminUserService = Depends(get_admin_user_service),
    _csrf: None = Depends(verify_csrf_token),
):
    """
    Creates a teacher account with keyed HMAC lookup and temporary password.
    Temporary password is returned only ONCE.
    """
    response.headers["Cache-Control"] = "private, no-store"
    return await service.create_teacher(
        admin_user_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        display_name=payload.displayName,
        identifier=payload.identifier,
        title=payload.title,
    )


@router.get("/{user_id}")
async def get_user_detail(
    user_id: str,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminUserService = Depends(get_admin_user_service),
):
    response.headers["Cache-Control"] = "private, no-store"
    return await service.get_user(school_id=auth_ctx.school_id, user_id=user_id)


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    payload: UpdateUserRequest,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminUserService = Depends(get_admin_user_service),
    _csrf: None = Depends(verify_csrf_token),
):
    """Updates safe profile fields (displayName, gradeLevel, title)."""
    response.headers["Cache-Control"] = "private, no-store"
    return await service.update_user(
        admin_user_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        user_id=user_id,
        display_name=payload.displayName,
        grade_level=str(payload.gradeLevel) if payload.gradeLevel is not None else None,
        title=payload.title,
    )


@router.post("/{user_id}/disable")
async def disable_user(
    user_id: str,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminUserService = Depends(get_admin_user_service),
    _csrf: None = Depends(verify_csrf_token),
):
    """Disables user and revokes active sessions."""
    response.headers["Cache-Control"] = "private, no-store"
    return await service.disable_user(
        admin_user_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        user_id=user_id,
    )


@router.post("/{user_id}/reactivate")
async def reactivate_user(
    user_id: str,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminUserService = Depends(get_admin_user_service),
    _csrf: None = Depends(verify_csrf_token),
):
    """Reactivates disabled user."""
    response.headers["Cache-Control"] = "private, no-store"
    return await service.reactivate_user(
        admin_user_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        user_id=user_id,
    )


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminUserService = Depends(get_admin_user_service),
    _csrf: None = Depends(verify_csrf_token),
):
    """Resets user password to random temporary credential and revokes sessions."""
    response.headers["Cache-Control"] = "private, no-store"
    return await service.reset_password(
        admin_user_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        user_id=user_id,
    )
