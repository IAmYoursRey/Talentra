import json
import uuid
from datetime import datetime, timezone
from typing import Tuple, List, Optional
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..core.database import AsyncSessionLocal
from ..core.security import compute_identifier_lookup_hash
from ..domain.enums import UserRole, IdentifierType, UserStatus, AuditEventType
from ..domain.models import User, AuthIdentity, School, SessionRecord, AuditEvent
from ..db.models import (
    SchoolModel,
    UserModel,
    AuthIdentityModel,
    StudentProfileModel,
    TeacherProfileModel,
    ClassModel,
    EnrollmentModel,
    TeacherAssignmentModel,
    SessionModel,
    AuditEventModel,
)
from .base import IdentityRepository, SessionRepository, AuditRepository


class PostgresIdentityRepository(IdentityRepository):
    def __init__(self, session_factory: Optional[async_sessionmaker[AsyncSession]] = None):
        self.session_factory = session_factory or AsyncSessionLocal

    async def get_school_by_id(self, school_id: str) -> Optional[School]:
        async with self.session_factory() as session:
            stmt = select(SchoolModel).where(SchoolModel.id == school_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                return None
            return School(
                id=model.id,
                name=model.name,
                npsn_masked="NPSN: *****" + model.id[-3:],
            )

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        async with self.session_factory() as session:
            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await session.execute(stmt)
            user_model = result.scalar_one_or_none()
            if not user_model:
                return None
            return await self._map_user_model_to_domain(session, user_model)

    async def get_user_for_school(self, school_id: str, user_id: str) -> Optional[User]:
        """Tenant-scoped user lookup guaranteeing school boundary isolation."""
        async with self.session_factory() as session:
            stmt = select(UserModel).where(
                and_(UserModel.id == user_id, UserModel.school_id == school_id)
            )
            result = await session.execute(stmt)
            user_model = result.scalar_one_or_none()
            if not user_model:
                return None
            return await self._map_user_model_to_domain(session, user_model)

    async def get_identity_by_identifier(
        self, normalized_identifier: str, identifier_type: IdentifierType
    ) -> Optional[Tuple[AuthIdentity, User]]:
        lookup_hash = compute_identifier_lookup_hash(normalized_identifier)
        ident_type_variants = [identifier_type.value.lower(), identifier_type.value.upper(), identifier_type.value]
        async with self.session_factory() as session:
            stmt = select(AuthIdentityModel).where(
                and_(
                    AuthIdentityModel.identifier_type.in_(ident_type_variants),
                    AuthIdentityModel.identifier_lookup_hash == lookup_hash,
                )
            )
            result = await session.execute(stmt)
            ident_model = result.scalar_one_or_none()
            if not ident_model:
                return None

            # Load user
            stmt_user = select(UserModel).where(UserModel.id == ident_model.user_id)
            res_user = await session.execute(stmt_user)
            user_model = res_user.scalar_one_or_none()
            if not user_model:
                return None

            user_domain = await self._map_user_model_to_domain(session, user_model)
            ident_domain = AuthIdentity(
                id=ident_model.id,
                user_id=ident_model.user_id,
                identifier_type=IdentifierType(ident_model.identifier_type.upper()),
                normalized_identifier=normalized_identifier,
                identifier_last4=ident_model.identifier_last4,
                identifier_lookup_hash=ident_model.identifier_lookup_hash,
                password_hash=ident_model.password_hash,
                active=ident_model.active,
            )
            return ident_domain, user_domain

    async def update_password_hash(self, user_id: str, new_hash: str, must_change_password: bool = False) -> bool:
        async with self.session_factory() as session:
            stmt = (
                update(AuthIdentityModel)
                .where(AuthIdentityModel.user_id == user_id)
                .values(
                    password_hash=new_hash,
                    must_change_password=must_change_password,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            res = await session.execute(stmt)
            await session.commit()
            return res.rowcount > 0

    update_user_password = update_password_hash

    async def verify_user_password(self, user_id: str, plain_password: str) -> bool:
        from ..core.security import verify_password
        async with self.session_factory() as session:
            stmt = select(AuthIdentityModel).where(
                and_(AuthIdentityModel.user_id == user_id, AuthIdentityModel.active.is_(True))
            )
            res = await session.execute(stmt)
            identities = res.scalars().all()
            for ident in identities:
                if verify_password(plain_password, ident.password_hash):
                    return True
            return False

    async def _map_user_model_to_domain(self, session: AsyncSession, model: UserModel) -> User:
        class_name = None
        title = None
        masked_id = "ID: *******" + model.id[-3:]

        if model.role == "student":
            stmt = select(StudentProfileModel).where(StudentProfileModel.user_id == model.id)
            res = await session.execute(stmt)
            profile = res.scalar_one_or_none()
            if profile:
                class_name = profile.class_name
        elif model.role in ("teacher", "admin"):
            stmt = select(TeacherProfileModel).where(TeacherProfileModel.user_id == model.id)
            res = await session.execute(stmt)
            t_profile = res.scalar_one_or_none()
            if t_profile:
                title = t_profile.display_title

        # Query first identity to construct masked identifier
        stmt_ident = select(AuthIdentityModel).where(AuthIdentityModel.user_id == model.id)
        res_ident = await session.execute(stmt_ident)
        first_ident = res_ident.scalars().first()
        must_change_pwd = False
        if first_ident:
            masked_id = f"{first_ident.identifier_type.upper()}: *******{first_ident.identifier_last4}"
            must_change_pwd = bool(first_ident.must_change_password)

        return User(
            id=model.id,
            school_id=model.school_id,
            role=UserRole(model.role),
            status=UserStatus(model.status),
            display_name=model.display_name,
            email=model.email or f"{model.id}@talentra.id",
            class_name=class_name,
            title=title,
            masked_identifier=masked_id,
            must_change_password=must_change_pwd,
        )


class PostgresSessionRepository(SessionRepository):
    def __init__(self, session_factory: Optional[async_sessionmaker[AsyncSession]] = None):
        self.session_factory = session_factory or AsyncSessionLocal

    async def create_session(self, session_record: SessionRecord) -> SessionRecord:
        async with self.session_factory() as session:
            model = SessionModel(
                id=session_record.session_id,
                user_id=session_record.user_id,
                school_id=session_record.school_id,
                role=session_record.role.value,
                created_at=session_record.created_at,
                expires_at=session_record.expires_at,
                revoked_at=session_record.revoked_at,
            )
            session.add(model)
            await session.commit()
            return session_record

    async def get_session(self, session_id: str) -> Optional[SessionRecord]:
        async with self.session_factory() as session:
            stmt = select(SessionModel).where(SessionModel.id == session_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                return None
            created_at = model.created_at
            if created_at and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            expires_at = model.expires_at
            if expires_at and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            revoked_at = model.revoked_at
            if revoked_at and revoked_at.tzinfo is None:
                revoked_at = revoked_at.replace(tzinfo=timezone.utc)

            return SessionRecord(
                session_id=model.id,
                user_id=model.user_id,
                school_id=model.school_id,
                role=UserRole(model.role),
                created_at=created_at,
                expires_at=expires_at,
                revoked_at=revoked_at,
            )

    async def revoke_session(self, session_id: str) -> bool:
        async with self.session_factory() as session:
            now = datetime.now(timezone.utc)
            stmt = (
                update(SessionModel)
                .where(SessionModel.id == session_id)
                .values(revoked_at=now)
            )
            res = await session.execute(stmt)
            await session.commit()
            return res.rowcount > 0

    async def revoke_all_user_sessions(self, user_id: str, except_session_id: Optional[str] = None) -> int:
        async with self.session_factory() as session:
            now = datetime.now(timezone.utc)
            conditions = [
                SessionModel.user_id == user_id,
                SessionModel.revoked_at.is_(None),
            ]
            if except_session_id:
                conditions.append(SessionModel.id != except_session_id)

            stmt = (
                update(SessionModel)
                .where(and_(*conditions))
                .values(revoked_at=now)
            )
            res = await session.execute(stmt)
            await session.commit()
            return res.rowcount


class PostgresAuditRepository(AuditRepository):
    def __init__(self, session_factory: Optional[async_sessionmaker[AsyncSession]] = None):
        self.session_factory = session_factory or AsyncSessionLocal

    async def record_event(self, event: AuditEvent) -> AuditEvent:
        async with self.session_factory() as session:
            payload_meta = dict(event.metadata or {})
            payload_meta["safe_context"] = event.safe_context
            # Explicitly sanitize: never persist passwords or tokens
            for key in ["password", "token", "raw_identifier", "jwt", "secret", "csrf"]:
                payload_meta.pop(key, None)

            created_at = event.timestamp
            if created_at and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            model = AuditEventModel(
                id=event.id,
                school_id=event.school_id,
                actor_user_id=event.user_id,
                event_type=event.event_type.value,
                request_id=event.request_correlation_id,
                metadata_json=json.dumps(payload_meta),
                created_at=created_at,
            )
            session.add(model)
            await session.commit()
            return event

    async def list_recent_events(self, limit: int = 50) -> List[AuditEvent]:
        async with self.session_factory() as session:
            stmt = (
                select(AuditEventModel)
                .order_by(AuditEventModel.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            models = result.scalars().all()
            events = []
            for m in models:
                try:
                    meta = json.loads(m.metadata_json) if m.metadata_json else {}
                    safe_ctx = meta.get("safe_context", "")
                except Exception:
                    meta = {}
                    safe_ctx = ""

                created_at = m.created_at
                if created_at and created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)

                events.append(
                    AuditEvent(
                        id=m.id,
                        timestamp=created_at,
                        event_type=AuditEventType(m.event_type),
                        user_id=m.actor_user_id,
                        school_id=m.school_id,
                        request_correlation_id=m.request_id,
                        safe_context=safe_ctx,
                        metadata=meta,
                    )
                )
            return events

    async def get_events_for_school(self, school_id: str) -> List[AuditEvent]:
        async with self.session_factory() as session:
            stmt = (
                select(AuditEventModel)
                .where(AuditEventModel.school_id == school_id)
                .order_by(AuditEventModel.created_at.desc())
            )
            result = await session.execute(stmt)
            models = result.scalars().all()
            events = []
            for m in models:
                try:
                    meta = json.loads(m.metadata_json) if m.metadata_json else {}
                    safe_ctx = meta.get("safe_context", "")
                except Exception:
                    meta = {}
                    safe_ctx = ""

                created_at = m.created_at
                if created_at and created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)

                events.append(
                    AuditEvent(
                        id=m.id,
                        timestamp=created_at,
                        event_type=AuditEventType(m.event_type),
                        user_id=m.actor_user_id,
                        school_id=m.school_id,
                        request_correlation_id=m.request_id,
                        safe_context=safe_ctx,
                        metadata=meta,
                    )
                )
            return events
