import os
import hashlib
import time

REDACT_PROMPT = os.getenv("METRICS_REDACT_PROMPT", "true").lower() in ("1", "true", "yes")
SANITIZE_PROMPT = os.getenv("METRICS_SANITIZE_PROMPT", "true").lower() in ("1", "true", "yes")

# Extra sanitization patterns can be provided via env:
# METRICS_SANITIZE_EXTRA = "pattern1:::REPL1;pattern2:::REPL2"
EXTRA_PATTERNS_RAW = os.getenv("METRICS_SANITIZE_EXTRA", "")
EXTRA_PATTERNS = []
if EXTRA_PATTERNS_RAW:
    for part in EXTRA_PATTERNS_RAW.split(';'):
        if ':::' in part:
            pat, repl = part.split(':::', 1)
            try:
                EXTRA_PATTERNS.append((re.compile(pat), repl))
            except Exception:
                # ignore invalid patterns
                pass

import re
from cryptography.fernet import Fernet, InvalidToken

ENCRYPT_PROMPT = os.getenv("METRICS_ENCRYPT_PROMPT", "false").lower() in ("1", "true", "yes")
FERNET_KEY = os.getenv("METRICS_ENCRYPTION_KEY")
FERNET = None
if ENCRYPT_PROMPT and FERNET_KEY:
    try:
        FERNET = Fernet(FERNET_KEY.encode() if isinstance(FERNET_KEY, str) else FERNET_KEY)
    except Exception:
        FERNET = None


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

    # Apply extra patterns
    for (pattern, repl) in EXTRA_PATTERNS:
        try:
            s = pattern.sub(repl, s)
        except Exception:
            pass

    return s


# Encryption helpers
def encrypt_text(plain: str) -> str | None:
    if not plain:
        return None
    if not ENCRYPT_PROMPT or not FERNET:
        return None
    try:
        token = FERNET.encrypt(plain.encode('utf-8'))
        return token.decode('utf-8')
    except Exception:
        return None


def decrypt_text(token: str) -> str | None:
    if not token:
        return None
    if not ENCRYPT_PROMPT or not FERNET:
        return None
    try:
        plain = FERNET.decrypt(token.encode('utf-8'))
        return plain.decode('utf-8')
    except (InvalidToken, Exception):
        return None


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

    # Optionally encrypt stored snippet
    if ENCRYPT_PROMPT and stored_snippet and FERNET:
        try:
            encrypted = encrypt_text(stored_snippet)
            if encrypted:
                stored_snippet = encrypted
        except Exception:
            pass

    # Lazy import of DB dependencies to keep the module importable in test-only environments
    try:
        from backend.database import SessionLocal
        import backend.models as models
        from sqlalchemy.exc import SQLAlchemyError
    except Exception:
        # If DB or SQLAlchemy isn't available (e.g., in lightweight test env), skip writing metrics
        return None

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
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return None
    finally:
        try:
            db.close()
        except Exception:
            pass
