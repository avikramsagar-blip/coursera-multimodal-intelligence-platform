from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Any
from sqlalchemy.orm import Session
from database import get_db
import models
import security
from datetime import datetime

router = APIRouter()
security_scheme = HTTPBearer()

# Local dependency to get current user to avoid circular import with main
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
        # Normalize role names and allowed roles
        user_role = (current_user.role or "").lower()
        allowed = [r.lower() for r in allowed_roles]
        if user_role not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return _require

# Pydantic schemas
class EvidenceIn(BaseModel):
    source_type: str
    source_id: Optional[int] = None
    segment_id: Optional[int] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    snippet_text: Optional[str] = None
    source_uri: Optional[str] = None
    embedding_id: Optional[str] = None
    metadata: Optional[Any] = None
    score: Optional[float] = None
    retrieval_id: Optional[int] = None

class RetrievalIn(BaseModel):
    query: str
    user_id: Optional[int] = None
    retriever: Optional[str] = None
    metadata: Optional[Any] = None

class InsightCreate(BaseModel):
    title: Optional[str] = None
    summary: str
    generated_by_model_id: Optional[int] = None
    created_by: Optional[int] = None
    evidence: Optional[List[EvidenceIn]] = []

class InsightOut(BaseModel):
    insight_id: int
    status: str

class ReviewIn(BaseModel):
    action: str  # approved, rejected, request_changes
    notes: Optional[str] = None


@router.post("/retrievals")
def create_retrieval(payload: RetrievalIn, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    rec = models.RetrievalRecord(
        query=payload.query,
        user_id=payload.user_id or current_user.user_id,
        retriever=payload.retriever,
        metadata_json=str(payload.metadata) if payload.metadata is not None else None
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"retrieval_id": rec.retrieval_id}


@router.post("/evidence/bulk")
def create_evidence_bulk(items: List[EvidenceIn], db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    created_ids = []
    for it in items:
        ev = models.Evidence(
            source_type=it.source_type,
            source_id=it.source_id,
            segment_id=it.segment_id,
            start_time=it.start_time,
            end_time=it.end_time,
            snippet_text=it.snippet_text,
            source_uri=it.source_uri,
            embedding_id=it.embedding_id,
            metadata_json=str(it.metadata) if it.metadata is not None else None
        )
        db.add(ev)
        db.flush()
        created_ids.append(ev.evidence_id)
    db.commit()
    return {"evidence_ids": created_ids}


@router.post("/insights", response_model=InsightOut)
def create_insight(payload: InsightCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Create insight record
    insight = models.Insight(
        title=payload.title,
        summary=payload.summary,
        generated_by_model_id=payload.generated_by_model_id,
        created_by=payload.created_by or current_user.user_id
    )
    db.add(insight)
    db.flush()

    # Attach evidence
    for ev in payload.evidence or []:
        # If an evidence_id already exists in payload.metadata, user may have created earlier.
        created_evidence = models.Evidence(
            source_type=ev.source_type,
            source_id=ev.source_id,
            segment_id=ev.segment_id,
            start_time=ev.start_time,
            end_time=ev.end_time,
            snippet_text=ev.snippet_text,
            source_uri=ev.source_uri,
            embedding_id=ev.embedding_id,
            metadata_json=str(ev.metadata) if ev.metadata is not None else None
        )
        db.add(created_evidence)
        db.flush()

        link = models.InsightEvidence(
            insight_id=insight.insight_id,
            evidence_id=created_evidence.evidence_id,
            retrieval_id=ev.retrieval_id,
            score=ev.score
        )
        db.add(link)

    db.commit()
    db.refresh(insight)

    return InsightOut(insight_id=insight.insight_id, status=insight.status)


@router.get("/insights/{insight_id}/evidence")
def get_insight_evidence(insight_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    insight = db.query(models.Insight).filter(models.Insight.insight_id == insight_id).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    links = db.query(models.InsightEvidence).filter(models.InsightEvidence.insight_id == insight_id).all()
    evidence_list = []
    for l in links:
        ev = db.query(models.Evidence).filter(models.Evidence.evidence_id == l.evidence_id).first()
        if not ev:
            continue
        evidence_list.append({
            "evidence_id": ev.evidence_id,
            "source_type": ev.source_type,
            "source_id": ev.source_id,
            "segment_id": ev.segment_id,
            "start_time": ev.start_time,
            "end_time": ev.end_time,
            "snippet_text": ev.snippet_text,
            "source_uri": ev.source_uri,
            "embedding_id": ev.embedding_id,
            "metadata": ev.metadata_json,
            "score": l.score,
            "retrieval_id": l.retrieval_id
        })

    return {"insight_id": insight_id, "evidence": evidence_list}


@router.get("/insights")
def list_insights(status: Optional[str] = None, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    q = db.query(models.Insight)
    if status:
        q = q.filter(models.Insight.status == status)
    insights = q.order_by(models.Insight.created_at.desc()).limit(100).all()
    out = []
    for ins in insights:
        out.append({
            "insight_id": ins.insight_id,
            "title": ins.title,
            "summary": ins.summary,
            "status": ins.status,
            "created_at": ins.created_at,
            "reviewed_by": ins.reviewed_by,
            "reviewed_at": ins.reviewed_at
        })
    return {"insights": out}


@router.post("/insights/{insight_id}/review")
def review_insight(insight_id: int, payload: ReviewIn, db: Session = Depends(get_db), current_user: models.User = Depends(require_roles(["reviewer", "admin", "ops"]))):
    insight = db.query(models.Insight).filter(models.Insight.insight_id == insight_id).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    action = payload.action.lower()
    if action not in {"approved", "rejected", "request_changes", "approve", "reject"}:
        raise HTTPException(status_code=400, detail="Invalid review action")

    # Normalize action
    if action == "approve":
        action = "approved"
    if action == "reject":
        action = "rejected"

    # Create review record
    review = models.Review(
        insight_id=insight.insight_id,
        reviewer_id=current_user.user_id,
        action=action,
        notes=payload.notes
    )
    db.add(review)

    # Update insight status and reviewed metadata
    prev_status = insight.status
    insight.status = "approved" if action == "approved" else ("rejected" if action == "rejected" else "pending_review")
    insight.reviewed_by = current_user.user_id
    insight.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(insight)

    # Audit the review action (best-effort)
    try:
        from audit_utils import record_audit
        details = f"action={action};notes={payload.notes};prev_status={prev_status};new_status={insight.status}"
        record_audit(actor_id=current_user.user_id, action_type="insight_review", target_type="insight", target_id=insight.insight_id, details=details)
    except Exception:
        pass

    return {"insight_id": insight.insight_id, "status": insight.status}
