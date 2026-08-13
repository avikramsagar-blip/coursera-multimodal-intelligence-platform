"""
Evaluation helpers for RAG: Faithfulness and Retrieval Recall using Gemini as an LLM judge.

This module provides two functions:
 - evaluate_faithfulness(answer, retrieved_context, question)
 - evaluate_retrieval_recall(retrieved_docs, question)

Both functions call Gemini (using the GEMINI_API_KEY from environment)
and request a JSON reply with keys: score (0-100 or null) and reason (short string).

If evaluation fails for any reason, they return {"score": None, "reason": "Evaluation unavailable"}

Implementation notes:
 - Keep prompts conservative and explicitly ask the model to output a strict JSON object.
 - Truncate long contexts to avoid exceeding token limits while keeping useful content.
 - Parsing is defensive: try JSON.parse, else fallback to extracting a first integer and the rest as reason.
"""

import os
import json
import re
from typing import List, Dict, Any

from dotenv import load_dotenv
import google.genai as genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
_client = genai.Client(api_key=API_KEY)

# Maximum characters of context/chunk text to include in judge prompt to avoid huge prompts
_MAX_CHUNK_TEXT = 800
_MAX_TOTAL_CONTEXT = 4000


def _safe_parse_json(text: str) -> Dict[str, Any]:
    """Attempt to parse JSON from LLM reply. Fall back to best-effort extraction.

    Returns dict with keys 'score' and 'reason'.
    """
    # Try direct JSON load
    try:
        obj = json.loads(text)
        # Normalize keys
        score = obj.get("score") if isinstance(obj.get("score"), (int, float)) else None
        reason = obj.get("reason") or obj.get("explanation") or ""
        # If score is percent as float 0-1 sometimes, convert
        if isinstance(score, float) and 0.0 <= score <= 1.0:
            score = int(round(score * 100))
        if isinstance(score, float):
            score = int(round(score))
        return {"score": score, "reason": str(reason)}
    except Exception:
        pass

    # Try to find first integer between 0 and 100
    m = re.search(r"(\d{1,3})", text)
    score = None
    if m:
        try:
            n = int(m.group(1))
            if 0 <= n <= 100:
                score = n
        except Exception:
            score = None

    # Reason: use the remaining text after the number or whole text
    reason = text.strip()
    if score is not None:
        # remove the first matched number from reason for brevity
        reason = re.sub(r"\b" + re.escape(str(score)) + r"\b", "", reason, count=1).strip()

    # Truncate reason
    if len(reason) > 400:
        reason = reason[:400] + "..."

    return {"score": score, "reason": reason or ""}


# -------------------------------
# Faithfulness evaluation
# -------------------------------

def evaluate_faithfulness(answer: str, retrieved_context: str, question: str) -> Dict[str, Any]:
    """Judge whether the answer is grounded in the retrieved_context.

    Returns {"score": int|None, "reason": str} where score is 0-100.

    Uses the Gemini model as a judge and requests a strict JSON reply.

    The prompt asks the model to compare the answer with the provided context and to
    score how well the factual claims in the answer are supported by the context.
    """

    if not API_KEY:
        return {"score": None, "reason": "Evaluation unavailable"}

    # Truncate context to a safe size (keep the start and end if needed)
    ctx = (retrieved_context or "")
    if len(ctx) > _MAX_TOTAL_CONTEXT:
        ctx = ctx[: _MAX_TOTAL_CONTEXT // 2] + "\n...\n" + ctx[-_MAX_TOTAL_CONTEXT // 2 :]

    prompt = f"""
You are an objective evaluator. Given a user question, the retrieved course context, and an AI-generated answer, judge whether the answer's factual claims are grounded in the retrieved context.

Return a JSON object ONLY with keys: score (integer 0-100) and reason (short explanation).

Question:
{question}

Retrieved context (provided to the model during generation):
{ctx}

AI answer:
{answer}

Evaluation rubric (use to determine score):
- 100: Every factual claim in the answer is explicitly supported by the retrieved context.
- 75-99: Most claims are supported; minor unsupported or ambiguous statements.
- 50-74: Some important claims are unsupported or contradicted by the context.
- 1-49: Majority of claims are unsupported or contradicted.
- 0: Answer contains fabricated facts not present in context or contradicts it.

Provide only a JSON object. Keep reason concise (1-2 sentences).
"""

    try:
        resp = _client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        text = resp.text if hasattr(resp, "text") else str(resp)
        return _safe_parse_json(text)
    except Exception:
        return {"score": None, "reason": "Evaluation unavailable"}


# -------------------------------
# Retrieval recall evaluation
# -------------------------------

def evaluate_retrieval_recall(retrieved_docs: List[Any], question: str) -> Dict[str, Any]:
    """Judge whether the retrieved chunks contain sufficient information to answer the question.

    retrieved_docs is expected to be a list of objects with attributes "page_content" and "metadata".
    The function truncates and formats the chunks for the prompt.

    Returns {"score": int|None, "reason": str}.
    """

    if not API_KEY:
        return {"score": None, "reason": "Evaluation unavailable"}

    if not retrieved_docs:
        return {"score": None, "reason": "No retrieved chunks"}

    # Build a concise listing of retrieved chunks (id + snippet + metadata)
    parts = []
    for i, d in enumerate(retrieved_docs, start=1):
        content = getattr(d, "page_content", "") if hasattr(d, "page_content") else d.get("page_content", "")
        md = getattr(d, "metadata", {}) if hasattr(d, "metadata") else d.get("metadata", {})
        snippet = content[:_MAX_CHUNK_TEXT].replace("\n", " ")
        parts.append(f"CHUNK {i}: {snippet} | METADATA: {md}")

    ctx = "\n\n".join(parts)

    # Truncate overall ctx
    if len(ctx) > _MAX_TOTAL_CONTEXT:
        ctx = ctx[:_MAX_TOTAL_CONTEXT // 2] + "\n...\n" + ctx[-_MAX_TOTAL_CONTEXT // 2 :]

    prompt = f"""
You are an objective evaluator. Given a user question and a list of retrieved chunks (text snippets with metadata), judge whether the retrieved chunks together contain sufficient information for an accurate answer.

Return a JSON object ONLY with keys: score (integer 0-100) and reason (short explanation).

Question:
{question}

Retrieved chunks (top candidate snippets):
{ctx}

Scoring guidance:
- 100: The chunks include explicit, specific information that fully answers the question.
- 75-99: Most required information is present, minor gaps remain.
- 50-74: Useful information is present but key facts are missing.
- 1-49: Retrieved chunks are mostly irrelevant or insufficient.
- 0: No relevant information present in retrieved chunks.

Provide only a JSON object. Keep reason concise (1-2 sentences).
"""

    try:
        resp = _client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        text = resp.text if hasattr(resp, "text") else str(resp)
        return _safe_parse_json(text)
    except Exception:
        return {"score": None, "reason": "Evaluation unavailable"}
