from pathlib import Path

import chromadb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VECTOR_DB_PATH = PROJECT_ROOT / "vector_db"

client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
collection = client.get_collection("langchain")


def retrieve_documents(query: str, limit: int = 3) -> list[str]:
    results = collection.query(query_texts=[query], n_results=limit)
    documents = results.get("documents", [[]])[0]
    return list(dict.fromkeys(document for document in documents if document))
