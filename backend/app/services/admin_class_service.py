import uuid
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status

from ..core.audit import audit_logger
from ..domain.enums import AuditEventType
from ..repositories.admin_class import AdminClassRepository


class AdminClassService:
    def __init__(self, admin_class_repo: Optional[AdminClassRepository] = None):
        self.class_repo = admin_class_repo or AdminClassRepository()

    async def list_classes(
        self,
        school_id: str,
        academic_year: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return await self.class_repo.list_classes(
            school_id=school_id,
            academic_year=academic_year,
            status=status_filter,
        )

    async def get_class(self, school_id: str, class_id: str) -> Dict[str, Any]:
        req_id = str(uuid.uuid4())
        detail = await self.class_repo.get_class_detail(school_id, class_id)
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CLASS_NOT_FOUND", "message": "Kelas rombel tidak ditemukan pada sekolah ini.", "requestId": req_id},
            )
        return detail

    async def create_class(
        self,
        admin_user_id: str,
        school_id: str,
        name: str,
        grade_level: str,
        academic_year: str,
    ) -> Dict[str, Any]:
        req_id = str(uuid.uuid4())
        cleaned_name = name.strip()
        if not cleaned_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "VALIDATION_ERROR", "message": "Nama rombel wajib diisi.", "requestId": req_id},
            )

        result = await self.class_repo.create_class(
            school_id=school_id,
            name=cleaned_name,
            grade_level=str(grade_level).strip(),
            academic_year=academic_year.strip(),
        )

        audit_logger.log(
            event_type=AuditEventType.ADMIN_CLASS_CREATED,
            safe_context="Class created by admin",
            user_id=admin_user_id,
            school_id=school_id,
            correlation_id=req_id,
            metadata={"class_id": result["id"], "name": cleaned_name},
        )
        return result

    async def update_class(
        self,
        admin_user_id: str,
        school_id: str,
        class_id: str,
        name: Optional[str] = None,
        grade_level: Optional[str] = None,
        academic_year: Optional[str] = None,
    ) -> Dict[str, Any]:
        req_id = str(uuid.uuid4())
        updated = await self.class_repo.update_class(
            school_id=school_id,
            class_id=class_id,
            name=name.strip() if name else None,
            grade_level=str(grade_level).strip() if grade_level is not None else None,
            academic_year=academic_year.strip() if academic_year else None,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CLASS_NOT_FOUND", "message": "Kelas rombel tidak ditemukan pada sekolah ini.", "requestId": req_id},
            )

        audit_logger.log(
            event_type=AuditEventType.ADMIN_CLASS_UPDATED,
            safe_context="Class updated by admin",
            user_id=admin_user_id,
            school_id=school_id,
            correlation_id=req_id,
            metadata={"class_id": class_id},
        )
        return updated

    async def archive_class(
        self,
        admin_user_id: str,
        school_id: str,
        class_id: str,
    ) -> Dict[str, Any]:
        req_id = str(uuid.uuid4())
        success = await self.class_repo.archive_class(school_id, class_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CLASS_NOT_FOUND", "message": "Kelas rombel tidak ditemukan pada sekolah ini.", "requestId": req_id},
            )

        audit_logger.log(
            event_type=AuditEventType.ADMIN_CLASS_ARCHIVED,
            safe_context="Class archived by admin",
            user_id=admin_user_id,
            school_id=school_id,
            correlation_id=req_id,
            metadata={"class_id": class_id},
        )
        return {"success": True, "message": "Kelas rombel berhasil diarsipkan."}

    async def enroll_student(
        self,
        admin_user_id: str,
        school_id: str,
        class_id: str,
        student_id: str,
    ) -> Dict[str, Any]:
        req_id = str(uuid.uuid4())
        try:
            await self.class_repo.enroll_student(school_id, class_id, student_id)
        except ValueError as e:
            if str(e) == "CLASS_NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "CLASS_NOT_FOUND", "message": "Kelas rombel tidak ditemukan pada sekolah ini.", "requestId": req_id},
                )
            if str(e) == "STUDENT_NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "ADMIN_USER_NOT_FOUND", "message": "Siswa tidak ditemukan atau bukan siswa aktif pada sekolah ini.", "requestId": req_id},
                )
            raise

        audit_logger.log(
            event_type=AuditEventType.ADMIN_ENROLLMENT_CHANGED,
            safe_context="Student enrolled into class",
            user_id=admin_user_id,
            school_id=school_id,
            correlation_id=req_id,
            metadata={"class_id": class_id, "student_id": student_id, "action": "enrolled"},
        )
        return {"success": True, "message": "Siswa berhasil didaftarkan ke dalam rombel."}

    async def unenroll_student(
        self,
        admin_user_id: str,
        school_id: str,
        class_id: str,
        student_id: str,
    ) -> Dict[str, Any]:
        req_id = str(uuid.uuid4())
        success = await self.class_repo.unenroll_student(school_id, class_id, student_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ENROLLMENT_NOT_FOUND", "message": "Pendaftaran siswa pada rombel ini tidak ditemukan.", "requestId": req_id},
            )

        audit_logger.log(
            event_type=AuditEventType.ADMIN_ENROLLMENT_CHANGED,
            safe_context="Student removed from class enrollment",
            user_id=admin_user_id,
            school_id=school_id,
            correlation_id=req_id,
            metadata={"class_id": class_id, "student_id": student_id, "action": "unenrolled"},
        )
        return {"success": True, "message": "Siswa berhasil dikeluarkan dari rombel."}

    async def assign_teacher(
        self,
        admin_user_id: str,
        school_id: str,
        class_id: str,
        teacher_id: str,
        assignment_type: str = "portfolio_validator",
    ) -> Dict[str, Any]:
        req_id = str(uuid.uuid4())
        try:
            await self.class_repo.assign_teacher(school_id, class_id, teacher_id, assignment_type)
        except ValueError as e:
            if str(e) == "CLASS_NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "CLASS_NOT_FOUND", "message": "Kelas rombel tidak ditemukan pada sekolah ini.", "requestId": req_id},
                )
            if str(e) == "TEACHER_NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "ADMIN_USER_NOT_FOUND", "message": "Pendidik tidak ditemukan atau bukan pendidik aktif pada sekolah ini.", "requestId": req_id},
                )
            raise

        audit_logger.log(
            event_type=AuditEventType.ADMIN_TEACHER_ASSIGNMENT_CHANGED,
            safe_context="Teacher assigned to class",
            user_id=admin_user_id,
            school_id=school_id,
            correlation_id=req_id,
            metadata={"class_id": class_id, "teacher_id": teacher_id, "action": "assigned"},
        )
        return {"success": True, "message": "Guru berhasil ditugaskan pada rombel."}

    async def remove_teacher_assignment(
        self,
        admin_user_id: str,
        school_id: str,
        class_id: str,
        teacher_id: str,
    ) -> Dict[str, Any]:
        req_id = str(uuid.uuid4())
        success = await self.class_repo.remove_teacher_assignment(school_id, class_id, teacher_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "TEACHER_ASSIGNMENT_NOT_FOUND", "message": "Penugasan guru pada rombel ini tidak ditemukan.", "requestId": req_id},
            )

        audit_logger.log(
            event_type=AuditEventType.ADMIN_TEACHER_ASSIGNMENT_CHANGED,
            safe_context="Teacher removed from class assignment",
            user_id=admin_user_id,
            school_id=school_id,
            correlation_id=req_id,
            metadata={"class_id": class_id, "teacher_id": teacher_id, "action": "removed"},
        )
        return {"success": True, "message": "Penugasan guru pada rombel berhasil dihentikan."}
