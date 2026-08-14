import os
from typing import Any, List

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))


QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_PREFIX = os.getenv("QDRANT_COLLECTION_PREFIX", "course")

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


def _collection_name(course_id: int) -> str:
    return f"{QDRANT_COLLECTION_PREFIX}_{course_id}"


def _get_dimensions() -> int:
    sample_vector = embeddings.embed_query("sample text")
    if isinstance(sample_vector, list):
        return len(sample_vector)
    return len(sample_vector[0]) if isinstance(sample_vector, list) and sample_vector and isinstance(sample_vector[0], list) else 768


def create_vector_store(documents: List[Document], course_id: int):
    collection_name = _collection_name(course_id)
    dimensions = _get_dimensions()

    if client.collection_exists(collection_name=collection_name):
        client.delete_collection(collection_name=collection_name)

    client.create_collection(
        collection_name=collection_name,
        vectors_config=qmodels.VectorParams(size=dimensions, distance=qmodels.Distance.COSINE),
        on_disk_payload=True,
    )

    points = []
    for index, document in enumerate(documents):
        page_content = document.page_content or ""
        metadata = getattr(document, "metadata", {}) or {}
        payload = {
            "text": page_content,
            **metadata,
        }
        vector = embeddings.embed_query(page_content)
        points.append(
            qmodels.PointStruct(
                id=index,
                vector=vector,
                payload=payload,
            )
        )

    if points:
        client.upsert(collection_name=collection_name, wait=True, points=points)

    return collection_name


def load_vector_store(course_id: int):
    collection_name = _collection_name(course_id)
    if not client.collection_exists(collection_name=collection_name):
        return None
    return client


def get_vector_client():
    return client
