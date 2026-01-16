import re
from pathlib import Path

from chonkie import TokenChunker

from src.document_loader import load_document
from src.logging_config import get_logger, setup_logging
from src.vector_store import get_chroma_client, get_collection

setup_logging()
logger = get_logger(__name__)

# Pattern to extract URL from HTML comment: <!-- Source: URL -->
SOURCE_URL_PATTERN = re.compile(r"<!--\s*Source:\s*(https?://[^\s>]+)\s*-->")


def extract_source_url(content: str) -> str:
    """Extract source URL from document content.

    Looks for HTML comment in format: <!-- Source: https://... -->

    Returns:
        The extracted URL or empty string if not found.
    """
    match = SOURCE_URL_PATTERN.search(content)
    return match.group(1) if match else ""


def index_documents(documents_dir: str = "./documents") -> None:
    logger.info("Starting document indexing", documents_dir=documents_dir)

    doc_path = Path(documents_dir)
    if not doc_path.exists():
        logger.error("Documents directory not found", path=documents_dir)
        raise FileNotFoundError(f"Documents directory not found: {documents_dir}")

    document_files = list(doc_path.glob("*.pdf")) + list(doc_path.glob("*.txt")) + list(doc_path.glob("*.md"))

    if not document_files:
        logger.warning("No documents found to index", path=documents_dir)
        return

    logger.info("Found documents to index", count=len(document_files))

    chunker = TokenChunker(tokenizer="cl100k_base", chunk_size=512, chunk_overlap=128)

    client = get_chroma_client()
    collection = get_collection(client)

    total_chunks = 0

    for doc_file in document_files:
        logger.info("Processing document", file=str(doc_file))

        text_content = load_document(str(doc_file))
        source_url = extract_source_url(text_content)
        chunks = chunker.chunk(text_content)

        chunk_ids = [f"{doc_file.name}_chunk_{i}" for i in range(len(chunks))]
        chunk_texts = [chunk.text for chunk in chunks]
        chunk_metadatas = [
            {
                "source": doc_file.name,
                "url": source_url,
                "start_index": chunk.start_index,
                "token_count": chunk.token_count,
            }
            for chunk in chunks
        ]

        collection.add(ids=chunk_ids, documents=chunk_texts, metadatas=chunk_metadatas)

        total_chunks += len(chunks)
        logger.info("Indexed document", file=doc_file.name, chunks=len(chunks))

    logger.info("Indexing complete", total_documents=len(document_files), total_chunks=total_chunks)


if __name__ == "__main__":
    index_documents()
