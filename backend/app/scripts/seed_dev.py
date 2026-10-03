import asyncio
import os
import sys
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password, compute_identifier_lookup_hash
from app.db.models import (
    SchoolModel,
    UserModel,
    AuthIdentityModel,
    StudentProfileModel,
    TeacherProfileModel,
    ClassModel,
    EnrollmentModel,
    TeacherAssignmentModel,
    SkillTagModel,
)


async def seed_development_data(session_factory: async_sessionmaker[AsyncSession] | None = None) -> None:
    """
    Idempotent development seed script populating synthetic test data.
    Never run or allowed in production mode!
    """
    if settings.app_env == "production":
        raise RuntimeError("CRITICAL: seed_dev cannot be executed in production environment!")

    factory = session_factory or AsyncSessionLocal
    async with factory() as session:
        # 1. Demo School: SMA Negeri 1 Teladan Jakarta
        school_id = "sch_teladan_001"
        stmt = select(SchoolModel).where(SchoolModel.id == school_id)
        res = await session.execute(stmt)
        school = res.scalar_one_or_none()
        if not school:
            school = SchoolModel(
                id=school_id,
                name="SMA Negeri 1 Teladan Jakarta",
                status="active",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(school)
            await session.flush()

        # 2. Synthetic Student: Alya Rahma Azzahra (NISN: 0071234321)
        student_id = "usr_std_001"
        stmt = select(UserModel).where(UserModel.id == student_id)
        res = await session.execute(stmt)
        student = res.scalar_one_or_none()
        if not student:
            student = UserModel(
                id=student_id,
                school_id=school_id,
                role="student",
                status="active",
                display_name="Alya Rahma Azzahra",
                email="alya.rahma@student.talentra.id",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(student)
            await session.flush()

            # Student profile
            session.add(
                StudentProfileModel(
                    user_id=student_id,
                    grade_level="XII",
                    class_name="XII RPL 1",
                    graduation_year=2026,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )

            # Student NISN AuthIdentity (leading zero preserved)
            nisn = "0071234321"
            session.add(
                AuthIdentityModel(
                    id="idn_std_001",
                    user_id=student_id,
                    identifier_type="nisn",
                    identifier_lookup_hash=compute_identifier_lookup_hash(nisn),
                    identifier_last4=nisn[-4:],
                    password_hash=hash_password("PasswordSiswa123!"),
                    active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )

        # 3. Synthetic Teacher: Budi Santoso (NIP: 198204152005011789, NUPTK: 4235760662200112)
        teacher_id = "usr_tch_002"
        stmt = select(UserModel).where(UserModel.id == teacher_id)
        res = await session.execute(stmt)
        teacher = res.scalar_one_or_none()
        if not teacher:
            teacher = UserModel(
                id=teacher_id,
                school_id=school_id,
                role="teacher",
                status="active",
                display_name="Budi Santoso, S.Kom., M.Kom.",
                email="budi.santoso@guru.talentra.id",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(teacher)
            await session.flush()

            # Teacher profile
            session.add(
                TeacherProfileModel(
                    user_id=teacher_id,
                    display_title="Guru Pembimbing & Validator RPL",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )

            # Teacher NIP
            nip = "198204152005011789"
            session.add(
                AuthIdentityModel(
                    id="idn_tch_002_nip",
                    user_id=teacher_id,
                    identifier_type="nip",
                    identifier_lookup_hash=compute_identifier_lookup_hash(nip),
                    identifier_last4=nip[-4:],
                    password_hash=hash_password("PasswordGuru123!"),
                    active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )

            # Teacher NUPTK
            nuptk = "4235760662200112"
            session.add(
                AuthIdentityModel(
                    id="idn_tch_002_nuptk",
                    user_id=teacher_id,
                    identifier_type="nuptk",
                    identifier_lookup_hash=compute_identifier_lookup_hash(nuptk),
                    identifier_last4=nuptk[-4:],
                    password_hash=hash_password("PasswordGuru123!"),
                    active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )

        # 4. Synthetic School Admin: Dra. Hj. Ratna Juwita (NPSN: 20101543)
        admin_id = "usr_adm_003"
        stmt = select(UserModel).where(UserModel.id == admin_id)
        res = await session.execute(stmt)
        admin = res.scalar_one_or_none()
        if not admin:
            admin = UserModel(
                id=admin_id,
                school_id=school_id,
                role="admin",
                status="active",
                display_name="Dra. Hj. Ratna Juwita, M.Pd.",
                email="admin.kurikulum@teladan.sch.id",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(admin)
            await session.flush()

            session.add(
                TeacherProfileModel(
                    user_id=admin_id,
                    display_title="Koordinator Talenta & Kurikulum Sekolah",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )

            npsn = "20101543"
            session.add(
                AuthIdentityModel(
                    id="idn_adm_003",
                    user_id=admin_id,
                    identifier_type="npsn",
                    identifier_lookup_hash=compute_identifier_lookup_hash(npsn),
                    identifier_last4=npsn[-4:],
                    password_hash=hash_password("PasswordAdmin123!"),
                    active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )

        # 4b. Admin Raihan Ansari (email login: raihanansari6678@gmail.com)
        raihan_id = "usr_adm_raihan"
        stmt = select(UserModel).where(UserModel.id == raihan_id)
        res = await session.execute(stmt)
        raihan_user = res.scalar_one_or_none()
        if not raihan_user:
            raihan_user = UserModel(
                id=raihan_id,
                school_id=school_id,
                role="admin",
                status="active",
                display_name="Admin Demo",
                email="raihanansari6678@gmail.com",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(raihan_user)
            await session.flush()

            session.add(
                TeacherProfileModel(
                    user_id=raihan_id,
                    display_title="Administrator Sekolah TALENTRA",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )

            email_ident = "raihanansari6678@gmail.com"
            session.add(
                AuthIdentityModel(
                    id="idn_adm_raihan",
                    user_id=raihan_id,
                    identifier_type="email",
                    identifier_lookup_hash=compute_identifier_lookup_hash(email_ident),
                    identifier_last4="6678",
                    password_hash=hash_password("raihanansari6678@gmail.com"),
                    active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )

        # 5. Disabled User for Negative Authorization Testing: Dimas Nonaktif (NISN: 0089999884)
        disabled_id = "usr_std_disabled"
        stmt = select(UserModel).where(UserModel.id == disabled_id)
        res = await session.execute(stmt)
        disabled_user = res.scalar_one_or_none()
        if not disabled_user:
            disabled_user = UserModel(
                id=disabled_id,
                school_id=school_id,
                role="student",
                status="disabled",
                display_name="Dimas Nonaktif",
                email="dimas.nonaktif@student.talentra.id",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(disabled_user)
            await session.flush()

            session.add(
                StudentProfileModel(
                    user_id=disabled_id,
                    grade_level="XII",
                    class_name="XII TKJ 1",
                    graduation_year=2026,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )

            dis_nisn = "0089999884"
            session.add(
                AuthIdentityModel(
                    id="idn_std_disabled",
                    user_id=disabled_id,
                    identifier_type="nisn",
                    identifier_lookup_hash=compute_identifier_lookup_hash(dis_nisn),
                    identifier_last4=dis_nisn[-4:],
                    password_hash=hash_password("PasswordSiswa123!"),
                    active=False,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )

        # 5b. Unassigned Teacher in Same School (Siti Aminah, S.Pd. - NIP: 198501012010011001)
        unassigned_tch_id = "usr_tch_unassigned"
        stmt = select(UserModel).where(UserModel.id == unassigned_tch_id)
        res = await session.execute(stmt)
        if not res.scalar_one_or_none():
            session.add(
                UserModel(
                    id=unassigned_tch_id,
                    school_id=school_id,
                    role="teacher",
                    status="active",
                    display_name="Siti Aminah, S.Pd.",
                    email="siti.aminah@guru.talentra.id",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            session.add(
                TeacherProfileModel(
                    user_id=unassigned_tch_id,
                    display_title="Guru Bahasa Indonesia",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            session.add(
                AuthIdentityModel(
                    id="idn_tch_unassigned_nip",
                    user_id=unassigned_tch_id,
                    identifier_type="nip",
                    identifier_lookup_hash=compute_identifier_lookup_hash("198501012010011001"),
                    identifier_last4="1001",
                    password_hash=hash_password("PasswordGuru123!"),
                    active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )

        # 5c. Other School & Teacher for Cross-School Boundary Testing
        other_sch_id = "sch_sekolah_lain_999"
        stmt = select(SchoolModel).where(SchoolModel.id == other_sch_id)
        res = await session.execute(stmt)
        if not res.scalar_one_or_none():
            session.add(
                SchoolModel(
                    id=other_sch_id,
                    name="SMK Negeri 2 Bandung",
                    status="active",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            other_tch_id = "usr_tch_other_school"
            session.add(
                UserModel(
                    id=other_tch_id,
                    school_id=other_sch_id,
                    role="teacher",
                    status="active",
                    display_name="Agus Setiawan, M.Pd.",
                    email="agus.setiawan@guru.smk2bdg.sch.id",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            session.add(
                TeacherProfileModel(
                    user_id=other_tch_id,
                    display_title="Guru Pembimbing Bandung",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            session.add(
                AuthIdentityModel(
                    id="idn_tch_other_nip",
                    user_id=other_tch_id,
                    identifier_type="nip",
                    identifier_lookup_hash=compute_identifier_lookup_hash("197903032003011003"),
                    identifier_last4="1003",
                    password_hash=hash_password("PasswordGuru123!"),
                    active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )
        await session.flush()

        # 6. Class: XII RPL 1
        class_id = "cls_rpl_001"
        stmt = select(ClassModel).where(ClassModel.id == class_id)
        res = await session.execute(stmt)
        cls = res.scalar_one_or_none()
        if not cls:
            cls = ClassModel(
                id=class_id,
                school_id=school_id,
                name="XII RPL 1",
                grade_level="XII",
                academic_year="2025/2026",
                status="active",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(cls)
            await session.flush()

        # 7. Enrollment: Alya -> XII RPL 1
        enr_id = "enr_alya_001"
        stmt = select(EnrollmentModel).where(EnrollmentModel.id == enr_id)
        res = await session.execute(stmt)
        enr = res.scalar_one_or_none()
        if not enr:
            enr = EnrollmentModel(
                id=enr_id,
                school_id=school_id,
                class_id=class_id,
                student_id=student_id,
                academic_year="2025/2026",
                status="active",
                created_at=datetime.now(timezone.utc),
            )
            session.add(enr)

        # 8. Teacher Assignment: Pak Budi -> Validator for XII RPL 1
        assign_id = "asn_budi_001"
        stmt = select(TeacherAssignmentModel).where(TeacherAssignmentModel.id == assign_id)
        res = await session.execute(stmt)
        asn = res.scalar_one_or_none()
        if not asn:
            asn = TeacherAssignmentModel(
                id=assign_id,
                school_id=school_id,
                teacher_id=teacher_id,
                class_id=class_id,
                assignment_type="portfolio_validator",
                active=True,
                created_at=datetime.now(timezone.utc),
            )
            session.add(asn)

        # 9. Canonical Skill Tags Catalog
        canonical_tags_data = [
            ("web-development", "Web Development", "technical", "Pengembangan aplikasi web modern", "digital-literacy", 1),
            ("ui-ux", "UI/UX Design", "creative", "Desain antarmuka dan pengalaman pengguna", "creativity", 2),
            ("problem-solving", "Problem Solving", "problem_solving", "Pemecahan masalah dan logika algoritma", "problem-solving", 3),
            ("leadership", "Leadership", "leadership", "Kepemimpinan tim dan manajemen proyek", "leadership", 4),
            ("teamwork", "Teamwork & Kolaborasi", "collaboration", "Kerja sama tim dalam menyelesaikan proyek", "collaboration", 5),
            ("public-speaking", "Public Speaking", "communication", "Presentasi dan komunikasi verbal", "communication", 6),
            ("event-management", "Event Management", "leadership", "Manajemen acara dan koordinasi kegiatan", "leadership", 7),
            ("data-analysis", "Data Analysis", "technical", "Pengolahan dan visualisasi data", "digital-literacy", 8),
            ("graphic-design", "Graphic Design", "creative", "Desain grafis dan ilustrasi digital", "creativity", 9),
            ("research", "Research & Riset", "problem_solving", "Riset investigatif dan penulisan ilmiah", "problem-solving", 10),
            ("writing", "Technical Writing", "communication", "Penulisan teknis dan dokumentasi", "communication", 11),
            ("video-editing", "Video Editing", "creative", "Penyuntingan video dan konten multimedia", "digital-literacy", 12),
            ("creativity", "Kreativitas & Inovasi", "creative", "Inovasi karya dan solusi kreatif", "creativity", 13),
            ("digital-literacy", "Digital Literacy", "technical", "Literasi digital dan etika siber", "digital-literacy", 14),
        ]
        for code, label, category, desc, radar_dim, order in canonical_tags_data:
            stmt = select(SkillTagModel).where(SkillTagModel.code == code)
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                session.add(
                    SkillTagModel(
                        id=f"tag_{code.replace('-', '_')}",
                        code=code,
                        display_name=label,
                        category=category,
                        description=desc,
                        radar_dimension=radar_dim,
                        sort_order=order,
                        active=True,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                )

        await session.commit()
        print("✓ Development synthetic data successfully seeded into database.")


if __name__ == "__main__":
    asyncio.run(seed_development_data())
