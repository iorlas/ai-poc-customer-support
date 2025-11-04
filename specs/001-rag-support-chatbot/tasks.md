# Tasks: RAG-Based Customer Support Chatbot

**Input**: Design documents from `/specs/001-rag-support-chatbot/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT required per POC policy (constitution allows omitting tests for POC features).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- All source code in `src/` directory
- Documents in `documents/` directory
- ChromaDB storage in `chroma_db/` directory (gitignored)
- Tickets storage in `tickets.jsonl` file (gitignored)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Update pyproject.toml with dependencies: chromadb ^0.4.0, pydantic-ai ^0.0.14, chonkie[tiktoken] ^0.5.0, sentence-transformers ^2.2.0, streamlit ^1.28.0, pypdf ^3.17.0, python-dotenv ^1.0.0
- [X] T002 Create .env.example with OPENAI_API_KEY, OPENAI_BASE_URL (https://openrouter.ai/api/v1), OPENAI_MODEL (openai/gpt-4o)
- [X] T003 [P] Create src/ directory structure
- [X] T004 [P] Create documents/ directory for knowledge base files
- [X] T005 [P] Update .gitignore to exclude chroma_db/, tickets.jsonl, .env

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create Pydantic Settings configuration in src/config.py with OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL validation
- [X] T007 [P] Create Pydantic models in src/models.py: Message, Document, SupportTicket with validation per data-model.md
- [X] T008 [P] Implement document_loader.py in src/ with load_document() function supporting PDF (pypdf), TXT, MD formats
- [X] T009 Initialize ChromaDB client with sentence-transformers embedding (BAAI/bge-small-en-v1.5) in src/vector_store.py
- [X] T010 [P] Setup logging with structlog in src/logging_config.py (INFO/WARNING/ERROR levels)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic Question Answering (Priority: P1) 🎯 MVP

**Goal**: Customer can ask questions and receive accurate answers grounded in the knowledge base documents.

**Independent Test**: Load sample knowledge base with FAQs, ask a question covered in the documents, verify chatbot returns accurate information from those documents.

### Implementation for User Story 1

- [X] T011 [US1] Implement indexing_script.py in src/ with Chonkie TokenChunker (512 tokens, 128 overlap) to chunk documents and index to ChromaDB
- [X] T012 [US1] Implement RAG retrieval function in src/vector_store.py: query_documents(query: str) -> list[RetrievalResult] with top-3, >0.7 similarity threshold
- [X] T013 [US1] Create streamlit_app.py in src/ with basic Streamlit chat interface (st.chat_message, st.chat_input)
- [X] T014 [US1] Implement session state management in src/streamlit_app.py for conversation history (st.session_state.messages)
- [X] T015 [US1] Integrate RAG retrieval into streamlit_app.py: query ChromaDB → filter by similarity → format as LLM context
- [X] T016 [US1] Initialize PydanticAI agent in src/streamlit_app.py with system prompt for support chatbot role
- [X] T017 [US1] Implement LLM response generation in src/streamlit_app.py with retrieved context and conversation history
- [X] T018 [US1] Add typing indicators (st.spinner) and response display in src/streamlit_app.py

**Checkpoint**: At this point, User Story 1 should be fully functional - customer can ask questions and get answers from knowledge base

---

## Phase 4: User Story 2 - Multi-Turn Conversation (Priority: P2)

**Goal**: Customer can engage in conversation with follow-up questions, and chatbot maintains context for coherent responses.

**Independent Test**: Initiate a conversation, ask an initial question, then ask 2-3 follow-up questions that reference previous context, verify chatbot maintains conversational coherence.

### Implementation for User Story 2

- [X] T019 [US2] Update PydanticAI agent in src/streamlit_app.py to include conversation history in LLM prompts
- [X] T020 [US2] Implement context window management in src/streamlit_app.py to limit message history to reasonable token count
- [X] T021 [US2] Add conversation context to RAG retrieval in src/streamlit_app.py to improve query understanding
- [X] T022 [US2] Test multi-turn conversation flows and verify context preservation across turns

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - basic Q&A and multi-turn conversations both functional

---

## Phase 5: User Story 3 - Graceful Failure Handling (Priority: P2)

**Goal**: When chatbot cannot find relevant information or is uncertain, it communicates this clearly and offers alternatives.

**Independent Test**: Ask questions not covered in knowledge base, ask ambiguous questions, test edge cases, verify chatbot responds appropriately without fabricating answers.

### Implementation for User Story 3

- [ ] T023 [US3] Update system prompt in src/streamlit_app.py to handle low-confidence scenarios and communicate limitations
- [ ] T024 [US3] Implement similarity threshold checking in src/streamlit_app.py to detect when no relevant documents found (all results <0.7)
- [ ] T025 [US3] Add fallback responses in src/streamlit_app.py for no-match scenarios offering to create ticket or contact human
- [ ] T026 [US3] Implement ambiguity detection in src/streamlit_app.py to trigger clarifying questions when query unclear

**Checkpoint**: All basic chatbot functionality complete - Q&A, conversations, and graceful failures working

---

## Phase 6: User Story 4 - Basic Ticket Submission and Retrieval (Priority: P2)

**Goal**: Customer can submit support tickets when issue cannot be resolved through knowledge base, and can retrieve tickets using natural language.

**Independent Test**: (1) Ask a question chatbot cannot answer or explicitly request ticket creation, verify submit_ticket is invoked and ticket appended to tickets.jsonl. (2) Ask to find tickets by ID or content, verify find_ticket is invoked and returns matching tickets.

### Implementation for User Story 4

- [ ] T027 [P] [US4] Create ticket_manager.py in src/ with SupportTicket Pydantic model (ticket_id, timestamp, customer_message, status, conversation_context)
- [ ] T028 [P] [US4] Implement submit_ticket() function in src/ticket_manager.py with UUID4 ticket_id generation and JSON Lines append
- [ ] T029 [US4] Implement find_ticket(query: str) function in src/ticket_manager.py with ID matching and content search
- [ ] T030 [US4] Integrate PydanticAI @agent.tool decorator for submit_ticket in src/streamlit_app.py per contracts/tool-schemas.json
- [ ] T031 [US4] Integrate PydanticAI @agent.tool decorator for find_ticket in src/streamlit_app.py per contracts/tool-schemas.json
- [ ] T032 [US4] Update system prompt in src/streamlit_app.py to guide LLM when to invoke submit_ticket (low similarity, explicit request)
- [ ] T033 [US4] Update system prompt in src/streamlit_app.py to guide LLM when to invoke find_ticket (user asks to view/search tickets)
- [ ] T034 [US4] Test tool calling workflow: verify submit_ticket creates tickets.jsonl entry with correct schema
- [ ] T035 [US4] Test tool calling workflow: verify find_ticket searches tickets by ID and content successfully

**Checkpoint**: All user stories complete - full chatbot functionality with ticketing system operational

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and deployment readiness

- [ ] T036 [P] Update README.md with setup instructions, quickstart guide, and architecture overview
- [ ] T037 [P] Verify .env.example has all required configuration variables
- [ ] T038 Run quickstart.md validation: verify indexing_script.py works, verify streamlit_app.py launches, test basic Q&A flow
- [ ] T039 Run make check to verify ruff format, ruff lint, ty typecheck all pass
- [ ] T040 [P] Add structured logging to key operations: document indexing, RAG retrieval, tool calls
- [ ] T041 Verify error messages are user-friendly in streamlit_app.py for common failures (no documents, API errors)
- [ ] T042 Performance testing: verify query response <5 seconds, indexing <10 minutes per 10-page PDF

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (Basic Q&A): Can start after Foundational
  - User Story 2 (Multi-turn): Depends on User Story 1 completion (extends conversation handling)
  - User Story 3 (Graceful failures): Can start after User Story 1 (independent feature)
  - User Story 4 (Ticketing): Can start after User Story 1 (independent feature, though often triggered by US3 scenarios)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - REQUIRED for MVP
- **User Story 2 (P2)**: Depends on User Story 1 - Extends conversation handling built in US1
- **User Story 3 (P2)**: Can start after User Story 1 - Independent but builds on basic Q&A
- **User Story 4 (P2)**: Can start after User Story 1 - Independent feature using PydanticAI tools

### Within Each User Story

- Configuration/models before business logic
- Core retrieval/indexing before UI integration
- UI components before integration testing
- Independent features (US3, US4) can be developed in parallel after US1

### Parallel Opportunities

- **Phase 1 Setup**: T003, T004, T005 can run in parallel
- **Phase 2 Foundational**: T007, T008, T010 can run in parallel (different files)
- **Phase 4**: US2 tasks are sequential (extend US1)
- **Phase 5 & 6**: US3 and US4 can be worked in parallel after US1 completes (independent features)
- **Phase 6 US4**: T027, T028 can run in parallel (ticket model and functions)
- **Phase 7 Polish**: T036, T037, T040 can run in parallel (different files)

---

## Parallel Example: Phase 2 Foundational

```bash
# Launch foundational tasks together:
Task: "Create Pydantic models in src/models.py"
Task: "Implement document_loader.py in src/"
Task: "Setup logging with structlog in src/logging_config.py"
```

## Parallel Example: Phase 6 User Story 4

```bash
# Launch ticket infrastructure together:
Task: "Create ticket_manager.py with SupportTicket model"
Task: "Implement submit_ticket() function"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Basic Q&A)
4. **STOP and VALIDATE**: Test User Story 1 independently with sample documents
5. Deploy/demo minimal RAG chatbot

**MVP Scope**: ~130 lines of code (per plan.md) - Basic document Q&A with Streamlit UI

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test multi-turn conversations → Deploy/Demo
4. Add User Story 3 + User Story 4 in parallel → Test failure handling and ticketing → Deploy/Demo
5. Polish and performance validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (~50 lines)
2. Once Foundational is done:
   - Developer A: User Story 1 (Basic Q&A) - ~130 lines
   - Wait for US1 completion, then:
   - Developer B: User Story 2 (Multi-turn) - ~30 lines
   - Developer C: User Story 3 (Graceful failures) - ~20 lines
   - Developer D: User Story 4 (Ticketing) - ~50 lines
3. Stories integrate independently

---

## Task Count Summary

- **Phase 1 (Setup)**: 5 tasks
- **Phase 2 (Foundational)**: 5 tasks (BLOCKING)
- **Phase 3 (US1 - Basic Q&A)**: 8 tasks (MVP)
- **Phase 4 (US2 - Multi-turn)**: 4 tasks
- **Phase 5 (US3 - Graceful failures)**: 4 tasks
- **Phase 6 (US4 - Ticketing)**: 9 tasks
- **Phase 7 (Polish)**: 7 tasks

**Total**: 42 tasks

**MVP Scope**: 18 tasks (Phase 1 + Phase 2 + Phase 3)

**Parallel Opportunities**: 8 tasks marked [P] can run in parallel within their phases

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label (US1, US2, US3, US4) maps task to specific user story for traceability
- Each user story should be independently testable after completion
- Tests NOT required per POC policy (constitution Principle II allows omitting tests for POC)
- Commit after each task or logical group
- Stop at Phase 3 checkpoint for MVP validation
- US3 and US4 can be implemented in parallel after US1 completes (both independent features)
- Total implementation: ~230 lines of code (per plan.md estimate)
