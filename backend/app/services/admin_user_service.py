import secrets
import uuid
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status

from ..core.security import hash_password
from ..core.audit import audit_logger
from ..domain.enums import AuditEventType
from ..domain.normalizers import normalize_login_identifier
from ..repositories.admin_user import AdminUserRepository
from ..repositories.base import SessionRepository


class AdminUserService:
    def __init__(
        self,
        admin_user_repo: Optional[AdminUserRepository] = None,
        session_repo: Optional[SessionRepository] = None,
    ):
        self.user_repo = admin_user_repo or AdminUserRepository()
        self.session_repo = session_repo

    def _generate_temporary_password(self) -> str:
        """Generates cryptographically random temporary password."""
        return secrets.token_urlsafe(12)

    async def create_student(
        self,
        admin_user_id: str,
        school_id: str,
        display_name: str,
        nisn: str,
        grade_level: str,
        class_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates student with server-generated temporary password and HMAC identity lookup.
        Returns temporary password ONCE.
        """
        req_id = str(uuid.uuid4())
        # 1. Normalize NISN (preserves leading zero, checks length)
        try:
            norm_res = normalize_login_identifier(nisn)
            normalized_nisn = norm_res.normalized
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "VALIDATION_ERROR", "message": str(e), "requestId": req_id},
            )

        if len(normalized_nisn) != 10 or not normalized_nisn.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "VALIDATION_ERROR", "message": "NISN harus tepat 10 digit angka.", "requestId": req_id},
            )

        # 2. Generate temporary password & Argon2id hash
        temp_pwd = self._generate_temporary_password()
        pwd_hash = hash_password(temp_pwd)

        # 3. Create student in repository
        try:
            result = await self.user_repo.create_student(
                school_id=school_id,
                display_name=display_name.strip(),
                normalized_nisn=normalized_nisn,
                grade_level=str(grade_level),
                password_hash=pwd_hash,
                class_id=class_id,
            )
        except ValueError as e:
            if str(e) == "IDENTITY_ALREADY_EXISTS":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "IDENTITY_ALREADY_EXISTS", "message": "Identitas NISN sudah terdaftar di sistem.", "requestId": req_id},
                )
            if str(e) == "CLASS_NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "CLASS_NOT_FOUND", "message": "Kelas rombel tidak ditemukan pada sekolah ini.", "requestId": req_id},
                )
            raise

        # 4. Audit event (NEVER log password or full NISN!)
        audit_logger.log(
            event_type=AuditEventType.ADMIN_USER_CREATED,
            safe_context="Student account created by school admin",
            user_id=admin_user_id,
            school_id=school_id,
            correlation_id=req_id,
            metadata={"created_user_id": result["id"], "role": "student"},
        )

        # 5. Return user object plus one-time temporary password
        response_data = dict(result)
        response_data["temporaryPassword"] = temp_pwd
        return response_data

    async def create_teacher(
        self,
        admin_user_id: str,
        school_id: str,
        display_name: str,
        identifier: str,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates teacher with server-resolved identifier type (NUPTK / NIP).
        Returns temporary password ONCE.
        """
        req_id = str(uuid.uuid4())
        # 1. Normalize identifier
        try:
            norm_res = normalize_login_identifier(identifier)
            normalized_ident = norm_res.normalized
            ident_type = norm_res.identifier_type.value
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "VALIDATION_ERROR", "message": str(e), "requestId": req_id},
            )

        if ident_type not in ("NUPTK", "NIP"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "VALIDATION_ERROR",
                    "message": "Identitas pendidik harus berupa NUPTK (16 digit) atau NIP (18 digit).",
                    "requestId": req_id,
                },
            )

        # 2. Generate temporary password & Argon2id hash
        temp_pwd = self._generate_temporary_password()
        pwd_hash = hash_password(temp_pwd)

        # 3. Create teacher in repository
        try:
            result = await self.user_repo.create_teacher(
                school_id=school_id,
                display_name=display_name.strip(),
                normalized_ident=normalized_ident,
                ident_type=ident_type,
                password_hash=pwd_hash,
                title=title.strip() if title else None,
            )
        except ValueError as e:
            if str(e) == "IDENTITY_ALREADY_EXISTS":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "IDENTITY_ALREADY_EXISTS", "message": f"Identitas {ident_type} sudah terdaftar di sistem.", "requestId": req_id},
                )
            raise

        # 4. Audit event
        audit_logger.log(
            event_type=AuditEventType.ADMIN_USER_CREATED,
            safe_context=f"Teacher account ({ident_type}) created by school admin",
            user_id=admin_user_id,
            school_id=school_id,
            correlation_id=req_id,
            metadata={"created_user_id": result["id"], "role": "teacher"},
        )

        response_data = dict(result)
        response_data["temporaryPassword"] = temp_pwd
        return response_data

    async def get_user(self, school_id: str, user_id: str) -> Dict[str, Any]:
        req_id = str(uuid.uuid4())
        detail = await self.user_repo.get_user_detail(school_id, user_id)
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ADMIN_USER_NOT_FOUND", "message": "Pengguna tidak ditemukan pada sekolah ini.", "requestId": req_id},
            )
        return detail

    async def update_user(
        self,
        admin_user_id: str,
        school_id: str,
        user_id: str,
        display_name: Optional[str] = None,
        grade_level: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Safe profile updates for display name, grade level, or title."""
        req_id = str(uuid.uuid4())
        updated = await self.user_repo.update_user_profile(
            school_id=school_id,
            user_id=user_id,
            display_name=display_name.strip() if display_name else None,
            grade_level=str(grade_level) if grade_level is not None else None,
            title=title.strip() if title else None,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ADMIN_USER_NOT_FOUND", "message": "Pengguna tidak ditemukan pada sekolah ini.", "requestId": req_id},
            )

        audit_logger.log(
            event_type=AuditEventType.ADMIN_USER_UPDATED,
            safe_context="User profile updated by admin",
            user_id=admin_user_id,
            school_id=school_id,
            correlation_id=req_id,
            metadata={"target_user_id": user_id},
        )
        return updated

    async def disable_user(
        self,
        admin_user_id: str,
        school_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Disables account and immediately revokes all active sessions.
        Historical portfolio and validation decisions remain preserved.
        """
        req_id = str(uuid.uuid4())
        success = await self.user_repo.set_user_status(school_id, user_id, "disabled")
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ADMIN_USER_NOT_FOUND", "message": "Pengguna tidak ditemukan pada sekolah ini.", "requestId": req_id},
            )

        # Revoke all active sessions
        if self.session_repo:
            await self.session_repo.revoke_all_user_sessions(user_id)

        audit_logger.log(
            event_type=AuditEventType.ADMIN_USER_DISABLED,
            safe_context="User disabled by admin; active sessions revoked",
            user_id=admin_user_id,
            school_id=school_id,
            correlation_id=req_id,
            metadata={"target_user_id": user_id},
        )
        return {"success": True, "message": "Akun pengguna berhasil dinonaktifkan."}

    async def reactivate_user(
        self,
        admin_user_id: str,
        school_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Reactivates account. Does not restore old sessions. User must login again.
        """
        req_id = str(uuid.uuid4())
        success = await self.user_repo.set_user_status(school_id, user_id, "active")
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ADMIN_USER_NOT_FOUND", "message": "Pengguna tidak ditemukan pada sekolah ini.", "requestId": req_id},
            )

        audit_logger.log(
            event_type=AuditEventType.ADMIN_USER_REACTIVATED,
            safe_context="User reactivated by admin",
            user_id=admin_user_id,
            school_id=school_id,
            correlation_id=req_id,
            metadata={"target_user_id": user_id},
        )
        return {"success": True, "message": "Akun pengguna berhasil diaktifkan kembali."}

    async def reset_password(
        self,
        admin_user_id: str,
        school_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Generates new random temporary password, sets must_change_password=True,
        revokes all active sessions, audits event, and returns temporary password ONCE.
        """
        req_id = str(uuid.uuid4())
        temp_pwd = self._generate_temporary_password()
        new_hash = hash_password(temp_pwd)

        success = await self.user_repo.reset_password(school_id, user_id, new_hash)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ADMIN_USER_NOT_FOUND", "message": "Pengguna tidak ditemukan pada sekolah ini.", "requestId": req_id},
            )

        # Revoke all active sessions
        if self.session_repo:
            await self.session_repo.revoke_all_user_sessions(user_id)

        # Audit event (never log password!)
        audit_logger.log(
            event_type=AuditEventType.ADMIN_PASSWORD_RESET,
            safe_context="User password reset by admin; active sessions revoked",
            user_id=admin_user_id,
            school_id=school_id,
            correlation_id=req_id,
            metadata={"target_user_id": user_id},
        )

        return {
            "success": True,
            "temporaryPassword": temp_pwd,
            "message": "Kata sandi sementara berhasil dibuat. Pengguna wajib menggantinya saat login berikutnya.",
        }

    async def list_users(
        self,
        school_id: str,
        role: Optional[str] = None,
        status: Optional[str] = None,
        class_id: Optional[str] = None,
        grade_level: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        return await self.user_repo.list_users(
            school_id=school_id,
            role=role,
            status=status,
            class_id=class_id,
            grade_level=grade_level,
            search=search,
            limit=limit,
            offset=offset,
        )
