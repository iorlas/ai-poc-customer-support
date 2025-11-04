# Quickstart: RAG-Based Customer Support Chatbot

**Feature**: 001-rag-support-chatbot
**Date**: 2025-11-04
**Phase**: 1 (Design & Contracts)

## Overview

This quickstart guide provides step-by-step instructions to get the RAG-based customer support chatbot running locally.

---

## Prerequisites

- **Python 3.12+** installed
- **uv** package manager (or pip)
- **Git** (for cloning repository)
- **OpenRouter API key** (or other OpenAI-compatible API)

---

## Installation

### 1. Clone Repository

```bash
cd /path/to/customer_support
git checkout 001-rag-support-chatbot
```

### 2. Install Dependencies

Using `uv` (recommended):
```bash
uv sync
```

Using `pip`:
```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```bash
# OpenAI-compatible API Configuration
OPENAI_API_KEY=your_openrouter_api_key_here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o

# Optional: Adjust model if needed
# OPENAI_MODEL=anthropic/claude-3-5-sonnet
```

---

## Usage

### Step 1: Index Documents

Place your knowledge base documents in the `documents/` directory:

```bash
mkdir -p documents/
cp /path/to/your/faq.pdf documents/
cp /path/to/your/policies.md documents/
```

Run the indexing script:

```bash
uv run python src/indexing_script.py
```

**Expected output:**
```
Loading documents from ./documents...
Loaded 3 documents: faq.pdf, policies.md, guide.txt
Chunking documents...
Created 47 chunks
Indexing to ChromaDB...
Indexed 3 documents with 47 chunks to ChromaDB
ChromaDB collection 'support_docs' ready at ./chroma_db
```

**Troubleshooting:**
- **No documents found**: Ensure files have `.pdf`, `.txt`, or `.md` extensions
- **PDF parsing error**: Check if PDF is text-based (not scanned image)
- **Embedding download**: First run will download sentence-transformers model (~80MB)

---

### Step 2: Launch Chatbot

Start the Streamlit application:

```bash
uv run streamlit run src/streamlit_app.py
```

**Expected output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501
```

Open your browser to `http://localhost:8501`

---

## Using the Chatbot

### Basic Q&A

1. Type a question in the chat input: *"What are your business hours?"*
2. The chatbot will:
   - Query ChromaDB for relevant chunks (top-3, >0.7 similarity)
   - Generate an answer using the LLM based on retrieved context
   - Display the response

**Example interaction:**
```
User: What are your business hours?
Assistant: Based on our documentation, we are open Monday through Friday, 9:00 AM to 5:00 PM EST. We are closed on weekends and major holidays.
```

### Creating a Ticket

If the chatbot can't answer your question:

```
User: I need help with my order #12345
Assistant: I couldn't find relevant information about your specific order. Let me create a support ticket for you.
[Calls submit_ticket tool]
Assistant: I've created ticket 123e4567-e89b-12d3-a456-426614174000 for your request. A human agent will review your order issue shortly.
```

**What happened:**
1. PydanticAI agent detected it couldn't answer from knowledge base
2. Invoked `submit_ticket` tool via @agent.tool decorator
3. Pydantic SupportTicket model validated and serialized
4. Ticket saved to `tickets.jsonl`
5. Returned confirmation to user

### Finding Tickets

```
User: Show me my tickets
Assistant: [Calls find_ticket tool with empty query]
Assistant: I found 2 tickets:
1. Ticket 123e4567... (created 2025-11-04): "I need help with my order #12345"
2. Ticket 789abcde... (created 2025-11-03): "Billing question"
```

**Search by ID:**
```
User: Find ticket 123e4567
Assistant: [Calls find_ticket with specific ID]
Assistant: Here's your ticket:
- ID: 123e4567-e89b-12d3-a456-426614174000
- Created: 2025-11-04T12:34:56Z
- Message: "I need help with my order #12345"
- Status: Open
```

---

## Verification

### Check ChromaDB Index

Verify documents are indexed:

```bash
uv run python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('support_docs')
print(f'Collection has {collection.count()} chunks')
"
```

**Expected output:**
```
Collection has 47 chunks
```

### Check Tickets File

View submitted tickets:

```bash
cat tickets.jsonl
```

**Expected output:**
```json
{"ticket_id": "123e4567-e89b-12d3-a456-426614174000", "timestamp": "2025-11-04T12:34:56Z", "customer_message": "I need help with my order #12345", "status": "open", "conversation_context": [...]}
```

---

## Common Issues

### 1. OpenRouter API Error

**Error:** `openai.AuthenticationError: 401 Unauthorized`

**Solution:** Check your `OPENAI_API_KEY` in `.env` file. Verify it's valid at https://openrouter.ai/keys

### 2. No Relevant Results Found

**Symptom:** Chatbot always says "I couldn't find relevant information"

**Causes:**
- No documents indexed (run `indexing_script.py`)
- Similarity threshold too high (>0.7 may be strict for small knowledge bases)
- Documents don't contain relevant information

**Debug:**
```python
# Test query directly
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('support_docs')
results = collection.query(query_texts=["business hours"], n_results=3)
print(results)
```

### 3. ChromaDB Embedding Download Fails

**Error:** `URLError: <urlopen error [Errno 60] Operation timed out>`

**Solution:** The first run downloads the embedding model. Ensure internet connection, or manually download:

```bash
uv run python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-small-en-v1.5')
"
```

### 4. Streamlit Port Already in Use

**Error:** `OSError: [Errno 48] Address already in use`

**Solution:** Specify a different port:
```bash
uv run streamlit run src/streamlit_app.py --server.port 8502
```

---

## Development Workflow

### Re-indexing Documents

After adding/updating documents:

```bash
# Remove old index
rm -rf chroma_db/

# Re-run indexing
uv run python src/indexing_script.py
```

### Clearing Tickets

Reset ticket storage:

```bash
rm tickets.jsonl
```

### Code Quality Checks

Before committing:

```bash
make check
```

Runs:
1. `ruff format` - Format code
2. `ruff check --fix` - Lint and auto-fix
3. `ty check` - Type check

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│ User (Browser)                                      │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│ Streamlit UI (streamlit_app.py)                     │
│ - Chat interface (st.chat_message, st.chat_input)   │
│ - Session state (conversation history)              │
│ - RAG retrieval (ChromaDB query)                    │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│ PydanticAI Agent (ticket_manager.py)                │
│ - Agent with @agent.tool decorators                 │
│ - Pydantic models for validation                    │
│ - OpenRouter API integration                        │
└──────┬────────────────────────────────────┬─────────┘
       │                                    │
       ▼                                    ▼
┌──────────────────┐              ┌────────────────────┐
│ ChromaDB         │              │ OpenRouter API     │
│ - Query chunks   │              │ - LLM chat         │
│ - Top-3, >0.7    │              │ - Tool calling     │
│ - Cosine sim     │              │ via PydanticAI     │
└──────────────────┘              └─────────┬──────────┘
                                            │
                                            ▼
                                  ┌─────────────────────┐
                                  │ Tools (Pydantic)    │
                                  │ - @agent.tool       │
                                  │ - submit_ticket()   │
                                  │ - find_ticket()     │
                                  │ - tickets.jsonl     │
                                  └─────────────────────┘
```

**Offline Indexing Pipeline:**
```
documents/
    │
    ▼
document_loader.py (load PDF/TXT/MD)
    │
    ▼
Chonkie TokenChunker (512 tokens, 128 overlap)
    │
    ▼
ChromaDB (embed + store in ./chroma_db)
```

---

## Next Steps

1. **Add More Documents**: Place PDFs/TXT/MD files in `documents/` and re-index
2. **Customize System Prompt**: Edit `streamlit_app.py` to adjust chatbot personality
3. **Tune Retrieval**: Adjust `n_results` (top-k) or similarity threshold (>0.7)
4. **Experiment with Models**: Try different LLMs via `OPENAI_MODEL` in `.env`
5. **View Tickets**: Build a simple admin interface to view `tickets.jsonl` (future enhancement)

---

## Support

For issues or questions:
- Check [research.md](./research.md) for technology decisions
- Review [data-model.md](./data-model.md) for entity definitions
- See [contracts/tool-schemas.json](./contracts/tool-schemas.json) for tool specifications
- Run `/speckit.tasks` to generate implementation tasks
