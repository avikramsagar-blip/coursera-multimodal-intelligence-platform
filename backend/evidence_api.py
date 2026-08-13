from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter()

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


@router.post("/retrievals")
def create_retrieval(payload: RetrievalIn, db: Session = Depends(get_db)):
    rec = models.RetrievalRecord(
        query=payload.query,
        user_id=payload.user_id,
        retriever=payload.retriever,
        metadata=str(payload.metadata) if payload.metadata is not None else None
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"retrieval_id": rec.retrieval_id}


@router.post("/evidence/bulk")
def create_evidence_bulk(items: List[EvidenceIn], db: Session = Depends(get_db)):
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
            metadata=str(it.metadata) if it.metadata is not None else None
        )
        db.add(ev)
        db.flush()
        created_ids.append(ev.evidence_id)
    db.commit()
    return {"evidence_ids": created_ids}


@router.post("/insights", response_model=InsightOut)
def create_insight(payload: InsightCreate, db: Session = Depends(get_db)):
    # Create insight record
    insight = models.Insight(
        title=payload.title,
        summary=payload.summary,
        generated_by_model_id=payload.generated_by_model_id,
        created_by=payload.created_by
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
            metadata=str(ev.metadata) if ev.metadata is not None else None
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
def get_insight_evidence(insight_id: int, db: Session = Depends(get_db)):
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
            "metadata": ev.metadata,
            "score": l.score,
            "retrieval_id": l.retrieval_id
        })

    return {"insight_id": insight_id, "evidence": evidence_list}
