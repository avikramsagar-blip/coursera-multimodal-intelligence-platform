import os

from dotenv import load_dotenv
from fastapi import HTTPException
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

BASE_DIR = os.path.dirname(__file__)
embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)


def search_chunks(course_id, question, k=10):
    from backend.vector_store import client, _collection_name

    collection_name = _collection_name(course_id)
    if not client.collection_exists(collection_name=collection_name):
        raise HTTPException(
            status_code=404,
            detail=(
                f"Vector database not found for course {course_id}. "
                "Run /generate-vector-db/{course_id} to create the index."
            )
        )

    query_vector = embeddings.embed_query(question)
    hits = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=k,
        with_payload=True,
        with_vectors=False,
    )

    docs = []
    for hit in hits:
        payload = hit.payload or {}
        docs.append(
            Document(
                page_content=payload.get("text", ""),
                metadata={
                    key: value for key, value in payload.items() if key != "text"
                },
            )
        )

    return docs