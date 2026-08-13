import os
import importlib
import sys
import unittest

# Ensure the backend package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class MetricsUtilsTest(unittest.TestCase):
    def setUp(self):
        # Remove module if already loaded to force re-import with env changes
        if 'metrics_utils' in sys.modules:
            del sys.modules['metrics_utils']

    def test_sanitize_email_url_phone_card(self):
        import metrics_utils
        # Email
        s = "Contact: john.doe@example.com"
        out = metrics_utils.sanitize_prompt(s)
        self.assertIn("<REDACTED_EMAIL>", out)

        # URL
        s2 = "Visit http://example.com/path"
        out2 = metrics_utils.sanitize_prompt(s2)
        self.assertIn("<REDACTED_URL>", out2)

        # Phone
        s3 = "Call me at +1 555-123-4567"
        out3 = metrics_utils.sanitize_prompt(s3)
        self.assertIn("<REDACTED_PHONE>", out3)

        # Card-like number
        s4 = "Card 4111 1111 1111 1111"
        out4 = metrics_utils.sanitize_prompt(s4)
        self.assertIn("<REDACTED_NUMBER>", out4)

    def test_extra_patterns_env(self):
        # Set extra pattern and reload module
        os.environ['METRICS_SANITIZE_EXTRA'] = r"SECRET(\d+):::<SNUM>"
        if 'metrics_utils' in sys.modules:
            del sys.modules['metrics_utils']
        import metrics_utils
        importlib.reload(metrics_utils)
        s = "This is SECRET12345 in text"
        out = metrics_utils.sanitize_prompt(s)
        self.assertIn("<SNUM>", out)
        # cleanup
        del os.environ['METRICS_SANITIZE_EXTRA']

    def test_encrypt_decrypt(self):
        # enable encryption
        try:
            from cryptography.fernet import Fernet
        except Exception:
            self.skipTest('cryptography not available')

        key = Fernet.generate_key().decode('utf-8')
        os.environ['METRICS_ENCRYPT_PROMPT'] = 'true'
        os.environ['METRICS_ENCRYPTION_KEY'] = key

        if 'metrics_utils' in sys.modules:
            del sys.modules['metrics_utils']
        import metrics_utils
        importlib.reload(metrics_utils)

        plain = 'Hello john.doe@example.com and visit http://x.com'
        sanitized = metrics_utils.sanitize_prompt(plain)
        enc = metrics_utils.encrypt_text(sanitized)
        self.assertIsNotNone(enc)
        dec = metrics_utils.decrypt_text(enc)
        self.assertIsNotNone(dec)
        # decrypted should equal sanitized
        self.assertEqual(dec, sanitized)

        # cleanup
        del os.environ['METRICS_ENCRYPT_PROMPT']
        del os.environ['METRICS_ENCRYPTION_KEY']

if __name__ == '__main__':
    unittest.main()
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
