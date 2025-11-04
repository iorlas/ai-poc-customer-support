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
    system_prompt="""You are a helpful customer support chatbot. Working for B&H Photo Video.
Use the knowledge base context provided to answer questions accurately.

If you cannot find relevant information in the provided context,
clearly communicate this limitation and avoid fabricating answers.

When responding:
- Be concise and helpful
- Reference the knowledge base when possible
- If uncertain, acknowledge the limitation
- Maintain a professional and friendly tone""",
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

            if retrieval_results:
                context = "\n\n".join([f"[Source: {r.metadata.get('source', 'unknown')}]\n{r.text}" for r in retrieval_results])
                logger.info("Retrieved context", num_chunks=len(retrieval_results))

                # Build prompt with context
                context_prompt = f"""Based on the following knowledge base context, please answer the user's question.

Knowledge Base Context:
{context}

User Question: {prompt}

Answer:"""
            else:
                context_prompt = prompt
                logger.warning("No relevant context found", query=prompt)

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
