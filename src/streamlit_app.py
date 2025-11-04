import os
import sys
from pathlib import Path

# Fix tokenizers warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import streamlit as st
from pydantic_ai import Agent, ModelMessage

# Add project root to path for imports (required for Streamlit standalone execution)
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import settings  # noqa: E402
from src.logging_config import get_logger, setup_logging  # noqa: E402
from src.vector_store import query_documents  # noqa: E402

setup_logging()
logger = get_logger(__name__)

# Configure OpenAI-compatible settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key
os.environ["OPENAI_BASE_URL"] = settings.openai_base_url


# History processor: Keep only last 10 turns (20 messages) for short-term memory
def keep_recent_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
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
    system_prompt="""You are a helpful customer support chatbot working for B&H Photo Video.
Use the knowledge base context provided to answer questions accurately.

IMPORTANT GUIDELINES FOR LOW-CONFIDENCE SCENARIOS:

1. **When Knowledge Base Has No Relevant Information:**
   - Clearly state: "I couldn't find specific information about that in our knowledge base."
   - DO NOT fabricate or guess answers
   - Offer to create a support ticket for human assistance
   - Example: "I don't have information about that in my current knowledge base.
     Would you like me to create a support ticket so a human agent can help you?"

2. **When Query is Ambiguous or Unclear:**
   - Ask clarifying questions to better understand the customer's needs
   - Example: "Could you provide more details about...?" or "Are you asking about X or Y?"
   - Be specific about what information would help you assist them better

3. **When Context is Insufficient:**
   - Acknowledge the limitation honestly
   - Explain what information you DO have
   - Offer alternative ways to get help (ticket, human contact)

4. **Response Guidelines:**
   - Be concise and helpful
   - Reference the knowledge base when answers are found
   - Maintain a professional and friendly tone
   - Always prioritize accuracy over completeness
   - Never make up information to fill gaps""",
    history_processors=[keep_recent_messages],  # Automatic short-term memory management
)

# Streamlit app configuration
st.set_page_config(page_title="Customer Support Chatbot", page_icon="🤖", layout="wide")

st.title("🤖 Customer Support Chatbot")
st.caption("Ask me anything about our products and services!")

# Initialize session state for conversation history
if "agent_history" not in st.session_state:
    st.session_state.agent_history = []  # PydanticAI message history (ModelMessage objects)
    logger.info("Initialized new chat session")

# Display conversation history from agent_history
# Extract user and assistant messages from ModelMessage objects
for msg in st.session_state.agent_history:
    # ModelRequest contains user prompts, ModelResponse contains assistant replies
    if hasattr(msg, "parts"):
        for part in msg.parts:
            # UserPromptPart = user message, TextPart = assistant message
            if part.__class__.__name__ == "UserPromptPart":
                with st.chat_message("user"):
                    st.write(part.content)
            elif part.__class__.__name__ == "TextPart":
                with st.chat_message("assistant"):
                    st.write(part.content)


# User input
if prompt := st.chat_input("Ask a question..."):
    # Display user message immediately
    with st.chat_message("user"):
        st.write(prompt)

    logger.info("Processing user query", query=prompt, conversation_turns=len(st.session_state.agent_history) // 2)

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

        # Display response in placeholder
        message_placeholder.write(response)
