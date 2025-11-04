# Research: RAG-Based Customer Support Chatbot

**Feature**: 001-rag-support-chatbot
**Date**: 2025-11-04
**Phase**: 0 (Outline & Research)

## Overview

This document captures research decisions and rationale for technology choices, integration patterns, and best practices for building a minimal RAG-based customer support chatbot.

---

## 1. Chunking Strategy

### Decision
**Use Chonkie library with TokenChunker (512 tokens, 128 overlap)**

### Rationale
- Lightweight RAG-specific library (released 2024-2025)
- Built-in tiktoken support for accurate token counting
- Simple 3-line API: `TokenChunker(tokenizer="cl100k_base", chunk_size=512, chunk_overlap=128)`
- Avoids heavy frameworks (LangChain adds 50+ dependencies)
- Matches spec requirement exactly: "512 tokens with 128 token overlap"

### Alternatives Considered
- **Custom tiktoken chunking** - More transparent (~30 lines) but Chonkie provides same functionality with better testing
- **LangChain RecursiveCharacterTextSplitter** - Too heavy (entire LangChain ecosystem)
- **semantic-text-splitter** - Character-based, not token-based

### Implementation
```python
from chonkie import TokenChunker

chunker = TokenChunker(
    tokenizer="cl100k_base",  # GPT-4 tokenizer
    chunk_size=512,
    chunk_overlap=128
)

chunks = chunker.chunk(document_text)
# Returns list of chunks with .text, .token_count, .start_index, .end_index
```

---

## 2. Document Parsing

### Decision
**Use pypdf for PDF extraction + built-in Python for TXT/MD**

### Rationale
- **pypdf**: Pure Python (no C compilation), most portable, actively maintained (2024-2025)
- Simple API: `PdfReader(path)` → `page.extract_text()`
- TXT/MD files: Use `Path(file_path).read_text()` (no dependency needed)
- Meets "self-hosted, minimal" requirement

### Alternatives Considered
- **pypdfium2** - Faster but requires C compilation (less portable)
- **pdftext** - Wrapper around pypdfium2, same portability issue
- **LlamaIndex SimpleDirectoryReader** - Heavy framework dependency
- **ChromaDB Data Pipes** - CLI-focused, unclear Python API

### Implementation
```python
from pathlib import Path
from pypdf import PdfReader

def load_document(file_path: str) -> str:
    path = Path(file_path)

    if path.suffix == ".pdf":
        reader = PdfReader(path)
        return "\n\n".join(page.extract_text() for page in reader.pages)
    elif path.suffix in [".txt", ".md"]:
        return path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")
```

---

## 3. Vector Store & Embeddings

### Decision
**ChromaDB with local sentence-transformers embeddings (BAAI/bge-small-en-v1.5)**

### Rationale
- **ChromaDB**: Self-hosted, persistent storage, simple API
- **Local embeddings**: Truly self-hosted (no API calls), faster (no network latency), free
- **BAAI/bge-small-en-v1.5**: Better quality than default all-MiniLM-L6-v2, still lightweight
- Cosine similarity metric for easier threshold interpretation (>0.7)

### Alternatives Considered
- **OpenRouter embeddings** - Originally in spec but violates "self-hosted" requirement
- **OpenAI text-embedding-3-small** - API cost, requires internet
- **Default all-MiniLM-L6-v2** - Lower quality

### Implementation
```python
import chromadb
from chromadb.utils import embedding_functions

sentence_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-en-v1.5"
)

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="support_docs",
    embedding_function=sentence_ef,
    metadata={"hnsw:space": "cosine"}  # Cosine distance for similarity
)

# Query: top-3 with >0.7 similarity threshold
results = collection.query(query_texts=[user_query], n_results=3)
filtered_docs = [
    doc for doc, dist in zip(results['documents'][0], results['distances'][0])
    if (1 - dist) > 0.7  # Cosine: similarity = 1 - distance
]
```

---

## 4. LLM Integration & Tool Calling

### Decision
**PydanticAI with OpenAI-compatible agent + Pydantic-native tool definitions**

### Rationale
- **Constitution-aligned**: Principle III mandates "Pydantic MUST be used for validation and schema enforcement"
- **Type-safe tool definitions**: Pydantic models for tool parameters (auto-validation)
- **Minimal overhead**: Single dependency (`pydantic-ai`), thin abstraction over OpenAI SDK
- **Works with OpenRouter**: OpenAI-compatible model specification
- **Less boilerplate**: ~30% less code than manual JSON schema + dispatch logic
- **Built-in conversation support**: Handles message history natively
- **Fail-fast compatible**: Exceptions still bubble up (no forced error handling)

### Alternatives Considered
- **Direct OpenAI SDK** - More transparent but violates Pydantic-first principle; requires manual JSON schemas and tool dispatch (~50 lines vs ~20 with PydanticAI)
- **OpenAI Assistants API** - Thread/run model adds complexity for simple chat
- **LangGraph** - Heavy framework (50+ dependencies), overkill for basic tool calling
- **LlamaIndex agents** - Overlaps with ChromaDB choice

### Implementation
```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
import uuid
from datetime import datetime

# Pydantic models for type safety (constitution-compliant)
class SupportTicket(BaseModel):
    ticket_id: str
    timestamp: str
    customer_message: str
    status: str = "open"
    conversation_context: list[dict] | None = None

# Initialize PydanticAI agent
agent = Agent(
    model="openai:gpt-4o",  # Works with OpenRouter via OPENAI_BASE_URL
    system_prompt="""You are a support chatbot. Use the knowledge base context provided
    to answer questions. If you cannot answer, offer to create a support ticket."""
)

@agent.tool
def submit_ticket(ctx: RunContext, message: str, include_conversation: bool = True) -> str:
    """Submit a support ticket for human assistance."""
    ticket = SupportTicket(
        ticket_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow().isoformat() + "Z",
        customer_message=message,
        conversation_context=ctx.messages if include_conversation else None
    )

    with open("tickets.jsonl", "a") as f:
        f.write(ticket.model_dump_json() + "\n")

    return f"Ticket {ticket.ticket_id} created successfully."

@agent.tool
def find_ticket(ctx: RunContext, query: str) -> str:
    """Find tickets by ID or content search."""
    with open("tickets.jsonl", "r") as f:
        tickets = [SupportTicket.model_validate_json(line) for line in f]

    matches = [t for t in tickets
               if query in t.ticket_id or query.lower() in t.customer_message.lower()]

    if not matches:
        return "No tickets found matching your query."

    return f"Found {len(matches)} tickets: " + ", ".join(t.ticket_id for t in matches)

# Usage in Streamlit
result = agent.run_sync(user_message)
```

---

## 5. Ticket Storage

### Decision
**JSON Lines (.jsonl) with append-only writes, fail-fast on corruption**

### Rationale
- Simple format: one ticket per line, easy to parse
- Append-only: atomic writes, no file locking complexity
- Fail-fast POC: No error recovery if file corrupted/missing
- Unique IDs via UUID4 or timestamp-based generation

### Alternatives Considered
- **SQLite** - Overkill for POC, adds database dependency
- **JSON array** - Requires full file rewrite on each append
- **CSV** - Poor support for nested conversation_context field

### Implementation
```python
import json
import uuid
from pathlib import Path
from datetime import datetime

def submit_ticket(message: str, conversation_context: list[dict] | None = None) -> str:
    ticket_id = str(uuid.uuid4())
    ticket = {
        "ticket_id": ticket_id,
        "timestamp": datetime.utcnow().isoformat(),
        "customer_message": message,
        "status": "open",
        "conversation_context": conversation_context or []
    }

    # Fail-fast: no error handling
    with open("tickets.jsonl", "a") as f:
        f.write(json.dumps(ticket) + "\n")

    return ticket_id

def find_ticket(query: str) -> list[dict]:
    # Fail-fast: assume file exists
    with open("tickets.jsonl", "r") as f:
        tickets = [json.loads(line) for line in f]

    # Simple search: match query in ticket_id or customer_message
    return [t for t in tickets if query in t["ticket_id"] or query.lower() in t["customer_message"].lower()]
```

---

## 6. Streamlit UI Pattern

### Decision
**Native Streamlit chat components (st.chat_message, st.chat_input) with session state**

### Rationale
- Built-in chat UI components (no custom React needed)
- Session state for conversation history: `st.session_state.messages`
- Typing indicators via `st.spinner()`
- Minimal dependencies (just Streamlit)

### Best Practices
- Store conversation history in `st.session_state.messages` (list of dicts)
- Display all messages on each rerun (Streamlit pattern)
- Use `st.chat_input()` for user input (returns value on submit)
- Show assistant responses with `st.chat_message("assistant").write(text)`

### Implementation
```python
import streamlit as st

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User input
if prompt := st.chat_input("Ask a question..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # RAG retrieval + LLM response
    with st.spinner("Thinking..."):
        response = generate_response(prompt)

    # Add assistant message
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)
```

---

## 7. Configuration Management

### Decision
**Pydantic Settings with .env file**

### Rationale
- Pydantic validation for environment variables (constitution requirement)
- `python-dotenv` for .env file loading
- Type-safe config access

### Implementation
```python
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        env="OPENAI_BASE_URL"
    )
    openai_model: str = Field(
        default="openai/gpt-4o",
        env="OPENAI_MODEL"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

---

## Summary of Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Chunking** | Chonkie (TokenChunker) | Lightweight, token-accurate, RAG-optimized |
| **PDF Parsing** | pypdf | Pure Python, portable, minimal |
| **Vector DB** | ChromaDB (persistent) | Self-hosted, simple API |
| **Embeddings** | sentence-transformers (bge-small) | Local, self-hosted, good quality |
| **LLM Agent** | PydanticAI | Pydantic-native, constitution-aligned (Principle III) |
| **Tool Calling** | PydanticAI @agent.tool decorator | Type-safe, less boilerplate than raw OpenAI SDK |
| **Ticket Storage** | JSON Lines (.jsonl) | Simple, append-only, fail-fast |
| **UI** | Streamlit (chat components) | Minimal, built-in chat support |
| **Config** | Pydantic Settings + .env | Type-safe, constitution-compliant |

**Total Dependencies**: 7 core packages (chromadb, pydantic-ai, chonkie, sentence-transformers, streamlit, pypdf, python-dotenv)

**Implementation Estimate**: ~230 lines of code for complete POC (30 lines saved with PydanticAI vs manual tool dispatch)
