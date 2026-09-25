import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, update, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..core.database import AsyncSessionLocal
from ..core.security import compute_identifier_lookup_hash
from ..db.models import (
    UserModel,
    AuthIdentityModel,
    StudentProfileModel,
    TeacherProfileModel,
    ClassModel,
    EnrollmentModel,
)


class AdminUserRepository:
    def __init__(self, session_factory: Optional[async_sessionmaker[AsyncSession]] = None):
        self.session_factory = session_factory or AsyncSessionLocal

    async def check_identity_exists(self, identifier_type: str, normalized_identifier: str) -> bool:
        lookup_hash = compute_identifier_lookup_hash(normalized_identifier)
        ident_types = [identifier_type.lower(), identifier_type.upper()]
        async with self.session_factory() as session:
            stmt = select(AuthIdentityModel.id).where(
                and_(
                    AuthIdentityModel.identifier_type.in_(ident_types),
                    AuthIdentityModel.identifier_lookup_hash == lookup_hash,
                )
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none() is not None

    async def create_student(
        self,
        school_id: str,
        display_name: str,
        normalized_nisn: str,
        grade_level: str,
        password_hash: str,
        class_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates student account inside school tenant.
        NISN is keyed-HMAC hashed, internal UUID assigned, leading zeros preserved.
        """
        lookup_hash = compute_identifier_lookup_hash(normalized_nisn)
        last4 = normalized_nisn[-4:]

        async with self.session_factory() as session:
            # Check duplicate identity
            stmt_dup = select(AuthIdentityModel.id).where(
                and_(
                    AuthIdentityModel.identifier_type.in_(["nisn", "NISN"]),
                    AuthIdentityModel.identifier_lookup_hash == lookup_hash,
                )
            )
            res_dup = await session.execute(stmt_dup)
            if res_dup.scalar_one_or_none():
                raise ValueError("IDENTITY_ALREADY_EXISTS")

            class_name = None
            class_academic_year = None
            if class_id:
                stmt_cls = select(ClassModel).where(
                    and_(ClassModel.id == class_id, ClassModel.school_id == school_id)
                )
                res_cls = await session.execute(stmt_cls)
                cls_model = res_cls.scalar_one_or_none()
                if not cls_model:
                    raise ValueError("CLASS_NOT_FOUND")
                class_name = cls_model.name
                class_academic_year = cls_model.academic_year

            user_id = str(uuid.uuid4())
            user = UserModel(
                id=user_id,
                school_id=school_id,
                role="student",
                status="active",
                display_name=display_name,
                email=f"{user_id}@student.talentra.id",
            )
            session.add(user)

            identity = AuthIdentityModel(
                id=str(uuid.uuid4()),
                user_id=user_id,
                identifier_type="NISN",
                identifier_lookup_hash=lookup_hash,
                identifier_last4=last4,
                password_hash=password_hash,
                active=True,
                must_change_password=True,
            )
            session.add(identity)

            student_profile = StudentProfileModel(
                user_id=user_id,
                grade_level=str(grade_level),
                class_name=class_name,
            )
            session.add(student_profile)

            if class_id and class_academic_year:
                enrollment = EnrollmentModel(
                    id=str(uuid.uuid4()),
                    school_id=school_id,
                    class_id=class_id,
                    student_id=user_id,
                    academic_year=class_academic_year,
                    status="active",
                )
                session.add(enrollment)

            await session.commit()

            return {
                "id": user_id,
                "schoolId": school_id,
                "role": "student",
                "status": "active",
                "displayName": display_name,
                "email": user.email,
                "maskedIdentifier": f"NISN: ••••••{last4}",
                "gradeLevel": str(grade_level),
                "className": class_name,
                "classId": class_id,
                "mustChangePassword": True,
            }

    async def create_teacher(
        self,
        school_id: str,
        display_name: str,
        normalized_ident: str,
        ident_type: str,  # NUPTK or NIP
        password_hash: str,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates teacher account inside school tenant."""
        lookup_hash = compute_identifier_lookup_hash(normalized_ident)
        last4 = normalized_ident[-4:]
        type_upper = ident_type.upper()

        async with self.session_factory() as session:
            stmt_dup = select(AuthIdentityModel.id).where(
                and_(
                    AuthIdentityModel.identifier_type.in_([type_upper, type_upper.lower()]),
                    AuthIdentityModel.identifier_lookup_hash == lookup_hash,
                )
            )
            res_dup = await session.execute(stmt_dup)
            if res_dup.scalar_one_or_none():
                raise ValueError("IDENTITY_ALREADY_EXISTS")

            user_id = str(uuid.uuid4())
            user = UserModel(
                id=user_id,
                school_id=school_id,
                role="teacher",
                status="active",
                display_name=display_name,
                email=f"{user_id}@guru.talentra.id",
            )
            session.add(user)

            identity = AuthIdentityModel(
                id=str(uuid.uuid4()),
                user_id=user_id,
                identifier_type=type_upper,
                identifier_lookup_hash=lookup_hash,
                identifier_last4=last4,
                password_hash=password_hash,
                active=True,
                must_change_password=True,
            )
            session.add(identity)

            teacher_profile = TeacherProfileModel(
                user_id=user_id,
                display_title=title,
            )
            session.add(teacher_profile)

            await session.commit()

            mask_prefix = "••••••••••••" if type_upper == "NUPTK" else "••••••••••••••"
            return {
                "id": user_id,
                "schoolId": school_id,
                "role": "teacher",
                "status": "active",
                "displayName": display_name,
                "email": user.email,
                "maskedIdentifier": f"{type_upper}: {mask_prefix}{last4}",
                "title": title,
                "mustChangePassword": True,
            }

    async def get_user_detail(self, school_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Tenant-scoped user detail retrieval with masked identifier."""
        async with self.session_factory() as session:
            stmt = select(UserModel).where(
                and_(UserModel.id == user_id, UserModel.school_id == school_id)
            )
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            if not user:
                return None

            # Retrieve identity for masked ID
            stmt_id = select(AuthIdentityModel).where(AuthIdentityModel.user_id == user_id)
            res_id = await session.execute(stmt_id)
            ident = res_id.scalars().first()

            masked_id = "ID: ••••••" + user.id[-4:]
            must_change = False
            if ident:
                type_upper = ident.identifier_type.upper()
                last4 = ident.identifier_last4
                mask_dots = "••••••" if type_upper == "NISN" else ("••••••••••••" if type_upper == "NUPTK" else "••••••••••••••")
                masked_id = f"{type_upper}: {mask_dots}{last4}"
                must_change = bool(ident.must_change_password)

            class_name = None
            grade_level = None
            title = None
            if user.role == "student":
                stmt_sp = select(StudentProfileModel).where(StudentProfileModel.user_id == user_id)
                res_sp = await session.execute(stmt_sp)
                sp = res_sp.scalar_one_or_none()
                if sp:
                    class_name = sp.class_name
                    grade_level = sp.grade_level
            elif user.role in ("teacher", "admin"):
                stmt_tp = select(TeacherProfileModel).where(TeacherProfileModel.user_id == user_id)
                res_tp = await session.execute(stmt_tp)
                tp = res_tp.scalar_one_or_none()
                if tp:
                    title = tp.display_title

            return {
                "id": user.id,
                "schoolId": user.school_id,
                "role": user.role,
                "status": user.status,
                "displayName": user.display_name,
                "email": user.email,
                "maskedIdentifier": masked_id,
                "className": class_name,
                "gradeLevel": grade_level,
                "title": title,
                "mustChangePassword": must_change,
                "createdAt": user.created_at.isoformat() if user.created_at else None,
            }

    async def update_user_profile(
        self,
        school_id: str,
        user_id: str,
        display_name: Optional[str] = None,
        grade_level: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Safe profile updates. Cannot modify role, school_id, password_hash or identifiers."""
        async with self.session_factory() as session:
            stmt = select(UserModel).where(
                and_(UserModel.id == user_id, UserModel.school_id == school_id)
            )
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            if not user:
                return None

            if display_name:
                user.display_name = display_name
                user.updated_at = datetime.now(timezone.utc)

            if user.role == "student" and grade_level is not None:
                stmt_sp = select(StudentProfileModel).where(StudentProfileModel.user_id == user_id)
                res_sp = await session.execute(stmt_sp)
                sp = res_sp.scalar_one_or_none()
                if sp:
                    sp.grade_level = str(grade_level)
                    sp.updated_at = datetime.now(timezone.utc)

            if user.role in ("teacher", "admin") and title is not None:
                stmt_tp = select(TeacherProfileModel).where(TeacherProfileModel.user_id == user_id)
                res_tp = await session.execute(stmt_tp)
                tp = res_tp.scalar_one_or_none()
                if tp:
                    tp.display_title = title
                    tp.updated_at = datetime.now(timezone.utc)

            await session.commit()

        return await self.get_user_detail(school_id, user_id)

    async def set_user_status(self, school_id: str, user_id: str, status: str) -> bool:
        """Sets status to active or disabled. Also updates AuthIdentity active flag."""
        async with self.session_factory() as session:
            stmt = select(UserModel).where(
                and_(UserModel.id == user_id, UserModel.school_id == school_id)
            )
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            if not user:
                return False

            user.status = status
            user.updated_at = datetime.now(timezone.utc)

            # Update identity active flag
            stmt_id = (
                update(AuthIdentityModel)
                .where(AuthIdentityModel.user_id == user_id)
                .values(active=(status == "active"), updated_at=datetime.now(timezone.utc))
            )
            await session.execute(stmt_id)

            await session.commit()
            return True

    async def reset_password(self, school_id: str, user_id: str, new_hash: str) -> bool:
        """Updates password hash and sets must_change_password=True."""
        async with self.session_factory() as session:
            stmt_user = select(UserModel.id).where(
                and_(UserModel.id == user_id, UserModel.school_id == school_id)
            )
            res_user = await session.execute(stmt_user)
            if not res_user.scalar_one_or_none():
                return False

            stmt = (
                update(AuthIdentityModel)
                .where(AuthIdentityModel.user_id == user_id)
                .values(
                    password_hash=new_hash,
                    must_change_password=True,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            res = await session.execute(stmt)
            await session.commit()
            return res.rowcount > 0

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
        """
        Lists users strictly scoped to school tenant.
        Returns safe summary with masked identifiers only. Never returns password hashes or raw IDs.
        """
        async with self.session_factory() as session:
            conditions = [UserModel.school_id == school_id]

            if role and role != "all":
                conditions.append(UserModel.role == role)
            if status and status != "all":
                conditions.append(UserModel.status == status)
            if search and search.strip():
                term = f"%{search.strip().lower()}%"
                conditions.append(
                    or_(
                        func.lower(UserModel.display_name).like(term),
                        func.lower(UserModel.email).like(term),
                    )
                )

            # If class_id or grade_level filter specified for students
            if class_id and class_id != "all":
                stmt_enroll = select(EnrollmentModel.student_id).where(
                    and_(
                        EnrollmentModel.school_id == school_id,
                        EnrollmentModel.class_id == class_id,
                        EnrollmentModel.status == "active",
                    )
                )
                res_enroll = await session.execute(stmt_enroll)
                enrolled_student_ids = list(res_enroll.scalars().all())
                conditions.append(UserModel.id.in_(enrolled_student_ids))

            # Total count
            stmt_count = select(func.count(UserModel.id)).where(and_(*conditions))
            res_count = await session.execute(stmt_count)
            total = res_count.scalar() or 0

            # Paged query
            stmt_users = (
                select(UserModel)
                .where(and_(*conditions))
                .order_by(UserModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            res_users = await session.execute(stmt_users)
            users = res_users.scalars().all()

            if not users:
                return [], total

            user_ids = [u.id for u in users]

            # Batch fetch identities
            stmt_idents = select(AuthIdentityModel).where(AuthIdentityModel.user_id.in_(user_ids))
            res_idents = await session.execute(stmt_idents)
            ident_map: Dict[str, AuthIdentityModel] = {}
            for ident in res_idents.scalars().all():
                if ident.user_id not in ident_map:
                    ident_map[ident.user_id] = ident

            # Batch fetch student profiles
            stmt_sp = select(StudentProfileModel).where(StudentProfileModel.user_id.in_(user_ids))
            res_sp = await session.execute(stmt_sp)
            sp_map = {p.user_id: p for p in res_sp.scalars().all()}

            # Batch fetch teacher profiles
            stmt_tp = select(TeacherProfileModel).where(TeacherProfileModel.user_id.in_(user_ids))
            res_tp = await session.execute(stmt_tp)
            tp_map = {p.user_id: p for p in res_tp.scalars().all()}

            items: List[Dict[str, Any]] = []
            for u in users:
                ident = ident_map.get(u.id)
                masked_id = "ID: ••••••" + u.id[-4:]
                must_change = False
                if ident:
                    t = ident.identifier_type.upper()
                    l4 = ident.identifier_last4
                    dots = "••••••" if t == "NISN" else ("••••••••••••" if t == "NUPTK" else "••••••••••••••")
                    masked_id = f"{t}: {dots}{l4}"
                    must_change = bool(ident.must_change_password)

                sp = sp_map.get(u.id)
                tp = tp_map.get(u.id)

                items.append({
                    "id": u.id,
                    "schoolId": u.school_id,
                    "role": u.role,
                    "status": u.status,
                    "displayName": u.display_name,
                    "email": u.email,
                    "maskedIdentifier": masked_id,
                    "className": sp.class_name if sp else None,
                    "gradeLevel": sp.grade_level if sp else None,
                    "title": tp.display_title if tp else None,
                    "mustChangePassword": must_change,
                    "createdAt": u.created_at.isoformat() if u.created_at else None,
                })

            return items, total
