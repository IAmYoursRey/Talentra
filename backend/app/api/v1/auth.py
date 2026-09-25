import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from ...core.config import settings
from ...core.security import verify_password, hash_password, create_access_token
from ...core.rate_limiter import login_rate_limiter
from ...core.csrf import generate_csrf_token
from ...core.audit import audit_logger
from ...domain.enums import UserRole, UserStatus, IdentifierType, AuditEventType
from ...domain.models import SessionRecord
from ...domain.normalizers import normalize_login_identifier
from ...schemas.auth import (
    LoginRequest,
    DemoLoginRequest,
    LoginResponse,
    UserResponse,
    SchoolBrief,
    LogoutResponse,
    CsrfResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
)
from ..dependencies import (
    get_identity_repo,
    get_session_repo,
    get_audit_repo,
    require_authenticated_user,
    verify_csrf_token,
    AuthContext,
    IdentityRepository,
    SessionRepository,
    AuditRepository,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

def _set_auth_cookies(response: Response, token: str, csrf_token: str) -> None:
    # 1. HttpOnly JWT Session Cookie
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
        max_age=settings.access_token_expire_minutes * 60,
    )
    # 2. Readable CSRF Cookie (for client double-submit header)
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
        max_age=settings.access_token_expire_minutes * 60,
    )

def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        key=settings.cookie_name,
        path="/",
        domain=settings.cookie_domain,
    )
    response.delete_cookie(
        key=settings.csrf_cookie_name,
        path="/",
        domain=settings.cookie_domain,
    )

def _get_canonical_redirect(role: UserRole) -> str:
    if role == UserRole.STUDENT:
        return "/student"
    elif role == UserRole.TEACHER:
        return "/teacher"
    return "/admin"

@router.get("/csrf", response_model=CsrfResponse)
async def get_csrf_token(response: Response):
    """Issues fresh CSRF token and sets the verification cookie."""
    token = generate_csrf_token()
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return CsrfResponse(csrfToken=token)

@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    identity_repo: IdentityRepository = Depends(get_identity_repo),
    session_repo: SessionRepository = Depends(get_session_repo),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    req_id = str(uuid.uuid4())
    raw_identifier = payload.identifier.strip()

    # 1. Rate Limiting Check
    if login_rate_limiter.is_rate_limited(raw_identifier):
        audit_logger.log(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            safe_context="Login rate limit exceeded",
            correlation_id=req_id,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "AUTH_RATE_LIMITED",
                "message": "Terlalu banyak percobaan masuk. Silakan coba beberapa saat lagi demi keamanan akun Anda.",
                "requestId": req_id,
            },
        )

    # 2. Normalize Identifier
    try:
        norm_result = normalize_login_identifier(raw_identifier)
    except ValueError:
        login_rate_limiter.record_attempt(raw_identifier)
        audit_logger.log(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            safe_context="Invalid identifier format submitted",
            correlation_id=req_id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_INVALID_CREDENTIALS",
                "message": "ID pengguna atau kata sandi tidak sesuai.",
                "requestId": req_id,
            },
        )

    # 3. Lookup Identity
    identity_match = await identity_repo.get_identity_by_identifier(
        normalized_identifier=norm_result.normalized,
        identifier_type=norm_result.identifier_type,
    )

    if not identity_match:
        login_rate_limiter.record_attempt(raw_identifier)
        audit_logger.log(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            safe_context=f"Identity lookup not found for type {norm_result.identifier_type.value}",
            correlation_id=req_id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_INVALID_CREDENTIALS",
                "message": "ID pengguna atau kata sandi tidak sesuai.",
                "requestId": req_id,
            },
        )

    auth_identity, user = identity_match

    # 4. Verify Password & Account Status
    if not auth_identity.active or user.status == UserStatus.DISABLED:
        login_rate_limiter.record_attempt(raw_identifier)
        audit_logger.log(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            safe_context="Login attempt on inactive/disabled account",
            user_id=user.id,
            school_id=user.school_id,
            correlation_id=req_id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_ACCOUNT_DISABLED",
                "message": "ID pengguna atau kata sandi tidak sesuai.",
                "requestId": req_id,
            },
        )

    if not verify_password(payload.password, auth_identity.password_hash):
        login_rate_limiter.record_attempt(raw_identifier)
        audit_logger.log(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            safe_context="Password mismatch for user",
            user_id=user.id,
            school_id=user.school_id,
            correlation_id=req_id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_INVALID_CREDENTIALS",
                "message": "ID pengguna atau kata sandi tidak sesuai.",
                "requestId": req_id,
            },
        )

    # Reset rate limit on success
    login_rate_limiter.reset(raw_identifier)

    # 5. Create Session in Registry
    session_id = str(uuid.uuid4())
    token, expires_at = create_access_token(
        user_id=user.id,
        school_id=user.school_id,
        role=user.role,
        session_id=session_id,
    )

    session_record = SessionRecord(
        session_id=session_id,
        user_id=user.id,
        school_id=user.school_id,
        role=user.role,
        expires_at=expires_at,
    )
    await session_repo.create_session(session_record)

    # 6. Audit Success (NEVER log password or full NISN/NIP)
    audit_logger.log(
        event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
        safe_context=f"Login successful for role {user.role.value}",
        user_id=user.id,
        school_id=user.school_id,
        correlation_id=req_id,
    )

    # 7. Set Cookies
    csrf_token = generate_csrf_token()
    _set_auth_cookies(response, token, csrf_token)

    school = await identity_repo.get_school_by_id(user.school_id)
    school_name = school.name if school else "Sekolah TALENTRA"

    return LoginResponse(
        user=UserResponse(
            id=user.id,
            displayName=user.display_name,
            role=user.role,
            email=user.email,
            school=SchoolBrief(id=user.school_id, name=school_name),
            maskedIdentifier=user.masked_identifier,
            className=user.class_name,
            title=user.title,
        ),
        redirectTo=_get_canonical_redirect(user.role),
    )

@router.post("/demo-login", response_model=LoginResponse)
async def demo_login(
    payload: DemoLoginRequest,
    response: Response,
    identity_repo: IdentityRepository = Depends(get_identity_repo),
    session_repo: SessionRepository = Depends(get_session_repo),
):
    """
    Development-only demo persona authentication endpoint.
    Strictly forbidden in production mode!
    """
    req_id = str(uuid.uuid4())
    if not settings.enable_demo_auth or settings.app_env == "production":
        audit_logger.log(
            event_type=AuditEventType.AUTH_FORBIDDEN,
            safe_context="Unauthorized access attempt to demo-login in non-development environment",
            correlation_id=req_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "AUTH_FORBIDDEN",
                "message": "Akses autentikasi demo dinonaktifkan pada lingkungan ini.",
                "requestId": req_id,
            },
        )

    # Map requested demo role to synthetic user ID
    target_user_id = {
        UserRole.STUDENT: "usr_std_001",
        UserRole.TEACHER: "usr_tch_002",
        UserRole.ADMIN: "usr_adm_003",
    }.get(payload.role)

    user = await identity_repo.get_user_by_id(target_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "VALIDATION_ERROR", "message": "Demo persona tidak ditemukan.", "requestId": req_id},
        )

    # Real session & JWT creation for demo user
    session_id = str(uuid.uuid4())
    token, expires_at = create_access_token(
        user_id=user.id,
        school_id=user.school_id,
        role=user.role,
        session_id=session_id,
    )

    session_record = SessionRecord(
        session_id=session_id,
        user_id=user.id,
        school_id=user.school_id,
        role=user.role,
        expires_at=expires_at,
    )
    await session_repo.create_session(session_record)

    csrf_token = generate_csrf_token()
    _set_auth_cookies(response, token, csrf_token)

    school = await identity_repo.get_school_by_id(user.school_id)
    school_name = school.name if school else "Sekolah TALENTRA"

    audit_logger.log(
        event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
        safe_context=f"Demo login successful for role {user.role.value}",
        user_id=user.id,
        school_id=user.school_id,
        correlation_id=req_id,
    )

    return LoginResponse(
        user=UserResponse(
            id=user.id,
            displayName=user.display_name,
            role=user.role,
            email=user.email,
            school=SchoolBrief(id=user.school_id, name=school_name),
            maskedIdentifier=user.masked_identifier,
            className=user.class_name,
            title=user.title,
        ),
        redirectTo=_get_canonical_redirect(user.role),
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    auth_ctx: AuthContext = Depends(require_authenticated_user),
):
    """Returns the authenticated user profile and school context."""
    user = auth_ctx.user
    school = auth_ctx.school
    return UserResponse(
        id=user.id,
        displayName=user.display_name,
        role=user.role,
        email=user.email,
        school=SchoolBrief(id=school.id, name=school.name),
        maskedIdentifier=user.masked_identifier,
        className=user.class_name,
        title=user.title,
        requiresCredentialUpdate=getattr(user, "must_change_password", False),
    )

@router.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    auth_ctx: AuthContext = Depends(require_authenticated_user),
    session_repo: SessionRepository = Depends(get_session_repo),
    _csrf: None = Depends(verify_csrf_token),
):
    """Revokes session record in registry and deletes cookies."""
    req_id = str(uuid.uuid4())
    await session_repo.revoke_session(auth_ctx.session.session_id)
    _clear_auth_cookies(response)

    audit_logger.log(
        event_type=AuditEventType.AUTH_LOGOUT,
        safe_context="User successfully logged out",
        user_id=auth_ctx.user_id,
        school_id=auth_ctx.school_id,
        correlation_id=req_id,
    )

    return LogoutResponse(success=True, message="Sesi berhasil diakhiri.")

@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    payload: ChangePasswordRequest,
    auth_ctx: AuthContext = Depends(require_authenticated_user),
    identity_repo: IdentityRepository = Depends(get_identity_repo),
    session_repo: SessionRepository = Depends(get_session_repo),
    _csrf: None = Depends(verify_csrf_token),
):
    """Verifies current password, updates Argon2id hash, and revokes other sessions."""
    req_id = str(uuid.uuid4())
    # 1. Verify current password
    user = auth_ctx.user
    is_valid_current = await identity_repo.verify_user_password(user.id, payload.currentPassword)
    if not is_valid_current:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "AUTH_INVALID_CREDENTIALS",
                "message": "Kata sandi saat ini tidak sesuai.",
                "requestId": req_id,
            },
        )

    # 2. Update Argon2id password hash (and clear must_change_password)
    new_hash = hash_password(payload.newPassword)
    await identity_repo.update_password_hash(user.id, new_hash, must_change_password=False)
    
    # 3. Revoke all other sessions for security (current session remains active)
    await session_repo.revoke_all_user_sessions(user.id, except_session_id=auth_ctx.session.session_id)

    # 4. Audit password change event
    audit_logger.log(
        event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
        safe_context="User password updated; active sessions revoked",
        user_id=user.id,
        school_id=user.school_id,
        correlation_id=req_id,
    )

    return ChangePasswordResponse(
        success=True,
        message="Kata sandi berhasil diperbarui. Sesi perangkat lain telah dinonaktifkan.",
    )
