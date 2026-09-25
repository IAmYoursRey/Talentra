import uuid
from typing import Callable
from fastapi import Request, Depends, HTTPException, status
from ..core.config import settings
from ..core.security import decode_access_token
from ..core.csrf import validate_csrf_tokens
from ..core.audit import audit_logger
from ..domain.enums import UserRole, UserStatus, AuditEventType
from ..domain.models import User, School, SessionRecord
from ..repositories.base import IdentityRepository, SessionRepository, AuditRepository
from ..repositories.in_memory import (
    InMemoryIdentityRepository,
    InMemorySessionRepository,
    InMemoryAuditRepository,
)
from ..repositories.postgres import (
    PostgresIdentityRepository,
    PostgresSessionRepository,
    PostgresAuditRepository,
)

_identity_repo: IdentityRepository | None = None
_session_repo: SessionRepository | None = None
_audit_repo: AuditRepository | None = None


def get_identity_repo() -> IdentityRepository:
    global _identity_repo
    if _identity_repo is not None:
        return _identity_repo
    if settings.app_env == "production" and settings.repository_backend == "in_memory":
        raise RuntimeError("CRITICAL: Production cannot use in-memory repositories! PostgreSQL required.")
    if settings.repository_backend == "postgres":
        _identity_repo = PostgresIdentityRepository()
    else:
        _identity_repo = InMemoryIdentityRepository()
    return _identity_repo


def get_session_repo() -> SessionRepository:
    global _session_repo
    if _session_repo is not None:
        return _session_repo
    if settings.repository_backend == "postgres":
        _session_repo = PostgresSessionRepository()
    else:
        _session_repo = InMemorySessionRepository()
    return _session_repo


def get_audit_repo() -> AuditRepository:
    global _audit_repo
    if _audit_repo is not None:
        return _audit_repo
    if settings.repository_backend == "postgres":
        _audit_repo = PostgresAuditRepository()
    else:
        _audit_repo = InMemoryAuditRepository()
    return _audit_repo


def set_identity_repo(repo: IdentityRepository | None) -> None:
    global _identity_repo
    _identity_repo = repo


def set_session_repo(repo: SessionRepository | None) -> None:
    global _session_repo
    _session_repo = repo


def set_audit_repo(repo: AuditRepository | None) -> None:
    global _audit_repo
    _audit_repo = repo

class AuthContext:
    def __init__(self, session: SessionRecord, user: User, school: School):
        self.session = session
        self.user = user
        self.school = school
        self.user_id = user.id
        self.school_id = school.id
        self.role = user.role
        self.must_change_password = getattr(user, "must_change_password", False)

async def get_optional_auth_context(
    request: Request,
    session_repo: SessionRepository = Depends(get_session_repo),
    identity_repo: IdentityRepository = Depends(get_identity_repo),
) -> AuthContext | None:
    """Extract and validate session from HttpOnly cookie without throwing if unauthenticated."""
    cookie_token = request.cookies.get(settings.cookie_name)
    if not cookie_token:
        return None

    try:
        payload = decode_access_token(cookie_token)
    except Exception:
        return None

    session_id = payload.get("sid")
    user_id = payload.get("sub")
    school_id = payload.get("school_id")

    if not session_id or not user_id or not school_id:
        return None

    # Check session in registry
    session = await session_repo.get_session(session_id)
    if not session or not session.is_valid:
        return None

    # Check user and school
    user = await identity_repo.get_user_by_id(user_id)
    if not user or user.status == UserStatus.DISABLED:
        return None

    school = await identity_repo.get_school_by_id(school_id)
    if not school:
        return None

    return AuthContext(session=session, user=user, school=school)

async def require_authenticated_user(
    request: Request,
    auth_ctx: AuthContext | None = Depends(get_optional_auth_context),
) -> AuthContext:
    """Strict dependency requiring authenticated, active session. Denies otherwise."""
    req_id = str(uuid.uuid4())
    if not auth_ctx:
        audit_logger.log(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            safe_context="Unauthenticated access attempt to protected endpoint",
            correlation_id=req_id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_SESSION_REQUIRED",
                "message": "Sesi autentikasi diperlukan untuk mengakses layanan ini.",
                "requestId": req_id,
            },
        )

    # Server-enforced must_change_password gate (Phase 6 Requirement 15 & 61)
    if auth_ctx.must_change_password:
        path = request.url.path
        allowed_paths = [
            f"{settings.api_prefix}/auth/me",
            f"{settings.api_prefix}/auth/csrf",
            f"{settings.api_prefix}/auth/change-password",
            f"{settings.api_prefix}/auth/logout",
        ]
        if path not in allowed_paths:
            audit_logger.log(
                event_type=AuditEventType.AUTH_FORBIDDEN,
                safe_context="Access blocked: user must change temporary password before accessing protected endpoints",
                user_id=auth_ctx.user_id,
                school_id=auth_ctx.school_id,
                correlation_id=req_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "AUTH_PASSWORD_CHANGE_REQUIRED",
                    "message": "Pengguna wajib memperbarui kata sandi sementara sebelum melanjutkan.",
                    "requestId": req_id,
                },
            )

    return auth_ctx

def require_role(required_role: UserRole) -> Callable:
    """Factory creating strict role authorization dependency. Default deny!"""
    async def role_checker(auth_ctx: AuthContext = Depends(require_authenticated_user)) -> AuthContext:
        req_id = str(uuid.uuid4())
        if auth_ctx.role != required_role:
            audit_logger.log(
                event_type=AuditEventType.AUTH_FORBIDDEN,
                safe_context=f"Cross-role access denied: user_role={auth_ctx.role.value}, required_role={required_role.value}",
                user_id=auth_ctx.user_id,
                school_id=auth_ctx.school_id,
                correlation_id=req_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "AUTH_FORBIDDEN",
                    "message": f"Akses ditolak. Anda tidak memiliki otoritas hak akses sebagai {required_role.value}.",
                    "requestId": req_id,
                },
            )
        return auth_ctx
    return role_checker

def require_any_role(*allowed_roles: UserRole) -> Callable:
    """Allows access if user role is in allowed_roles. Default deny otherwise."""
    async def multi_role_checker(auth_ctx: AuthContext = Depends(require_authenticated_user)) -> AuthContext:
        req_id = str(uuid.uuid4())
        if auth_ctx.role not in allowed_roles:
            audit_logger.log(
                event_type=AuditEventType.AUTH_FORBIDDEN,
                safe_context=f"Role forbidden. user_role={auth_ctx.role.value}, allowed={[r.value for r in allowed_roles]}",
                user_id=auth_ctx.user_id,
                school_id=auth_ctx.school_id,
                correlation_id=req_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "AUTH_FORBIDDEN",
                    "message": "Akses ditolak untuk peran pengguna saat ini.",
                    "requestId": req_id,
                },
            )
        return auth_ctx
    return multi_role_checker

async def verify_csrf_token(request: Request) -> None:
    """Verifies CSRF token for mutating requests when cookie session is present."""
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        # Check if auth cookie exists
        if settings.cookie_name in request.cookies:
            cookie_csrf = request.cookies.get(settings.csrf_cookie_name)
            header_csrf = request.headers.get(settings.csrf_header_name)
            
            if not validate_csrf_tokens(cookie_csrf, header_csrf):
                req_id = str(uuid.uuid4())
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "CSRF_INVALID",
                        "message": "Validasi keamanan CSRF gagal. Muat ulang halaman dan coba kembali.",
                        "requestId": req_id,
                    },
                )
