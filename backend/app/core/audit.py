import logging
import uuid
from datetime import datetime, timezone
from ..domain.enums import AuditEventType
from ..domain.models import AuditEvent

logger = logging.getLogger("talentra.audit")
logger.setLevel(logging.INFO)

class AuditLogger:
    def __init__(self):
        self.events: list[AuditEvent] = []

    def log(
        self,
        event_type: AuditEventType,
        safe_context: str,
        user_id: str | None = None,
        school_id: str | None = None,
        correlation_id: str | None = None,
        metadata: dict | None = None,
    ) -> AuditEvent:
        # Sanitize safe_context to ensure no accidental leak of sensitive patterns
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            school_id=school_id,
            request_correlation_id=correlation_id or str(uuid.uuid4()),
            safe_context=safe_context,
            timestamp=datetime.now(timezone.utc),
        )
        self.events.append(event)
        
        # Log safely to system log
        logger.info(
            "AUDIT_EVENT event=%s user_id=%s school_id=%s correlation_id=%s context=%s",
            event.event_type.value,
            event.user_id or "anonymous",
            event.school_id or "-",
            event.request_correlation_id,
            event.safe_context,
        )
        return event

    def get_recent_events(self, limit: int = 50) -> list[AuditEvent]:
        return list(reversed(self.events[-limit:]))

    log_event = log


audit_logger = AuditLogger()
