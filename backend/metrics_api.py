from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
import models
from pydantic import BaseModel
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import security

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

class MetricsQuery(BaseModel):
    model_name: Optional[str] = None
    since_hours: Optional[int] = 24


@router.get("/metrics/generation")
def get_generation_metrics(model_name: Optional[str] = None, since_hours: int = 24, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
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


# Optional: raw listing endpoint
@router.get("/metrics/generation/raw")
def get_generation_metrics_raw(limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
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
