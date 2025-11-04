import chromadb
from chromadb.utils import embedding_functions

from src.models import RetrievalResult


def get_chroma_client(persist_directory: str = "./chroma_db") -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=persist_directory)


def get_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    sentence_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="BAAI/bge-small-en-v1.5")

    return client.get_or_create_collection(
        name="support_docs",
        embedding_function=sentence_ef,
        metadata={"hnsw:space": "cosine"},
    )


def query_documents(query: str, n_results: int = 3, similarity_threshold: float = 0.7) -> list[RetrievalResult]:
    client = get_chroma_client()
    collection = get_collection(client)

    results = collection.query(query_texts=[query], n_results=n_results)

    retrieval_results = []
    for doc, dist, meta in zip(results["documents"][0], results["distances"][0], results["metadatas"][0]):
        similarity = 1 - dist
        if similarity > similarity_threshold:
            retrieval_results.append(RetrievalResult(text=doc, distance=dist, similarity=similarity, metadata=meta))

    return retrieval_results
