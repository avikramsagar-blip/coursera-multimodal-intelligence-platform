import os
import shutil

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


def create_vector_store(documents, course_id):

    folder = os.path.join(
        BASE_DIR,
        "faiss_indexes",
        f"course_{course_id}"
    )

    if os.path.exists(folder):
        shutil.rmtree(folder)

    os.makedirs(
        folder,
        exist_ok=True
    )

    db = FAISS.from_documents(
        documents=documents,
        embedding=embeddings
    )

    db.save_local(folder)

    return folder


def load_vector_store(course_id):

    folder = os.path.join(
        BASE_DIR,
        "faiss_indexes",
        f"course_{course_id}"
    )

    if not os.path.exists(folder):
        return None

    db = FAISS.load_local(
        folder,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return db