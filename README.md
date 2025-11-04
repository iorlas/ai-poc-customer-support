# Customer Support RAG Chatbot

A minimal, self-hosted RAG-based customer support chatbot using Streamlit for the UI.

## Quick Start

See the [quickstart guide](./specs/001-rag-support-chatbot/quickstart.md) for detailed setup instructions.

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenRouter API key
   ```

3. Index documents:
   ```bash
   # Place your documents (PDF, TXT, MD) in the documents/ directory
   uv run python -m src.indexing_script
   ```

4. Launch chatbot:
   ```bash
   # Option 1: Direct execution
   uv run streamlit run src/streamlit_app.py

   # Option 2: If you have issues with imports
   cd src && uv run streamlit run streamlit_app.py
   ```

## Features

### User Story 1: Basic Question Answering (MVP) ✅
- RAG-based semantic search using ChromaDB
- Top-3 document chunk retrieval with >0.7 similarity threshold
- OpenAI-compatible LLM integration via PydanticAI
- Streamlit chat interface with conversation history
- Structured logging with context tracking

## Architecture

- **ChromaDB**: Vector database for semantic search
- **PydanticAI**: LLM agent framework with tool calling
- **Chonkie**: Token-based text chunking (512 tokens, 128 overlap)
- **Streamlit**: Web UI framework
- **sentence-transformers**: Local embeddings (BAAI/bge-small-en-v1.5)

## Project Structure

```
src/
├── config.py           # Pydantic Settings for .env
├── models.py          # Core Pydantic models
├── document_loader.py # PDF/TXT/MD parsing
├── vector_store.py    # ChromaDB + RAG retrieval
├── logging_config.py  # Structured logging setup
├── indexing_script.py # Document indexing CLI
└── streamlit_app.py   # Main chatbot UI
```

## License

MIT
