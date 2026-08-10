import os
from dotenv import load_dotenv
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings
)
from langchain_community.vectorstores import FAISS
load_dotenv()
BASE_DIR = os.path.dirname(__file__)
embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)
def search_chunks(course_id, question, k=5):

    folder = os.path.join(
        BASE_DIR,
        "faiss_indexes",
        f"course_{course_id}"
    )

    if not os.path.exists(folder):

        raise FileNotFoundError(
            f"Vector database not found for course {course_id}"
        )

    db = FAISS.load_local(
        folder,
        embeddings,
        allow_dangerous_deserialization=True
    )

    docs = db.similarity_search(
        query=question,
        k=k
    )

    print("=== RAG RETRIEVAL DEBUG ===")
    print(
        f"similarity_search returned: {len(docs)} docs"
    )

    for i, doc in enumerate(docs):

        print(f"\nEvidence {i + 1}")

        print(
            f"Source: "
            f"{doc.metadata.get('source', 'Unknown')}"
        )

        print(
            f"Page: "
            f"{doc.metadata.get('page', 'Unknown')}"
        )

        print(
            f"Chunk: "
            f"{doc.metadata.get('chunk', 'Unknown')}"
        )

        print(
            f"Content: "
            f"{doc.page_content[:300]}"
        )

    print("=== END RAG RETRIEVAL DEBUG ===")

    return docs