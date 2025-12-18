import os
import sys
from pathlib import Path

# Fix tokenizers warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import streamlit as st
from pydantic_ai import Agent

# Add project root to path for imports (required for Streamlit standalone execution)
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import settings  # noqa: E402
from src.logging_config import get_logger, setup_logging  # noqa: E402
from src.ticket_manager import find_ticket, submit_ticket  # noqa: E402
from src.vector_store import query_documents  # noqa: E402

setup_logging()
logger = get_logger(__name__)


def load_system_prompt() -> str:
    """Load system prompt from external markdown file."""
    prompt_path = project_root / "prompts" / "system_prompt.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"System prompt not found: {prompt_path}")
    return prompt_path.read_text().strip()


# Configure OpenAI-compatible settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key
os.environ["OPENAI_BASE_URL"] = settings.openai_base_url


# History processor: Keep only last 10 turns (20 messages) for short-term memory
def keep_recent_messages(messages: list) -> list:
    """Keep only the last 10 conversation turns (20 messages) to manage token usage.

    This implements short-term memory by limiting context window.
    """
    max_messages = 20  # 10 turns * 2 messages per turn (user + assistant)
    if len(messages) > max_messages:
        logger.info("Trimming conversation history", total_messages=len(messages), keeping=max_messages)
        return messages[-max_messages:]
    return messages


# Initialize PydanticAI agent with system prompt and history processor
agent = Agent(
    model=f"openai:{settings.openai_model}",
    system_prompt=load_system_prompt(),
    history_processors=[keep_recent_messages],  # Automatic short-term memory management
)


# Register tools as plain functions (PydanticAI will handle schema generation)
@agent.tool_plain
def submit_support_ticket(message: str) -> str:
    """Submit a support ticket for issues requiring human assistance.

    Use this when the knowledge base cannot answer the question or the user
    explicitly requests to create a ticket or talk to a human.

    Args:
        message: The customer's issue or question that requires human assistance

    Returns:
        Confirmation message with ticket ID
    """
    result = submit_ticket(message, conversation_context=None)
    logger.info("Tool called: submit_ticket", ticket_id=result["ticket_id"])
    return result["message"]


@agent.tool_plain
def find_support_ticket(query: str) -> str:
    """Find existing support tickets by ticket ID or search by content.

    Use this when the user asks to view their tickets, search for a specific
    ticket, or check ticket status.

    Args:
        query: Search query - can be a ticket ID (UUID) or keywords to search

    Returns:
        Summary message with ticket information
    """
    result = find_ticket(query)
    logger.info("Tool called: find_ticket", query=query, matches=result["count"])

    if result["count"] == 0:
        return result["message"]

    # Format detailed ticket info
    response_lines = [result["message"], ""]
    for ticket in result["tickets"]:
        response_lines.append(f"Ticket ID: {ticket['ticket_id']}")
        response_lines.append(f"Created: {ticket['timestamp']}")
        response_lines.append(f"Message: {ticket['customer_message']}")
        response_lines.append(f"Status: {ticket['status']}")
        response_lines.append("")

    return "\n".join(response_lines)


# Streamlit app configuration
st.set_page_config(page_title="Customer Support Chatbot", page_icon="🤖", layout="wide")

st.title("🤖 Customer Support Chatbot")
st.caption("Ask me anything about our products and services!")

# Initialize session state for conversation history
if "agent_history" not in st.session_state:
    st.session_state.agent_history = []  # PydanticAI message history (ModelMessage objects)
    logger.info("Initialized new chat session")

# Initialize display messages (user-facing only, no internal prompts)
if "display_messages" not in st.session_state:
    st.session_state.display_messages = []  # List of {"role": str, "content": str}

# Display conversation history (user-facing messages only)
for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


# User input
if prompt := st.chat_input("Ask a question..."):
    # Add user message to display history
    st.session_state.display_messages.append({"role": "user", "content": prompt})

    # Display user message immediately
    with st.chat_message("user"):
        st.write(prompt)

    logger.info("Processing user query", query=prompt, conversation_turns=len(st.session_state.display_messages) // 2)

    # Generate assistant response with spinner
    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        with st.spinner("Thinking..."):
            # RAG retrieval: Query directly with user prompt
            # The agent's conversation history will provide context for response generation
            retrieval_results = query_documents(prompt, n_results=3, similarity_threshold=0.7)

            # Detect low-confidence scenarios: no relevant documents found
            if retrieval_results:
                context = "\n\n".join([f"[Source: {r.metadata.get('source', 'unknown')}]\n{r.text}" for r in retrieval_results])
                min_sim = min(r.similarity for r in retrieval_results)
                max_sim = max(r.similarity for r in retrieval_results)
                avg_sim = sum(r.similarity for r in retrieval_results) / len(retrieval_results)

                logger.info(
                    "Retrieved context",
                    num_chunks=len(retrieval_results),
                    min_similarity=min_sim,
                    max_similarity=max_sim,
                    avg_similarity=avg_sim,
                )

                # Detect AMBIGUOUS queries: moderate confidence with high variance in similarity scores
                # This suggests the query might match multiple different topics or be unclear
                similarity_variance = max_sim - min_sim
                is_ambiguous = avg_sim < 0.85 and similarity_variance > 0.15

                if is_ambiguous:
                    # AMBIGUOUS scenario: Query might need clarification
                    logger.info("Ambiguous query detected", avg_similarity=avg_sim, variance=similarity_variance)

                    context_prompt = f"""The knowledge base returned results with varying relevance \
(similarities ranging from {min_sim:.2f} to {max_sim:.2f}), which suggests the query might be \
ambiguous or could relate to multiple topics.

Knowledge Base Context:
{context}

User Question: {prompt}

Please:
1. Attempt to answer if the context is sufficient
2. If the query seems unclear or could mean multiple things, ask a clarifying question to better understand what the customer needs
3. Be specific about what details would help you provide a more accurate answer
4. Offer 2-3 specific interpretations if applicable (e.g., "Are you asking about X or Y?")"""
                else:
                    # HIGH CONFIDENCE scenario: Clear, relevant results
                    context_prompt = f"""Based on the following knowledge base context, please answer the user's question.

Knowledge Base Context:
{context}

User Question: {prompt}

Answer:"""
            else:
                # LOW CONFIDENCE scenario: All results below 0.7 similarity threshold
                logger.warning("No relevant context found", query=prompt, threshold=0.7)

                # Explicitly signal to the LLM that no relevant information was found
                context_prompt = f"""IMPORTANT: No relevant information was found in the knowledge base \
for this query (all documents had similarity scores below 0.7).

User Question: {prompt}

Since you don't have relevant context to answer this question:
1. Clearly acknowledge that you couldn't find information in the knowledge base
2. Do NOT attempt to answer from general knowledge or make up information
3. Offer to create a support ticket for human assistance
4. Suggest the customer can contact human support directly

Respond with empathy and helpfulness while being honest about the limitation."""

            # Generate LLM response with PydanticAI conversation history
            try:
                # Pass PydanticAI message history from previous agent runs
                # This gives the agent access to the full conversation context
                result = agent.run_sync(context_prompt, message_history=st.session_state.agent_history)
                response = result.output

                # Store the new messages from this run for next turn
                # result.new_messages() contains the messages from THIS run only
                st.session_state.agent_history.extend(result.new_messages())

                logger.info(
                    "Generated response with conversation context",
                    query=prompt,
                    history_messages=len(st.session_state.agent_history),
                )

            except Exception as e:
                response = f"Sorry, I encountered an error: {str(e)}"
                logger.error("Error generating response", error=str(e), query=prompt)

        # Add assistant response to display history
        st.session_state.display_messages.append({"role": "assistant", "content": response})

        # Display response in placeholder
        message_placeholder.write(response)
