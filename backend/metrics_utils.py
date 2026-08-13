import os
import hashlib
import time
from database import SessionLocal
import models
from sqlalchemy.exc import SQLAlchemyError

REDACT_PROMPT = os.getenv("METRICS_REDACT_PROMPT", "true").lower() in ("1", "true", "yes")
SANITIZE_PROMPT = os.getenv("METRICS_SANITIZE_PROMPT", "true").lower() in ("1", "true", "yes")

import re


def sanitize_prompt(text: str) -> str:
    """Sanitize a prompt by redacting common PII patterns.

    Replacements:
    - Emails => <REDACTED_EMAIL>
    - URLs => <REDACTED_URL>
    - UUIDs => <REDACTED_UUID>
    - Long digit sequences (8+ digits) => <REDACTED_NUMBER>
    - Credit-card-like sequences (13-19 digits) => <REDACTED_NUMBER>
    - Phone-like sequences => <REDACTED_PHONE>

    The function returns the sanitized text.
    """
    if not text:
        return text

    s = text

    # Emails
    s = re.sub(r"[\w\.-]+@[\w\.-]+\.[A-Za-z]{2,}", "<REDACTED_EMAIL>", s)

    # URLs (http/https)
    s = re.sub(r"https?://\S+", "<REDACTED_URL>", s)
    s = re.sub(r"www\.\S+", "<REDACTED_URL>", s)

    # UUIDs
    s = re.sub(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b", "<REDACTED_UUID>", s)

    # Credit card like sequences (13 to 19 digits with optional separators)
    s = re.sub(r"\b(?:\d[ -]*?){13,19}\b", "<REDACTED_NUMBER>", s)

    # Phone numbers (simple heuristic)
    s = re.sub(r"\+?\d[\d\-\s]{7,}\d", "<REDACTED_PHONE>", s)

    # Long pure digit sequences (8+)
    s = re.sub(r"\b\d{8,}\b", "<REDACTED_NUMBER>", s)

    # Trim excessive whitespace
    s = re.sub(r"\s+", " ", s).strip()

    return s


# Utility to record generation metrics using an independent DB session
# Accepts raw_prompt for hashing/redaction and maintains backward-compatible prompt_snippet
def extract_token_usage(response) -> tuple[int|None, int|None]:
    """Try multiple response fields to extract prompt and completion token counts.

    Returns (tokens_in, tokens_out) where either value may be None if not available.
    """
    if response is None:
        return None, None

    # Common locations
    possible = []
    try:
        if hasattr(response, "token_usage"):
            possible.append(response.token_usage)
    except Exception:
        pass
    try:
        if hasattr(response, "usage"):
            possible.append(response.usage)
    except Exception:
        pass
    try:
        # google genai sometimes stores metadata dict
        if hasattr(response, "metadata") and isinstance(response.metadata, dict):
            possible.append(response.metadata.get("token_usage") or response.metadata.get("usage") or response.metadata)
    except Exception:
        pass
    try:
        if hasattr(response, "candidates") and isinstance(response.candidates, (list, tuple)) and len(response.candidates) > 0:
            cand = response.candidates[0]
            if hasattr(cand, "metadata") and isinstance(cand.metadata, dict):
                possible.append(cand.metadata.get("token_usage") or cand.metadata.get("usage"))
    except Exception:
        pass

    for p in possible:
        if not p:
            continue
        # p may be a dict-like object
        try:
            # dict-like access
            if isinstance(p, dict):
                # try common keys
                prompt_tokens = p.get("prompt_tokens") or p.get("prompt") or p.get("input_tokens")
                completion_tokens = p.get("completion_tokens") or p.get("generated_tokens") or p.get("completion")
                total_tokens = p.get("total_tokens") or p.get("tokens")
                if prompt_tokens is not None or completion_tokens is not None:
                    return (int(prompt_tokens) if prompt_tokens is not None else None,
                            int(completion_tokens) if completion_tokens is not None else None)
                if total_tokens is not None:
                    return (None, int(total_tokens))
        except Exception:
            pass
    return None, None


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
    # Sanitize prompt if enabled
    sanitized = None
    if raw_prompt is not None:
        sanitized = sanitize_prompt(raw_prompt) if SANITIZE_PROMPT else raw_prompt

    # Compute hash if not provided (hash the sanitized value)
    computed_hash = prompt_hash
    if sanitized and not computed_hash:
        h = hashlib.sha256()
        h.update(sanitized.encode("utf-8"))
        computed_hash = h.hexdigest()

    # Decide whether to store prompt snippet based on REDACT_PROMPT
    stored_snippet = None
    if not REDACT_PROMPT:
        if prompt_snippet is not None:
            # sanitize snippet too if needed
            stored_snippet = sanitize_prompt(prompt_snippet)[:1000] if SANITIZE_PROMPT else prompt_snippet[:1000]
        elif sanitized is not None:
            stored_snippet = sanitized[:1000]

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
