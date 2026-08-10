from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def split_text(pages, source_name):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    documents = []

    for page_data in pages:

        page_text = page_data["text"]
        page_number = page_data["page"]

        chunks = splitter.split_text(page_text)

        for chunk_index, chunk in enumerate(chunks):

            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": source_name,
                        "page": page_number,
                        "chunk": chunk_index + 1
                    }
                )
            )

    return documents