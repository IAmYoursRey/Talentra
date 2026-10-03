from datetime import datetime, timezone
from typing import Dict, List, Tuple
from ..core.config import settings
from ..core.security import hash_password
from ..domain.enums import UserRole, IdentifierType, UserStatus
from ..domain.models import User, AuthIdentity, School, SessionRecord, AuditEvent
from .base import IdentityRepository, SessionRepository, AuditRepository

class InMemoryIdentityRepository(IdentityRepository):
    def __init__(self):
        if settings.app_env == "production":
            raise RuntimeError(
                "CRITICAL ARCHITECTURAL CONSTRAINT: InMemoryIdentityRepository cannot be used in production mode! "
                "Phase 3 PostgreSQL persistence adapter is required."
            )
        
        self.schools: Dict[str, School] = {}
        self.users: Dict[str, User] = {}
        # Key: (normalized_identifier, identifier_type) -> (AuthIdentity, User)
        self.identities: Dict[Tuple[str, IdentifierType], Tuple[AuthIdentity, User]] = {}
        self._seed_synthetic_data()

    def _seed_synthetic_data(self):
        # 1. School
        demo_school = School(
            id="sch_teladan_001",
            name="SMA Negeri 1 Teladan Jakarta",
            npsn_masked="NPSN: *****543",
        )
        self.schools[demo_school.id] = demo_school

        # 2. Student (Alya Rahma Azzahra) - NISN 10 digits with leading 0
        student_user = User(
            id="usr_std_001",
            school_id=demo_school.id,
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            display_name="Alya Rahma Azzahra",
            email="alya.rahma@student.talentra.id",
            class_name="XII RPL 1",
            masked_identifier="NISN: *******321",
        )
        student_identity = AuthIdentity(
            id="idn_std_001",
            user_id=student_user.id,
            identifier_type=IdentifierType.NISN,
            normalized_identifier="0071234321",
            password_hash=hash_password("PasswordSiswa123!"),
            active=True,
        )
        student_identity_alias = AuthIdentity(
            id="idn_std_001_alias",
            user_id=student_user.id,
            identifier_type=IdentifierType.NISN,
            normalized_identifier="0081234567",
            password_hash=hash_password("PasswordSiswa123!"),
            active=True,
        )
        self.users[student_user.id] = student_user
        self.identities[(student_identity.normalized_identifier, student_identity.identifier_type)] = (student_identity, student_user)
        self.identities[(student_identity_alias.normalized_identifier, student_identity_alias.identifier_type)] = (student_identity_alias, student_user)

        # 3. Teacher (Budi Santoso) - NIP 18 digits and NUPTK 16 digits
        teacher_user = User(
            id="usr_tch_002",
            school_id=demo_school.id,
            role=UserRole.TEACHER,
            status=UserStatus.ACTIVE,
            display_name="Budi Santoso, S.Kom., M.Kom.",
            email="budi.santoso@guru.talentra.id",
            title="Guru Pembimbing & Validator RPL",
            masked_identifier="NIP: *******789",
        )
        teacher_nip_identity = AuthIdentity(
            id="idn_tch_002_nip",
            user_id=teacher_user.id,
            identifier_type=IdentifierType.NIP,
            normalized_identifier="198204152005011789",
            password_hash=hash_password("PasswordGuru123!"),
            active=True,
        )
        teacher_nip_identity_alias = AuthIdentity(
            id="idn_tch_002_nip_alias",
            user_id=teacher_user.id,
            identifier_type=IdentifierType.NIP,
            normalized_identifier="198501012010011001",
            password_hash=hash_password("PasswordGuru123!"),
            active=True,
        )
        teacher_nuptk_identity = AuthIdentity(
            id="idn_tch_002_nuptk",
            user_id=teacher_user.id,
            identifier_type=IdentifierType.NUPTK,
            normalized_identifier="4235760662200112",
            password_hash=hash_password("PasswordGuru123!"),
            active=True,
        )
        self.users[teacher_user.id] = teacher_user
        self.identities[(teacher_nip_identity.normalized_identifier, teacher_nip_identity.identifier_type)] = (teacher_nip_identity, teacher_user)
        self.identities[(teacher_nip_identity_alias.normalized_identifier, teacher_nip_identity_alias.identifier_type)] = (teacher_nip_identity_alias, teacher_user)
        self.identities[(teacher_nuptk_identity.normalized_identifier, teacher_nuptk_identity.identifier_type)] = (teacher_nuptk_identity, teacher_user)

        # 4. Admin (Dra. Hj. Ratna Juwita) - NPSN 8 alphanumeric chars
        admin_user = User(
            id="usr_adm_003",
            school_id=demo_school.id,
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            display_name="Dra. Hj. Ratna Juwita, M.Pd.",
            email="admin.kurikulum@teladan.sch.id",
            title="Koordinator Talenta & Kurikulum Sekolah",
            masked_identifier="NPSN: *****543",
        )
        admin_identity = AuthIdentity(
            id="idn_adm_003",
            user_id=admin_user.id,
            identifier_type=IdentifierType.NPSN,
            normalized_identifier="20101543",
            password_hash=hash_password("PasswordAdmin123!"),
            active=True,
        )
        self.users[admin_user.id] = admin_user
        self.identities[(admin_identity.normalized_identifier, admin_identity.identifier_type)] = (admin_identity, admin_user)

        # 4b. Admin Raihan Ansari (email login: raihanansari6678@gmail.com)
        raihan_admin = User(
            id="usr_adm_raihan",
            school_id=demo_school.id,
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            display_name="Raihan Ansari",
            email="raihanansari6678@gmail.com",
            title="Administrator Sekolah TALENTRA",
            masked_identifier="EMAIL: *******6678@gmail.com",
        )
        raihan_identity = AuthIdentity(
            id="idn_adm_raihan",
            user_id=raihan_admin.id,
            identifier_type=IdentifierType.EMAIL,
            normalized_identifier="raihanansari6678@gmail.com",
            password_hash=hash_password("raihanansari6678@gmail.com"),
            active=True,
        )
        self.users[raihan_admin.id] = raihan_admin
        self.identities[(raihan_identity.normalized_identifier, raihan_identity.identifier_type)] = (raihan_identity, raihan_admin)

        # 5. Disabled User (for negative authorization testing)
        disabled_student = User(
            id="usr_std_disabled",
            school_id=demo_school.id,
            role=UserRole.STUDENT,
            status=UserStatus.DISABLED,
            display_name="Dimas Nonaktif",
            email="dimas.nonaktif@student.talentra.id",
            class_name="XII TKJ 1",
            masked_identifier="NISN: *******884",
        )
        disabled_identity = AuthIdentity(
            id="idn_std_disabled",
            user_id=disabled_student.id,
            identifier_type=IdentifierType.NISN,
            normalized_identifier="0089999884",
            password_hash=hash_password("PasswordSiswa123!"),
            active=False,
        )
        self.users[disabled_student.id] = disabled_student
        self.identities[(disabled_identity.normalized_identifier, disabled_identity.identifier_type)] = (disabled_identity, disabled_student)

        # 6. Student 2 in Same School (Bambang Prakoso)
        student2_user = User(
            id="usr_std_002",
            school_id=demo_school.id,
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            display_name="Bambang Prakoso",
            email="bambang.prakoso@student.talentra.id",
            class_name="XII RPL 1",
            masked_identifier="NISN: *******322",
        )
        student2_identity = AuthIdentity(
            id="idn_std_002",
            user_id=student2_user.id,
            identifier_type=IdentifierType.NISN,
            normalized_identifier="0071234322",
            password_hash=hash_password("PasswordSiswa123!"),
            active=True,
        )
        self.users[student2_user.id] = student2_user
        self.identities[(student2_identity.normalized_identifier, student2_identity.identifier_type)] = (student2_identity, student2_user)

        # 7. Student in Other School
        other_school = School(
            id="sch_sekolah_lain_999",
            name="SMK Negeri 2 Bandung",
            npsn_masked="NPSN: *****999",
        )
        self.schools[other_school.id] = other_school
        other_student = User(
            id="usr_std_other_school",
            school_id=other_school.id,
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            display_name="Siti Rahayu",
            email="siti.rahayu@student.smk2bdg.sch.id",
            class_name="XII TKJ 2",
            masked_identifier="NISN: *******999",
        )
        other_identity = AuthIdentity(
            id="idn_std_other",
            user_id=other_student.id,
            identifier_type=IdentifierType.NISN,
            normalized_identifier="0071234999",
            password_hash=hash_password("PasswordSiswa123!"),
            active=True,
        )
        self.users[other_student.id] = other_student
        self.identities[(other_identity.normalized_identifier, other_identity.identifier_type)] = (other_identity, other_student)

        # 8. Unassigned Teacher in Same School (Siti Aminah, S.Pd.)
        unassigned_teacher = User(
            id="usr_tch_unassigned",
            school_id=demo_school.id,
            role=UserRole.TEACHER,
            status=UserStatus.ACTIVE,
            display_name="Siti Aminah, S.Pd.",
            email="siti.aminah@guru.talentra.id",
            title="Guru Bahasa Indonesia",
            masked_identifier="NIP: *******001",
        )
        unassigned_identity = AuthIdentity(
            id="idn_tch_unassigned_nip",
            user_id=unassigned_teacher.id,
            identifier_type=IdentifierType.NIP,
            normalized_identifier="198501012010011001",
            password_hash=hash_password("PasswordGuru123!"),
            active=True,
        )
        self.users[unassigned_teacher.id] = unassigned_teacher
        self.identities[(unassigned_identity.normalized_identifier, unassigned_identity.identifier_type)] = (unassigned_identity, unassigned_teacher)

        # 9. Teacher in Other School (Agus Setiawan, M.Pd.)
        other_teacher = User(
            id="usr_tch_other_school",
            school_id=other_school.id,
            role=UserRole.TEACHER,
            status=UserStatus.ACTIVE,
            display_name="Agus Setiawan, M.Pd.",
            email="agus.setiawan@guru.smk2bdg.sch.id",
            title="Guru Pembimbing Bandung",
            masked_identifier="NIP: *******003",
        )
        other_teacher_identity = AuthIdentity(
            id="idn_tch_other_nip",
            user_id=other_teacher.id,
            identifier_type=IdentifierType.NIP,
            normalized_identifier="197903032003011003",
            password_hash=hash_password("PasswordGuru123!"),
            active=True,
        )
        self.users[other_teacher.id] = other_teacher
        self.identities[(other_teacher_identity.normalized_identifier, other_teacher_identity.identifier_type)] = (other_teacher_identity, other_teacher)

    async def get_school_by_id(self, school_id: str) -> School | None:
        return self.schools.get(school_id)

    async def get_user_by_id(self, user_id: str) -> User | None:
        return self.users.get(user_id)

    async def get_identity_by_identifier(
        self, normalized_identifier: str, identifier_type: IdentifierType
    ) -> Tuple[AuthIdentity, User] | None:
        return self.identities.get((normalized_identifier, identifier_type))

    async def update_password_hash(self, user_id: str, new_hash: str, must_change_password: bool = False) -> bool:
        user = self.users.get(user_id)
        if not user:
            return False
        user.must_change_password = must_change_password
        for (ident_val, ident_type), (ident, u) in list(self.identities.items()):
            if u.id == user_id:
                ident.password_hash = new_hash
                ident.must_change_password = must_change_password
        return True

    async def verify_user_password(self, user_id: str, plain_password: str) -> bool:
        from ..core.security import verify_password
        for (ident_val, ident_type), (ident, u) in self.identities.items():
            if u.id == user_id and ident.active:
                if verify_password(plain_password, ident.password_hash):
                    return True
        return False


class InMemorySessionRepository(SessionRepository):
    def __init__(self):
        if settings.app_env == "production":
            raise RuntimeError(
                "CRITICAL ARCHITECTURAL CONSTRAINT: InMemorySessionRepository cannot be used in production mode!"
            )
        self.sessions: Dict[str, SessionRecord] = {}

    async def create_session(self, session: SessionRecord) -> SessionRecord:
        self.sessions[session.session_id] = session
        return session

    async def get_session(self, session_id: str) -> SessionRecord | None:
        return self.sessions.get(session_id)

    async def revoke_session(self, session_id: str) -> bool:
        session = self.sessions.get(session_id)
        if not session:
            return False
        session.revoked_at = datetime.now(timezone.utc)
        return True

    async def revoke_all_user_sessions(self, user_id: str, except_session_id: str | None = None) -> int:
        count = 0
        now = datetime.now(timezone.utc)
        for s in self.sessions.values():
            if s.user_id == user_id and s.revoked_at is None:
                if except_session_id and s.session_id == except_session_id:
                    continue
                s.revoked_at = now
                count += 1
        return count


class InMemoryAuditRepository(AuditRepository):
    def __init__(self):
        if settings.app_env == "production":
            raise RuntimeError(
                "CRITICAL ARCHITECTURAL CONSTRAINT: InMemoryAuditRepository cannot be used in production mode!"
            )
        self.events: List[AuditEvent] = []

    async def record_event(self, event: AuditEvent) -> AuditEvent:
        self.events.append(event)
        return event

    async def list_recent_events(self, limit: int = 50) -> List[AuditEvent]:
        return list(reversed(self.events[-limit:]))
