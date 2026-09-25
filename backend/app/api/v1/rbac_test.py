from fastapi import APIRouter, Depends
from ..dependencies import require_role, AuthContext
from ...domain.enums import UserRole

router = APIRouter(prefix="/protected", tags=["RBAC Verification"])

@router.get("/student")
async def student_only_endpoint(auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT))):
    return {
        "status": "authorized",
        "message": "Akses diberikan untuk Student",
        "userId": auth_ctx.user_id,
        "schoolId": auth_ctx.school_id,
        "role": auth_ctx.role.value,
    }

@router.get("/teacher")
async def teacher_only_endpoint(auth_ctx: AuthContext = Depends(require_role(UserRole.TEACHER))):
    return {
        "status": "authorized",
        "message": "Akses diberikan untuk Teacher Validator",
        "userId": auth_ctx.user_id,
        "schoolId": auth_ctx.school_id,
        "role": auth_ctx.role.value,
    }

@router.get("/admin")
async def admin_only_endpoint(auth_ctx: AuthContext = Depends(require_role(UserRole.ADMIN))):
    return {
        "status": "authorized",
        "message": "Akses diberikan untuk School Admin",
        "userId": auth_ctx.user_id,
        "schoolId": auth_ctx.school_id,
        "role": auth_ctx.role.value,
    }
