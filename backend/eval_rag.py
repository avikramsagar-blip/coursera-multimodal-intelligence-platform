"""
eval_rag.py — Standalone RAG retrieval evaluation script.

PURPOSE
-------
Measures retrieval quality of the existing FAISS index for course 1.
Reports Recall@10 and Precision@5 for three question categories:
  - PDF / course-material questions
  - Video transcript questions
  - Missing-answer questions

IMPORTANT CONSTRAINTS
---------------------
- Does NOT call Gemini for answer generation (no API quota used).
- Does NOT modify any production file.
- Does NOT invent ground-truth answers from outside knowledge.
- Relevance labels are defined ONLY from observable chunk metadata
  (source filename, page number, chunk index) and keyword presence
  in the actual retrieved chunk text.
- Where ground truth cannot be reliably established from the index
  alone, the metric is explicitly reported as "not reliably measurable"
  rather than fabricated.

HOW TO RUN
----------
From the backend/ directory:

    cd backend
    python eval_rag.py

The script loads the FAISS index for course_id=1 and prints a
structured report to stdout. No server needs to be running.

GROUND-TRUTH METHODOLOGY
-------------------------
Relevance is determined by two observable signals — no external
knowledge is used:

  1. SOURCE MATCH  — the retrieved chunk's metadata["source"] contains
     the expected PDF filename (for PDF questions) or equals "video"
     (for video questions).

  2. KEYWORD MATCH — at least one of the question's key domain terms
     appears in the chunk text (case-insensitive). Key terms are listed
     explicitly per test case below so the labelling rule is auditable.

A chunk is labelled RELEVANT only when BOTH signals are satisfied.
This is a conservative definition — it may undercount true positives
but it never fabricates relevance.

For MISSING-ANSWER questions the expected behaviour is that NO chunk
in the top-10 satisfies both signals. Recall@10 and Precision@5 are
therefore "not reliably measurable" for this category (there is no
positive ground-truth chunk to recall), but we report how many chunks
were retrieved and whether any appear superficially relevant.
"""

import os
import sys

# ---------------------------------------------------------------------------
# Path setup — allow running from repo root or from backend/
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv

load_dotenv(
    dotenv_path=os.path.join(SCRIPT_DIR, "..", ".env")
)

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
COURSE_ID = 1
FAISS_FOLDER = os.path.join(
    SCRIPT_DIR,
    "faiss_indexes",
    f"course_{COURSE_ID}"
)
K_RETRIEVAL = 10   # candidates fetched from FAISS
K_PRECISION = 5    # top-N used for Precision@K


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------
# Each test case is a dict with:
#   question        : str   — the retrieval query (same as production)
#   category        : str   — "pdf" | "video" | "missing"
#   expected_source : str   — substring that must appear in metadata["source"]
#                             for a chunk to be source-relevant.
#                             For video chunks this is the literal "video".
#                             For missing-answer cases this is None.
#   key_terms       : list  — domain words that must appear in chunk text
#                             (at least one) for a chunk to be term-relevant.
#                             Derived from the question and known PDF titles.
#   notes           : str   — explains why these terms were chosen.
# ---------------------------------------------------------------------------
TEST_CASES = [
    {
        "question": "What does the Central Limit Theorem state?",
        "category": "pdf",
        "expected_source": "Statistics",
        "key_terms": [
            "central limit theorem",
            "central limit",
            "clt",
            "sampling distribution",
            "normal distribution",
            "sample mean",
        ],
        "notes": (
            "The CLT is covered in the Statistics PDFs. "
            "A relevant chunk must come from a Statistics PDF "
            "AND contain CLT-related terminology."
        ),
    },
    {
        "question": "What does the FastAPI video explain?",
        "category": "video",
        "expected_source": "video",
        "key_terms": [
            "fastapi",
            "api",
            "endpoint",
            "route",
            "http",
            "request",
            "response",
            "python",
        ],
        "notes": (
            "A relevant chunk must have source='video' AND contain "
            "FastAPI-related terms from the actual transcript."
        ),
    },
    {
        "question": "Which language is used in Power Query?",
        "category": "missing",
        "expected_source": None,
        "key_terms": [
            "power query",
            "m language",
            "m formula",
            "query language",
        ],
        "notes": (
            "The PowerBI PDF contains the question but not the answer. "
            "Recall@10 and Precision@5 are not reliably measurable here "
            "because there is no known positive chunk in the index. "
            "We report retrieval behaviour only."
        ),
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_index():
    """Load the FAISS index. Exits with a clear message if not found."""
    if not os.path.exists(FAISS_FOLDER):
        print(
            f"\n[ERROR] FAISS index not found at: {FAISS_FOLDER}"
            "\nGenerate it first via POST /generate-vector-db/1"
        )
        sys.exit(1)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(
            "\n[ERROR] GEMINI_API_KEY not set in .env"
            "\nThe embedding model is needed to encode the query."
        )
        sys.exit(1)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        google_api_key=api_key
    )

    db = FAISS.load_local(
        FAISS_FOLDER,
        embeddings,
        allow_dangerous_deserialization=True
    )
    return db


def is_relevant(doc, expected_source, key_terms):
    """
    Returns (bool, str) — (is_relevant, reason).

    A chunk is relevant when BOTH conditions hold:
      1. metadata["source"] contains expected_source (case-insensitive)
      2. page_content contains at least one key_term (case-insensitive)

    For missing-answer cases (expected_source is None) always returns
    (False, "missing-answer: no positive ground truth").
    """
    if expected_source is None:
        return False, "missing-answer: no positive ground truth"

    source = str(doc.metadata.get("source", "")).lower()
    content = doc.page_content.lower()

    source_match = expected_source.lower() in source
    matched_term = next(
        (t for t in key_terms if t.lower() in content),
        None
    )
    term_match = matched_term is not None

    if source_match and term_match:
        return True, f"source='{source}' term='{matched_term}'"
    if not source_match:
        return False, f"source mismatch: got '{source}'"
    return False, f"no key term found in chunk"


def recall_at_k(relevant_flags):
    """
    Recall@K = (relevant chunks found in top-K) / (total relevant in top-K).

    Because we cannot enumerate ALL relevant chunks in the full index
    (we only have the retrieved set), we use a bounded definition:
      Recall@K = number of relevant chunks in top-K / K

    This is more precisely "relevant rate @K". We label it clearly in
    the report to avoid implying we know the full relevant set size.
    """
    if not relevant_flags:
        return 0.0
    return sum(relevant_flags) / len(relevant_flags)


def precision_at_k(relevant_flags, k):
    """Precision@K = relevant in top-K / K."""
    top_k = relevant_flags[:k]
    if not top_k:
        return 0.0
    return sum(top_k) / len(top_k)


def separator(char="=", width=60):
    return char * width


# ---------------------------------------------------------------------------
# Main evaluation loop
# ---------------------------------------------------------------------------

def run_evaluation():
    print(separator())
    print("  RAG RETRIEVAL EVALUATION — Course", COURSE_ID)
    print(f"  FAISS folder : {FAISS_FOLDER}")
    print(f"  K retrieval  : {K_RETRIEVAL}")
    print(f"  K precision  : {K_PRECISION}")
    print(separator())

    print("\nLoading FAISS index (requires one Gemini embedding call per")
    print("question to encode the query — no generation calls made)...\n")

    db = load_index()

    results_summary = []

    for case_num, case in enumerate(TEST_CASES, start=1):

        question = case["question"]
        category = case["category"]
        expected_source = case["expected_source"]
        key_terms = case["key_terms"]

        print(separator("-"))
        print(f"TEST {case_num} — {category.upper()}")
        print(f"Question : {question}")
        print(f"Category : {category}")
        print(f"Notes    : {case['notes']}")
        print()

        # Retrieve
        docs = db.similarity_search(query=question, k=K_RETRIEVAL)

        print(f"Retrieved {len(docs)} chunks from FAISS (k={K_RETRIEVAL})")
        print()

        # Label each chunk
        relevant_flags = []
        for i, doc in enumerate(docs):
            rel, reason = is_relevant(doc, expected_source, key_terms)
            relevant_flags.append(1 if rel else 0)

            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", "-")
            chunk = doc.metadata.get("chunk", "-")
            preview = doc.page_content[:120].replace("\n", " ")

            label = "RELEVANT" if rel else "       -"
            print(
                f"  [{i+1:02d}] {label} | "
                f"source={source} page={page} chunk={chunk}"
            )
            print(f"        reason : {reason}")
            print(f"        preview: {preview}")
            print()

        # Compute metrics
        if category == "missing":
            print("  Recall@10  : not reliably measurable")
            print("               (no positive ground-truth chunk exists)")
            print("  Precision@5: not reliably measurable")
            print("               (no positive ground-truth chunk exists)")
            superficially_relevant = sum(
                1 for doc in docs
                if any(t.lower() in doc.page_content.lower() for t in key_terms)
            )
            print(
                f"  Chunks containing a key term (surface match): "
                f"{superficially_relevant}/{len(docs)}"
            )
            print(
                "  Expected behaviour: Gemini should reply "
                "'I don't know from the course material.'"
            )
            results_summary.append({
                "test": case_num,
                "category": category,
                "question": question,
                "recall_at_10": "N/A",
                "precision_at_5": "N/A",
                "surface_matches": superficially_relevant,
            })

        else:
            r10 = recall_at_k(relevant_flags)
            p5 = precision_at_k(relevant_flags, K_PRECISION)
            total_relevant = sum(relevant_flags)

            print(
                f"  Relevant chunks in top-{K_RETRIEVAL}: "
                f"{total_relevant}/{len(docs)}"
            )
            print(
                f"  Recall@{K_RETRIEVAL}   : {r10:.2f}  "
                f"(relevant/{K_RETRIEVAL} — bounded definition, see docstring)"
            )
            print(
                f"  Precision@{K_PRECISION} : {p5:.2f}  "
                f"(relevant in top-{K_PRECISION} / {K_PRECISION})"
            )

            results_summary.append({
                "test": case_num,
                "category": category,
                "question": question,
                "recall_at_10": f"{r10:.2f}",
                "precision_at_5": f"{p5:.2f}",
                "relevant_in_top10": total_relevant,
            })

        print()

    # Final summary table
    print(separator())
    print("  SUMMARY")
    print(separator())
    print(
        f"  {'#':<4} {'Category':<10} "
        f"{'Recall@10':<12} {'Precision@5':<13} Question"
    )
    print(separator("-"))
    for r in results_summary:
        print(
            f"  {r['test']:<4} {r['category']:<10} "
            f"{r['recall_at_10']:<12} {r['precision_at_5']:<13} "
            f"{r['question']}"
        )
    print(separator())
    print()
    print("INTERPRETATION GUIDE")
    print(separator("-"))
    print(
        "  Recall@10   — what fraction of the 10 retrieved chunks are relevant."
        "\n               1.00 = all 10 relevant. 0.00 = none relevant."
        "\n               NOTE: this is a bounded estimate, not true recall,"
        "\n               because the full set of relevant chunks in the index"
        "\n               is unknown without exhaustive labelling."
    )
    print()
    print(
        "  Precision@5 — what fraction of the top-5 chunks sent to Gemini"
        "\n               are relevant. 1.00 = all 5 relevant. 0.00 = none."
        "\n               This directly measures context quality for generation."
    )
    print()
    print(
        "  N/A         — metric cannot be reliably calculated because no"
        "\n               positive ground-truth chunk exists in the index"
        "\n               for this question (missing-answer case)."
    )
    print(separator())


if __name__ == "__main__":
    run_evaluation()
