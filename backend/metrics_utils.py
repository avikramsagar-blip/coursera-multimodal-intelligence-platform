import time
from database import SessionLocal
import models
from sqlalchemy.exc import SQLAlchemyError

# Utility to record generation metrics using an independent DB session
def record_generation_metric(
    model_name: str,
    prompt_snippet: str | None = None,
    prompt_hash: str | None = None,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    latency_ms: float | None = None,
    success: bool = True,
    error: str | None = None,
    retrieval_id: int | None = None,
    insight_id: int | None = None,
):
    db = SessionLocal()
    try:
        m = models.GenerationMetric(
            model_name=model_name,
            prompt_snippet=(prompt_snippet[:1000] if prompt_snippet is not None else None),
            prompt_hash=prompt_hash,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            success=success,
            error=error,
            retrieval_id=retrieval_id,
            insight_id=insight_id
        )
        db.add(m)
        db.commit()
        db.refresh(m)
        return m.metric_id
    except SQLAlchemyError:
        db.rollback()
        return None
    finally:
        db.close()
