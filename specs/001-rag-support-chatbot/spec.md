# Feature Specification: RAG-Based Customer Support Chatbot

**Feature Branch**: `001-rag-support-chatbot`
**Created**: 2025-11-04
**Status**: Draft
**Input**: User description: "streamlit customer support chatbot simulating a real website with a chatbot. It should be able to answer questions based on documents - so we need RAG. consider everything selfhosted, minimal"

## Clarifications

### Session 2025-11-04

- Q: Embedding Model Selection - For self-hosted RAG semantic search, which embedding model approach should be used? → A: ChromaDB with its recommended model using OpenRouter
- Q: Document Chunking Strategy - How should documents be split into chunks for embedding and retrieval? → A: Fixed token size with overlap (e.g., 512 tokens with 128 token overlap)
- Q: Scope Simplification - Should admin features (document management UI) be included? → A: No - remove all admin UI features; use Python script for ChromaDB indexing only
- Q: Ticketing System Scope - What ticket functionality is needed? → A: Basic dirty implementation with LLM tool calling for submit_ticket only; append-only JSON Lines storage; no admin UI for ticket management
- Q: Chat Interface Implementation - What UI framework components should be used for the chat interface? → A: Streamlit native chat components only (st.chat_message, st.chat_input) - minimal dependencies
- Q: Retrieval Strategy - How many document chunks should be retrieved per query and what quality threshold should be applied? → A: Top-3 chunks with similarity threshold >0.7 - balanced context quality with token efficiency

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Question Answering (Priority: P1)

A customer visits the support page and asks a simple question about product features or policies documented in the knowledge base. The chatbot retrieves relevant information and provides an accurate answer.

**Why this priority**: This is the core value proposition - customers can get instant answers to common questions without waiting for human support. It's the minimum viable functionality that delivers immediate value.

**Independent Test**: Can be fully tested by loading a sample knowledge base with FAQs, asking a question covered in the documents, and verifying the chatbot returns accurate information from those documents.

**Acceptance Scenarios**:

1. **Given** a customer is on the support chat page, **When** they ask "What are your business hours?", **Then** the chatbot retrieves the relevant document section and responds with the correct business hours
2. **Given** a customer asks about product pricing, **When** pricing information exists in the knowledge base, **Then** the chatbot provides accurate pricing details from the documents
3. **Given** a customer asks a question in natural language, **When** multiple relevant documents exist, **Then** the chatbot synthesizes information from the most relevant sources

---

### User Story 2 - Multi-Turn Conversation (Priority: P2)

A customer engages in a conversation with follow-up questions, and the chatbot maintains context to provide coherent responses across multiple turns.

**Why this priority**: Real support interactions often require clarification and follow-up. This makes the chatbot feel more natural and helpful, significantly improving user experience beyond basic Q&A.

**Independent Test**: Can be tested by initiating a conversation, asking an initial question, then asking 2-3 follow-up questions that reference the previous context, and verifying the chatbot maintains conversational coherence.

**Acceptance Scenarios**:

1. **Given** a customer has asked about return policies, **When** they follow up with "How long does that take?", **Then** the chatbot understands "that" refers to returns and provides processing time
2. **Given** an ongoing conversation, **When** a customer asks a clarifying question, **Then** the chatbot maintains conversation history and responds appropriately
3. **Given** a customer starts a new topic mid-conversation, **When** they ask an unrelated question, **Then** the chatbot recognizes the context shift and responds to the new topic

---

### User Story 3 - Graceful Failure Handling (Priority: P2)

When the chatbot cannot find relevant information or is uncertain about an answer, it communicates this clearly and offers alternatives.

**Why this priority**: Honest communication about limitations builds trust. This prevents the chatbot from providing incorrect information and ensures customers know when to seek human assistance.

**Independent Test**: Can be tested by asking questions not covered in the knowledge base, asking ambiguous questions, or testing edge cases, and verifying the chatbot responds appropriately without fabricating answers.

**Acceptance Scenarios**:

1. **Given** a customer asks a question not covered in the knowledge base, **When** no relevant documents are found, **Then** the chatbot clearly states it cannot find relevant information and offers to connect to human support
2. **Given** a customer's question is ambiguous, **When** the chatbot cannot determine intent, **Then** it asks clarifying questions
3. **Given** the chatbot has low confidence in its answer, **When** responding, **Then** it indicates uncertainty and suggests verifying with a human agent

---

### User Story 4 - Basic Ticket Submission and Retrieval (Priority: P2)

A customer can submit a support ticket when their issue cannot be resolved through the knowledge base, and can later retrieve tickets using natural language requests. The LLM agent uses tool calling to invoke submit_ticket or find_ticket based on user intent.

**Why this priority**: Provides an escalation path and ticket tracking for issues beyond RAG capabilities. Important for realistic support workflow but secondary to core Q&A functionality.

**Independent Test**: Can be tested by (1) asking a question the chatbot cannot answer or explicitly requesting ticket creation, verifying submit_ticket is invoked and ticket is appended to tickets.jsonl, then (2) asking to find tickets by ID or content, verifying find_ticket is invoked and returns matching tickets.

**Acceptance Scenarios**:

1. **Given** a customer asks a question not in the knowledge base (similarity <0.7), **When** the chatbot offers to create a ticket and the customer agrees, **Then** the chatbot invokes submit_ticket and returns a confirmation with ticket ID
2. **Given** a customer explicitly says "I need to talk to a human" or "create a ticket", **When** the LLM processes this intent, **Then** the chatbot invokes submit_ticket with the conversation context
3. **Given** a ticket is successfully created, **When** written to tickets.jsonl, **Then** it contains unique ticket ID, timestamp, customer message, and status "open"
4. **Given** a customer asks "show me my tickets" or "find ticket 12345", **When** the LLM processes this intent, **Then** the chatbot invokes find_ticket with appropriate search parameters and displays matching tickets
5. **Given** multiple tickets exist in tickets.jsonl, **When** find_ticket is invoked with a specific ticket ID, **Then** the exact matching ticket is returned

---

### Edge Cases

- What happens when a customer asks the same question multiple times in different ways? → System should retrieve similar content and may provide consistent answers; conversation history may help detect repetition
- How does the system handle very long or very short questions? → Long questions truncated to model context limits; short questions (1-2 words) may trigger clarification request
- What happens when multiple documents contain contradictory information? → System retrieves top-k chunks by relevance score and LLM synthesizes answer; may acknowledge conflicting information if detected
- How does the system respond to inappropriate, off-topic, or adversarial inputs? → LLM system prompt includes safety guidelines; off-topic queries receive polite redirection to support topics
- What happens when the document store is empty or documents fail to load? → Fail immediately; no error handling in PoC
- What happens if tickets.jsonl is corrupted or missing? → Fail immediately; no error handling in PoC
- What happens if submit_ticket is invoked multiple times in quick succession? → Each invocation creates a separate ticket with unique ID; no deduplication logic

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept natural language questions from users through a chat interface
- **FR-002**: System MUST retrieve top-3 relevant document chunks using semantic search with similarity threshold >0.7
- **FR-003**: System MUST generate answers that are grounded in the retrieved document content
- **FR-004**: System MUST display the chat interface in a web browser without requiring user authentication
- **FR-005**: System MUST maintain conversation history within a single user session
- **FR-006**: System MUST indicate when it cannot find relevant information to answer a question (no chunks meet similarity threshold)
- **FR-007**: System MUST process and index common document formats (at minimum: PDF, plain text, markdown) via Python script
- **FR-008**: System MUST show typing indicators or loading states while processing requests
- **FR-009**: System MUST store document embeddings for semantic search using ChromaDB
- **FR-010**: System MAY use OpenRouter API for embedding generation (ChromaDB's recommended model) while maintaining self-hosted vector storage
- **FR-011**: System MUST provide LLM tool calling capability for submit_ticket and find_ticket functions
- **FR-012**: System MUST allow the LLM agent to autonomously decide when to invoke submit_ticket or find_ticket based on user intent
- **FR-013**: System MUST store submitted tickets in append-only JSON Lines format (.jsonl)
- **FR-014**: System MUST assign unique ticket IDs (e.g., UUID or timestamp-based) to each submitted ticket
- **FR-015**: System MUST persist tickets with fields: ticket_id, timestamp, customer_message, status (fixed value "open"), and optional conversation_context
- **FR-016**: System MUST support find_ticket tool for retrieving tickets by ticket_id or searching ticket content by natural language query
- **FR-017**: System MUST fail immediately if tickets.jsonl is corrupted or missing (no error recovery in PoC)

### Key Entities

- **User Session**: Represents an individual customer's interaction with the chatbot, including conversation history and context
- **Message**: A single turn in the conversation, either from the customer (question) or chatbot (response), with timestamp
- **Document**: A knowledge base artifact containing information that can be queried, with metadata (title, upload date, document type)
- **Document Chunk**: A fixed-size segment of a document (512 tokens with 128 token overlap) that can be independently embedded, retrieved, and referenced
- **Embedding**: A numerical vector representation of text (document chunks or queries) used for semantic similarity matching
- **Retrieval Result**: A document chunk matched to a user query, with relevance score and source reference
- **Support Ticket**: A simple escalation record stored in JSON Lines format, containing ticket_id (UUID or timestamp-based), timestamp (ISO8601), customer_message (text), status (always "open"), and optional conversation_context (list of prior messages). No update/close mechanism in this minimal implementation.

### Technical Constraints

- **Vector Database**: ChromaDB for self-hosted vector storage and similarity search
- **Embedding Provider**: OpenRouter API using ChromaDB's recommended embedding model
- **Chunking Strategy**: Fixed token size (512 tokens) with overlap (128 tokens) to preserve context at boundaries
- **Retrieval Parameters**: Top-3 chunks per query with similarity threshold >0.7 to filter low-quality matches
- **LLM Tool Calling**: Agent architecture with function/tool calling for submit_ticket and find_ticket (OpenAI-compatible tool schema); LLM autonomously decides when to invoke based on intent
- **Indexing**: Python script for offline document processing and ChromaDB index creation
- **UI Framework**: Streamlit native chat components (st.chat_message, st.chat_input) with session state for conversation history
- **Storage Architecture**: Local file-based persistence (ChromaDB data directory + tickets.jsonl append-only file)
- **Deployment**: Single-instance self-hosted deployment (no distributed components)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can receive a response to simple factual questions in under 5 seconds
- **SC-002**: The chatbot correctly answers at least 80% of questions that are covered in the knowledge base (measured through test question set)
- **SC-003**: The chatbot successfully declines to answer (rather than hallucinating) at least 90% of questions not covered in the knowledge base
- **SC-004**: Users can complete a full conversation (3+ turns) with maintained context
- **SC-005**: The indexing script can process and index a 10-page document in under 10 minutes
- **SC-006**: The system can handle 10 concurrent chat sessions without degraded response times
- **SC-007**: The interface loads and is interactive within 3 seconds of page load
