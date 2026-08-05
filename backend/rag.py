import os

from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)


def search_chunks(course_id, question):

    folder = f"faiss_indexes/course_{course_id}"

    db = FAISS.load_local(
        folder,
        embeddings,
        allow_dangerous_deserialization=True
    )

    docs = db.similarity_search(
        question,
        k=4
    )

    return docs
