from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from database import get_db
from sqlalchemy.orm import Session
import models
import security
from datetime import datetime

router = APIRouter()
security_scheme = HTTPBearer()

# local get_current_user
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    email = security.verify_access_token(token)
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def admin_required(current_user: models.User = Depends(get_current_user)):
    if (current_user.role or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user


class RoleUpdate(BaseModel):
    role: str


@router.post("/admin/users/{user_id}/role")
def set_user_role(user_id: int, payload: RoleUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(admin_required)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = user.role
    user.role = payload.role
    db.commit()
    db.refresh(user)

    # Audit role change
    try:
        from audit_utils import record_audit
        details = f"old_role={old_role};new_role={payload.role}"
        record_audit(actor_id=current_user.user_id, action_type="role_change", target_type="user", target_id=user.user_id, details=details)
    except Exception:
        pass

    return {"user_id": user.user_id, "role": user.role}


@router.get('/admin/audits')
def list_audits(limit: int = 100, since_hours: int = 24, db: Session = Depends(get_db), current_user: models.User = Depends(admin_required)):
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(hours=since_hours)
    rows = db.query(models.AuditLog).filter(models.AuditLog.created_at >= since).order_by(models.AuditLog.created_at.desc()).limit(limit).all()
    out = []
    for r in rows:
        out.append({
            'audit_id': r.audit_id,
            'actor_id': r.actor_id,
            'action_type': r.action_type,
            'target_type': r.target_type,
            'target_id': r.target_id,
            'details': r.details,
            'created_at': r.created_at
        })
    return {'audits': out}
