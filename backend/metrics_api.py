from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from backend.database import get_db
import backend.models as models
from pydantic import BaseModel
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import backend.security as security

router = APIRouter()
security_scheme = HTTPBearer()

# local get_current_user re-used from evidence_api pattern
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    email = security.verify_access_token(token)
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Role requirement factory: returns a dependency that enforces allowed roles
def require_roles(allowed_roles: list):
    def _require(current_user: models.User = Depends(get_current_user)):
        user_role = (current_user.role or "").lower()
        allowed = [r.lower() for r in allowed_roles]
        if user_role not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return _require

class MetricsQuery(BaseModel):
    model_name: Optional[str] = None
    since_hours: Optional[int] = 24


@router.get("/metrics/generation")
def get_generation_metrics(model_name: Optional[str] = None, since_hours: int = 24, db: Session = Depends(get_db), current_user: models.User = Depends(require_roles(["ops", "admin", "reviewer"]))):
    since = datetime.utcnow() - timedelta(hours=since_hours)
    q = db.query(models.GenerationMetric).filter(models.GenerationMetric.created_at >= since)
    if model_name:
        q = q.filter(models.GenerationMetric.model_name == model_name)

    rows = q.order_by(models.GenerationMetric.created_at.desc()).limit(1000).all()

    total = len(rows)
    if total == 0:
        return {
            "total": 0,
            "avg_latency_ms": None,
            "success_rate": None,
            "errors": []
        }

    latencies = [r.latency_ms for r in rows if r.latency_ms is not None]
    successes = sum(1 for r in rows if r.success)
    errors = [ {"metric_id": r.metric_id, "error": r.error} for r in rows if (r.success is False and r.error) ]

    avg_latency = (sum(latencies) / len(latencies)) if latencies else None
    success_rate = successes / total

    return {
        "total": total,
        "avg_latency_ms": avg_latency,
        "success_rate": success_rate,
        "errors": errors,
        "recent": [
            {
                "metric_id": r.metric_id,
                "model_name": r.model_name,
                "latency_ms": r.latency_ms,
                "created_at": r.created_at,
                "success": r.success,
                "error": r.error
            } for r in rows[:50]
        ]
    }


@router.get("/metrics/dashboard")
def get_metrics_dashboard(db: Session = Depends(get_db), current_user: models.User = Depends(require_roles(["ops", "admin"]))):
    # Aggregate metrics per model_name
    q = db.query(models.GenerationMetric).order_by(models.GenerationMetric.created_at.desc())
    rows = q.all()
    from collections import defaultdict
    agg = defaultdict(list)
    for r in rows:
        agg[r.model_name].append(r)

    out = []
    for model_name, items in agg.items():
        total = len(items)
        latencies = [it.latency_ms for it in items if it.latency_ms is not None]
        tokens_in = [it.tokens_in for it in items if it.tokens_in is not None]
        tokens_out = [it.tokens_out for it in items if it.tokens_out is not None]
        successes = sum(1 for it in items if it.success)
        last_seen = max(it.created_at for it in items)
        out.append({
            "model_name": model_name,
            "total_calls": total,
            "avg_latency_ms": (sum(latencies)/len(latencies)) if latencies else None,
            "success_rate": successes/total if total else None,
            "avg_tokens_in": (sum(tokens_in)/len(tokens_in)) if tokens_in else None,
            "avg_tokens_out": (sum(tokens_out)/len(tokens_out)) if tokens_out else None,
            "last_seen": last_seen
        })

    return {"models": out}


# Optional: raw listing endpoint
@router.get("/metrics/generation/raw")
def get_generation_metrics_raw(limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(require_roles(["ops", "admin", "reviewer"]))):
    rows = db.query(models.GenerationMetric).order_by(models.GenerationMetric.created_at.desc()).limit(limit).all()
    return [{
        "metric_id": r.metric_id,
        "model_name": r.model_name,
        "prompt_snippet": r.prompt_snippet,
        "tokens_in": r.tokens_in,
        "tokens_out": r.tokens_out,
        "latency_ms": r.latency_ms,
        "success": r.success,
        "error": r.error,
        "created_at": r.created_at
    } for r in rows]
