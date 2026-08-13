import os
import hashlib
import time
from database import SessionLocal
import models
from sqlalchemy.exc import SQLAlchemyError

REDACT_PROMPT = os.getenv("METRICS_REDACT_PROMPT", "true").lower() in ("1", "true", "yes")

# Utility to record generation metrics using an independent DB session
# Accepts raw_prompt for hashing/redaction and maintains backward-compatible prompt_snippet
def record_generation_metric(
    model_name: str,
    raw_prompt: str | None = None,
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
    # Compute hash if not provided
    computed_hash = prompt_hash
    if raw_prompt and not computed_hash:
        h = hashlib.sha256()
        h.update(raw_prompt.encode("utf-8"))
        computed_hash = h.hexdigest()

    # Decide whether to store prompt snippet based on REDACT_PROMPT
    stored_snippet = None
    if not REDACT_PROMPT:
        if prompt_snippet is not None:
            stored_snippet = prompt_snippet[:1000]
        elif raw_prompt is not None:
            stored_snippet = raw_prompt[:1000]

    db = SessionLocal()
    try:
        m = models.GenerationMetric(
            model_name=model_name,
            prompt_snippet=stored_snippet,
            prompt_hash=computed_hash,
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
