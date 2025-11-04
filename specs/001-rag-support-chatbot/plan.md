# Implementation Plan: RAG-Based Customer Support Chatbot

**Branch**: `001-rag-support-chatbot` | **Date**: 2025-11-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-rag-support-chatbot/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a minimal, self-hosted RAG-based customer support chatbot using Streamlit for the UI. The system retrieves relevant content from a ChromaDB vector store (top-3 chunks, >0.7 similarity threshold) and uses OpenAI-compatible LLM API (via OpenRouter) to generate answers. Supports LLM tool calling for basic ticket management (submit_ticket, find_ticket) with JSON Lines storage. Documents are indexed offline via Python script using Chonkie for token-based chunking (512 tokens, 128 overlap).

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**:
- `chromadb` (^0.4.0) - Vector database for semantic search
- `pydantic-ai` (^0.0.14) - LLM agent framework with Pydantic-native tools (OpenRouter compatible)
- `chonkie[tiktoken]` (^0.5.0) - Token-based text chunking
- `sentence-transformers` (^2.2.0) - Local embeddings for ChromaDB
- `streamlit` (^1.28.0) - Web UI framework
- `pypdf` (^3.17.0) - PDF text extraction
- `python-dotenv` (^1.0.0) - Environment configuration

**Storage**:
- ChromaDB persistent storage (./chroma_db directory)
- JSON Lines file (tickets.jsonl) for ticket storage
- No database required

**Testing**: pytest (POC - tests not required per constitution)
**Target Platform**: Local development (macOS/Linux), single-instance deployment
**Project Type**: Single project with Streamlit UI + indexing script
**Performance Goals**:
- Query response <5 seconds
- Document indexing <10 minutes per 10-page PDF
- Support 10 concurrent chat sessions

**Constraints**:
- Self-hosted only (no cloud dependencies except OpenRouter API)
- Fail-fast error handling (no recovery in POC)
- Minimal dependencies (7 core packages)
- Top-3 retrieval with >0.7 similarity threshold

**Scale/Scope**:
- POC for single knowledge base
- No multi-tenancy
- No authentication
- ~100-500 document chunks expected

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pipeline-First Architecture (Principle I)
**Status**: ❌ NOT APPLICABLE
**Rationale**: This feature is a standalone Streamlit chatbot, not a Dagster pipeline. The constitution states "Every feature MUST integrate into the Dagster pipeline architecture" but this RAG chatbot is a separate application. No bronze/silver/gold medallion pattern applies.
**Resolution**: Feature operates independently of existing Dagster infrastructure. Future integration possible but not required for POC.

### Code Quality Gates (Principle II)
**Status**: ✅ PASS
**Compliance**:
- Pre-commit hooks will enforce `ruff format`, `ruff check --fix`, `ty check`
- `make check` required before commits
- Tests NOT required per POC policy

### Type Safety & Validation (Principle III)
**Status**: ✅ PASS
**Compliance**:
- Python 3.12+ type hints for public functions
- Pydantic for environment config (.env validation)
- Pydantic for LLM tool schemas (submit_ticket, find_ticket)
- `ty` type checker zero errors required

### Observability & Experiment Tracking (Principle IV)
**Status**: ⚠️ PARTIAL (Acceptable for POC)
**Compliance**:
- No MLflow tracking (POC exception)
- `structlog` for basic logging (INFO/WARNING/ERROR levels)
- Constitution allows "SHOULD" not "MUST" for POC

### Dependency Management (Principle V)
**Status**: ✅ PASS
**Compliance**:
- `pyproject.toml` as single source of truth
- `uv sync` for reproducible environments
- `.env` for external service configuration (OPENAI_API_KEY, OPENAI_BASE_URL)

### Coding Standards & Pragmatism (Principle VI)
**Status**: ✅ PASS
**Compliance**:
- No docstrings required (POC)
- Minimal `__init__.py` usage
- All imports at top of files
- Idiomatic Python (context managers, list comprehensions)
- Divide and conquer architecture (document_loader.py + chunking via Chonkie + streamlit_app.py)
- Fail-fast error handling (no recovery in POC)

**Overall Gate Status**: ✅ PASS (with Pipeline-First exception noted)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
customer_support/
├── src/
│   ├── document_loader.py      # PDF/TXT/MD file loading
│   ├── indexing_script.py      # Offline ChromaDB indexing
│   ├── ticket_manager.py       # Submit/find ticket tools
│   └── streamlit_app.py        # Main chatbot UI
│
├── tests/
│   └── unit/                    # Optional for POC
│
├── documents/                   # Knowledge base documents (PDF/TXT/MD)
├── chroma_db/                   # ChromaDB persistent storage (gitignored)
├── tickets.jsonl                # Support tickets (gitignored)
│
├── .env.example                 # Environment template
├── .env                         # Local config (gitignored)
├── pyproject.toml               # Dependencies
├── Makefile                     # Quality checks
└── README.md                    # Setup instructions
```

**Structure Decision**: Single project (Option 1) selected. This is a standalone Streamlit application with minimal components:
- **src/document_loader.py** - Handles PDF/TXT/MD file reading (~20 lines)
- **src/indexing_script.py** - Chunks documents with Chonkie and indexes to ChromaDB (~50 lines)
- **src/ticket_manager.py** - PydanticAI agent with tool decorators for ticket operations (~30 lines)
- **src/streamlit_app.py** - Main UI with RAG retrieval + PydanticAI agent integration (~130 lines)

Total implementation: ~230 lines of code for complete POC (30 lines saved with PydanticAI vs manual tool dispatch).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Pipeline-First Architecture (Principle I) | RAG chatbot is standalone Streamlit app, not a data processing pipeline | Forcing Dagster integration would add unnecessary complexity (Dagster assets for chat UI) and violates "minimal" POC requirement. Future integration possible if chatbot becomes part of larger data workflow. |

**Justification**: The constitution's pipeline-first principle applies to data processing features. This is an interactive application (chat UI) that consumes processed data (ChromaDB vectors) but doesn't produce pipeline assets. The fail-fast POC approach prioritizes validating RAG + tool calling mechanics over architectural purity.
