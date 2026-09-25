from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status

from ...domain.enums import UserRole
from ...schemas.admin import (
    CreateClassRequest,
    UpdateClassRequest,
    EnrollStudentRequest,
    AssignTeacherRequest,
)
from ..dependencies import (
    require_role,
    verify_csrf_token,
    AuthContext,
    get_identity_repo,
    IdentityRepository,
)
from ...services.admin_class_service import AdminClassService
from ...repositories.admin_class import AdminClassRepository

router = APIRouter(prefix="/admin/classes", tags=["School Admin - Classes"])

_admin_class_service: Optional[AdminClassService] = None


def set_admin_class_service(svc: Optional[AdminClassService]) -> None:
    global _admin_class_service
    _admin_class_service = svc


def get_admin_class_service(
    identity_repo: IdentityRepository = Depends(get_identity_repo),
) -> AdminClassService:
    global _admin_class_service
    if _admin_class_service is not None:
        return _admin_class_service
    session_factory = getattr(identity_repo, "session_factory", None)
    class_repo = AdminClassRepository(session_factory=session_factory)
    return AdminClassService(admin_class_repo=class_repo)


@router.get("")
async def list_classes(
    response: Response,
    academic_year: Optional[str] = Query(None, alias="academicYear", description="Academic year filter"),
    status: Optional[str] = Query(None, description="Status filter: active or archived"),
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminClassService = Depends(get_admin_class_service),
):
    response.headers["Cache-Control"] = "private, no-store"
    classes = await service.list_classes(
        school_id=auth_ctx.school_id,
        academic_year=academic_year,
        status_filter=status,
    )
    return {"classes": classes}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_class(
    payload: CreateClassRequest,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminClassService = Depends(get_admin_class_service),
    _csrf: None = Depends(verify_csrf_token),
):
    response.headers["Cache-Control"] = "private, no-store"
    return await service.create_class(
        admin_user_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        name=payload.name,
        grade_level=str(payload.gradeLevel),
        academic_year=payload.academicYear,
    )


@router.get("/{class_id}")
async def get_class_detail(
    class_id: str,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminClassService = Depends(get_admin_class_service),
):
    response.headers["Cache-Control"] = "private, no-store"
    return await service.get_class(school_id=auth_ctx.school_id, class_id=class_id)


@router.patch("/{class_id}")
async def update_class(
    class_id: str,
    payload: UpdateClassRequest,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminClassService = Depends(get_admin_class_service),
    _csrf: None = Depends(verify_csrf_token),
):
    response.headers["Cache-Control"] = "private, no-store"
    return await service.update_class(
        admin_user_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        class_id=class_id,
        name=payload.name,
        grade_level=str(payload.gradeLevel) if payload.gradeLevel is not None else None,
        academic_year=payload.academicYear,
    )


@router.post("/{class_id}/archive")
async def archive_class(
    class_id: str,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminClassService = Depends(get_admin_class_service),
    _csrf: None = Depends(verify_csrf_token),
):
    response.headers["Cache-Control"] = "private, no-store"
    return await service.archive_class(
        admin_user_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        class_id=class_id,
    )


@router.post("/{class_id}/students")
async def enroll_student(
    class_id: str,
    payload: EnrollStudentRequest,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminClassService = Depends(get_admin_class_service),
    _csrf: None = Depends(verify_csrf_token),
):
    response.headers["Cache-Control"] = "private, no-store"
    return await service.enroll_student(
        admin_user_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        class_id=class_id,
        student_id=payload.studentId,
    )


@router.delete("/{class_id}/students/{student_id}")
async def unenroll_student(
    class_id: str,
    student_id: str,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminClassService = Depends(get_admin_class_service),
    _csrf: None = Depends(verify_csrf_token),
):
    response.headers["Cache-Control"] = "private, no-store"
    return await service.unenroll_student(
        admin_user_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        class_id=class_id,
        student_id=student_id,
    )


@router.post("/{class_id}/teachers")
async def assign_teacher(
    class_id: str,
    payload: AssignTeacherRequest,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminClassService = Depends(get_admin_class_service),
    _csrf: None = Depends(verify_csrf_token),
):
    response.headers["Cache-Control"] = "private, no-store"
    return await service.assign_teacher(
        admin_user_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        class_id=class_id,
        teacher_id=payload.teacherId,
        assignment_type=payload.assignmentType,
    )


@router.delete("/{class_id}/teachers/{teacher_id}")
async def remove_teacher_assignment(
    class_id: str,
    teacher_id: str,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN)),
    service: AdminClassService = Depends(get_admin_class_service),
    _csrf: None = Depends(verify_csrf_token),
):
    response.headers["Cache-Control"] = "private, no-store"
    return await service.remove_teacher_assignment(
        admin_user_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        class_id=class_id,
        teacher_id=teacher_id,
    )
