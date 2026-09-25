import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from .enums import UserRole, IdentifierType, UserStatus, AuditEventType

class School(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    npsn_masked: str  # e.g. "NPSN: *******543"

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    school_id: str
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE
    display_name: str
    email: str
    class_name: str | None = None
    title: str | None = None
    masked_identifier: str  # e.g. "NISN: *******321"
    must_change_password: bool = False

class AuthIdentity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    identifier_type: IdentifierType
    normalized_identifier: str
    identifier_last4: str | None = None
    identifier_lookup_hash: str | None = None
    password_hash: str
    active: bool = True
    must_change_password: bool = False

class SessionRecord(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    school_id: str
    role: UserRole
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    revoked_at: datetime | None = None

    @property
    def is_valid(self) -> bool:
        now = datetime.now(timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return self.revoked_at is None and now < exp

class AuditEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: AuditEventType
    user_id: str | None = None
    school_id: str | None = None
    request_correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    safe_context: str
    metadata: dict = Field(default_factory=dict)
    # NEVER store raw password, JWT token, or full NISN/NIP/NPSN here!

class CareerPath(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    title: str
    cluster: str
    description: str
    radar_weights: dict[str, float]
    tag_weights: dict[str, float]
    suggested_pathways: list[str]
    catalog_version: str = "career-catalog-v1"
    is_active: bool = True
    sort_order: int = 0

class StudyPath(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    title: str
    cluster: str
    description: str
    radar_weights: dict[str, float]
    tag_weights: dict[str, float]
    suggested_pathways: list[str]
    catalog_version: str = "career-catalog-v1"
    is_active: bool = True
    sort_order: int = 0

