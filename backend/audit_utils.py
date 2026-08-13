from typing import Optional
import json
from datetime import datetime

# Lazy imports to avoid import-time DB requirements

def record_audit(actor_id: Optional[int], action_type: str, target_type: Optional[str] = None,
                 target_id: Optional[int] = None, details: Optional[str] = None):
    """Record an audit log entry. Best-effort: failures are swallowed to avoid breaking callers.

    actor_id: user_id of the actor performing the action
    action_type: short string action
    target_type: type of the target ("insight", "user", ...)
    target_id: id of the target entity
    details: optional JSON/text with additional context
    """
    try:
        from backend.database import SessionLocal
        import backend.models as models
        db = SessionLocal()
        entry = models.AuditLog(
            actor_id=actor_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            details=details
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        db.close()
        return entry.audit_id
    except Exception:
        # swallow/logging could be added; keep best-effort
        try:
            db.close()
        except Exception:
            pass
        return None
