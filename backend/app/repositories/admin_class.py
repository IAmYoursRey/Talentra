import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..core.database import AsyncSessionLocal
from ..db.models import (
    ClassModel,
    EnrollmentModel,
    TeacherAssignmentModel,
    UserModel,
    StudentProfileModel,
    TeacherProfileModel,
    AuthIdentityModel,
)


class AdminClassRepository:
    def __init__(self, session_factory: Optional[async_sessionmaker[AsyncSession]] = None):
        self.session_factory = session_factory or AsyncSessionLocal

    async def list_classes(
        self,
        school_id: str,
        academic_year: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Lists classes with student counts and validator counts."""
        async with self.session_factory() as session:
            conditions = [ClassModel.school_id == school_id]
            if academic_year and academic_year != "all":
                conditions.append(ClassModel.academic_year == academic_year)
            if status and status != "all":
                conditions.append(ClassModel.status == status)

            stmt = select(ClassModel).where(and_(*conditions)).order_by(ClassModel.grade_level, ClassModel.name)
            res = await session.execute(stmt)
            classes = res.scalars().all()

            if not classes:
                return []

            class_ids = [c.id for c in classes]

            # Aggregate active student counts
            stmt_students = (
                select(EnrollmentModel.class_id, func.count(EnrollmentModel.student_id))
                .where(
                    and_(
                        EnrollmentModel.school_id == school_id,
                        EnrollmentModel.class_id.in_(class_ids),
                        EnrollmentModel.status == "active",
                    )
                )
                .group_by(EnrollmentModel.class_id)
            )
            res_students = await session.execute(stmt_students)
            student_count_map = dict(res_students.all())

            # Aggregate active teacher counts
            stmt_teachers = (
                select(TeacherAssignmentModel.class_id, func.count(TeacherAssignmentModel.teacher_id))
                .where(
                    and_(
                        TeacherAssignmentModel.school_id == school_id,
                        TeacherAssignmentModel.class_id.in_(class_ids),
                        TeacherAssignmentModel.active.is_(True),
                    )
                )
                .group_by(TeacherAssignmentModel.class_id)
            )
            res_teachers = await session.execute(stmt_teachers)
            teacher_count_map = dict(res_teachers.all())

            results: List[Dict[str, Any]] = []
            for c in classes:
                results.append({
                    "id": c.id,
                    "schoolId": c.school_id,
                    "name": c.name,
                    "gradeLevel": c.grade_level,
                    "academicYear": c.academic_year,
                    "status": c.status,
                    "studentsCount": student_count_map.get(c.id, 0),
                    "validatorsCount": teacher_count_map.get(c.id, 0),
                    "createdAt": c.created_at.isoformat() if c.created_at else None,
                })
            return results

    async def get_class_detail(self, school_id: str, class_id: str) -> Optional[Dict[str, Any]]:
        """Returns class details with enrolled students and assigned teachers."""
        async with self.session_factory() as session:
            stmt = select(ClassModel).where(
                and_(ClassModel.id == class_id, ClassModel.school_id == school_id)
            )
            res = await session.execute(stmt)
            cls_obj = res.scalar_one_or_none()
            if not cls_obj:
                return None

            # Enrolled students
            stmt_students = (
                select(
                    UserModel.id,
                    UserModel.display_name,
                    UserModel.status,
                    StudentProfileModel.grade_level,
                    AuthIdentityModel.identifier_last4,
                )
                .join(EnrollmentModel, EnrollmentModel.student_id == UserModel.id)
                .outerjoin(StudentProfileModel, StudentProfileModel.user_id == UserModel.id)
                .outerjoin(AuthIdentityModel, AuthIdentityModel.user_id == UserModel.id)
                .where(
                    and_(
                        EnrollmentModel.school_id == school_id,
                        EnrollmentModel.class_id == class_id,
                        EnrollmentModel.status == "active",
                    )
                )
            )
            res_std = await session.execute(stmt_students)
            students = []
            for row in res_std.all():
                l4 = row.identifier_last4 or row.id[-4:]
                students.append({
                    "id": row.id,
                    "displayName": row.display_name,
                    "status": row.status,
                    "gradeLevel": row.grade_level,
                    "maskedIdentifier": f"NISN: ••••••{l4}",
                })

            # Assigned teachers
            stmt_teachers = (
                select(
                    UserModel.id,
                    UserModel.display_name,
                    TeacherProfileModel.display_title,
                    TeacherAssignmentModel.assignment_type,
                )
                .join(TeacherAssignmentModel, TeacherAssignmentModel.teacher_id == UserModel.id)
                .outerjoin(TeacherProfileModel, TeacherProfileModel.user_id == UserModel.id)
                .where(
                    and_(
                        TeacherAssignmentModel.school_id == school_id,
                        TeacherAssignmentModel.class_id == class_id,
                        TeacherAssignmentModel.active.is_(True),
                    )
                )
            )
            res_tch = await session.execute(stmt_teachers)
            teachers = []
            for row in res_tch.all():
                teachers.append({
                    "id": row.id,
                    "displayName": row.display_name,
                    "title": row.display_title,
                    "assignmentType": row.assignment_type,
                })

            return {
                "id": cls_obj.id,
                "schoolId": cls_obj.school_id,
                "name": cls_obj.name,
                "gradeLevel": cls_obj.grade_level,
                "academicYear": cls_obj.academic_year,
                "status": cls_obj.status,
                "students": students,
                "teachers": teachers,
                "studentsCount": len(students),
                "validatorsCount": len(teachers),
            }

    async def create_class(
        self,
        school_id: str,
        name: str,
        grade_level: str,
        academic_year: str,
    ) -> Dict[str, Any]:
        """Creates a class record scoped to school tenant."""
        async with self.session_factory() as session:
            class_id = str(uuid.uuid4())
            cls_obj = ClassModel(
                id=class_id,
                school_id=school_id,
                name=name,
                grade_level=str(grade_level),
                academic_year=academic_year,
                status="active",
            )
            session.add(cls_obj)
            await session.commit()

            return {
                "id": class_id,
                "schoolId": school_id,
                "name": name,
                "gradeLevel": str(grade_level),
                "academicYear": academic_year,
                "status": "active",
                "studentsCount": 0,
                "validatorsCount": 0,
            }

    async def update_class(
        self,
        school_id: str,
        class_id: str,
        name: Optional[str] = None,
        grade_level: Optional[str] = None,
        academic_year: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Updates class details."""
        async with self.session_factory() as session:
            stmt = select(ClassModel).where(
                and_(ClassModel.id == class_id, ClassModel.school_id == school_id)
            )
            res = await session.execute(stmt)
            cls_obj = res.scalar_one_or_none()
            if not cls_obj:
                return None

            if name:
                cls_obj.name = name
            if grade_level is not None:
                cls_obj.grade_level = str(grade_level)
            if academic_year:
                cls_obj.academic_year = academic_year
            cls_obj.updated_at = datetime.now(timezone.utc)

            await session.commit()

            return {
                "id": cls_obj.id,
                "schoolId": cls_obj.school_id,
                "name": cls_obj.name,
                "gradeLevel": cls_obj.grade_level,
                "academicYear": cls_obj.academic_year,
                "status": cls_obj.status,
            }

    async def archive_class(self, school_id: str, class_id: str) -> bool:
        """Archives class without hard-deleting historical records."""
        async with self.session_factory() as session:
            stmt = select(ClassModel).where(
                and_(ClassModel.id == class_id, ClassModel.school_id == school_id)
            )
            res = await session.execute(stmt)
            cls_obj = res.scalar_one_or_none()
            if not cls_obj:
                return False

            cls_obj.status = "archived"
            cls_obj.updated_at = datetime.now(timezone.utc)
            await session.commit()
            return True

    async def enroll_student(self, school_id: str, class_id: str, student_id: str) -> bool:
        """
        Enrolls student in class.
        Preserves historical enrollment records across academic years.
        """
        async with self.session_factory() as session:
            # 1. Verify class belongs to same school
            stmt_cls = select(ClassModel).where(
                and_(ClassModel.id == class_id, ClassModel.school_id == school_id)
            )
            res_cls = await session.execute(stmt_cls)
            cls_obj = res_cls.scalar_one_or_none()
            if not cls_obj:
                raise ValueError("CLASS_NOT_FOUND")

            # 2. Verify student belongs to same school and role == student
            stmt_std = select(UserModel).where(
                and_(
                    UserModel.id == student_id,
                    UserModel.school_id == school_id,
                    UserModel.role == "student",
                )
            )
            res_std = await session.execute(stmt_std)
            student = res_std.scalar_one_or_none()
            if not student:
                raise ValueError("STUDENT_NOT_FOUND")

            # 3. Check existing enrollment in this class & academic year
            stmt_enr = select(EnrollmentModel).where(
                and_(
                    EnrollmentModel.school_id == school_id,
                    EnrollmentModel.class_id == class_id,
                    EnrollmentModel.student_id == student_id,
                    EnrollmentModel.academic_year == cls_obj.academic_year,
                )
            )
            res_enr = await session.execute(stmt_enr)
            existing_enr = res_enr.scalar_one_or_none()

            if existing_enr:
                existing_enr.status = "active"
            else:
                new_enr = EnrollmentModel(
                    id=str(uuid.uuid4()),
                    school_id=school_id,
                    class_id=class_id,
                    student_id=student_id,
                    academic_year=cls_obj.academic_year,
                    status="active",
                )
                session.add(new_enr)

            # Update student profile class_name
            stmt_sp = select(StudentProfileModel).where(StudentProfileModel.user_id == student_id)
            res_sp = await session.execute(stmt_sp)
            sp = res_sp.scalar_one_or_none()
            if sp:
                sp.class_name = cls_obj.name
                sp.updated_at = datetime.now(timezone.utc)

            await session.commit()
            return True

    async def unenroll_student(self, school_id: str, class_id: str, student_id: str) -> bool:
        """
        Deactivates enrollment without hard-deleting historical records.
        """
        async with self.session_factory() as session:
            stmt = select(EnrollmentModel).where(
                and_(
                    EnrollmentModel.school_id == school_id,
                    EnrollmentModel.class_id == class_id,
                    EnrollmentModel.student_id == student_id,
                    EnrollmentModel.status == "active",
                )
            )
            res = await session.execute(stmt)
            enr = res.scalar_one_or_none()
            if not enr:
                return False

            enr.status = "inactive"

            # Clear profile class_name if matched
            stmt_cls = select(ClassModel.name).where(ClassModel.id == class_id)
            res_cls = await session.execute(stmt_cls)
            cls_name = res_cls.scalar_one_or_none()

            stmt_sp = select(StudentProfileModel).where(StudentProfileModel.user_id == student_id)
            res_sp = await session.execute(stmt_sp)
            sp = res_sp.scalar_one_or_none()
            if sp and cls_name and sp.class_name == cls_name:
                sp.class_name = None
                sp.updated_at = datetime.now(timezone.utc)

            await session.commit()
            return True

    async def assign_teacher(
        self,
        school_id: str,
        class_id: str,
        teacher_id: str,
        assignment_type: str = "portfolio_validator",
    ) -> bool:
        """
        Assigns teacher to class.
        Controls future validator authorization.
        """
        async with self.session_factory() as session:
            # 1. Verify class belongs to school
            stmt_cls = select(ClassModel).where(
                and_(ClassModel.id == class_id, ClassModel.school_id == school_id)
            )
            res_cls = await session.execute(stmt_cls)
            if not res_cls.scalar_one_or_none():
                raise ValueError("CLASS_NOT_FOUND")

            # 2. Verify teacher belongs to school and is active teacher
            stmt_tch = select(UserModel).where(
                and_(
                    UserModel.id == teacher_id,
                    UserModel.school_id == school_id,
                    UserModel.role == "teacher",
                    UserModel.status == "active",
                )
            )
            res_tch = await session.execute(stmt_tch)
            if not res_tch.scalar_one_or_none():
                raise ValueError("TEACHER_NOT_FOUND")

            # 3. Check existing assignment
            stmt_asg = select(TeacherAssignmentModel).where(
                and_(
                    TeacherAssignmentModel.school_id == school_id,
                    TeacherAssignmentModel.class_id == class_id,
                    TeacherAssignmentModel.teacher_id == teacher_id,
                )
            )
            res_asg = await session.execute(stmt_asg)
            existing_asg = res_asg.scalar_one_or_none()

            if existing_asg:
                existing_asg.active = True
                existing_asg.assignment_type = assignment_type
            else:
                new_asg = TeacherAssignmentModel(
                    id=str(uuid.uuid4()),
                    school_id=school_id,
                    class_id=class_id,
                    teacher_id=teacher_id,
                    assignment_type=assignment_type,
                    active=True,
                )
                session.add(new_asg)

            await session.commit()
            return True

    async def remove_teacher_assignment(self, school_id: str, class_id: str, teacher_id: str) -> bool:
        """
        Deactivates teacher assignment (active = False).
        Teacher immediately loses access to class's pending queue reviews.
        Historical validated decisions remain intact.
        """
        async with self.session_factory() as session:
            stmt = select(TeacherAssignmentModel).where(
                and_(
                    TeacherAssignmentModel.school_id == school_id,
                    TeacherAssignmentModel.class_id == class_id,
                    TeacherAssignmentModel.teacher_id == teacher_id,
                    TeacherAssignmentModel.active.is_(True),
                )
            )
            res = await session.execute(stmt)
            asg = res.scalar_one_or_none()
            if not asg:
                return False

            asg.active = False
            await session.commit()
            return True
