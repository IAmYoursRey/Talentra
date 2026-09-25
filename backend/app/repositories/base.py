from abc import ABC, abstractmethod
from ..domain.models import User, AuthIdentity, School, SessionRecord, AuditEvent
from ..domain.enums import IdentifierType

class IdentityRepository(ABC):
    @abstractmethod
    async def get_school_by_id(self, school_id: str) -> School | None:
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> User | None:
        pass

    @abstractmethod
    async def get_identity_by_identifier(
        self, normalized_identifier: str, identifier_type: IdentifierType
    ) -> tuple[AuthIdentity, User] | None:
        pass

    @abstractmethod
    async def update_password_hash(self, user_id: str, new_hash: str, must_change_password: bool = False) -> bool:
        pass

    @abstractmethod
    async def verify_user_password(self, user_id: str, plain_password: str) -> bool:
        pass

class SessionRepository(ABC):
    @abstractmethod
    async def create_session(self, session: SessionRecord) -> SessionRecord:
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> SessionRecord | None:
        pass

    @abstractmethod
    async def revoke_session(self, session_id: str) -> bool:
        pass

    @abstractmethod
    async def revoke_all_user_sessions(self, user_id: str, except_session_id: str | None = None) -> int:
        pass

class AuditRepository(ABC):
    @abstractmethod
    async def record_event(self, event: AuditEvent) -> AuditEvent:
        pass

    @abstractmethod
    async def list_recent_events(self, limit: int = 50) -> list[AuditEvent]:
        pass
