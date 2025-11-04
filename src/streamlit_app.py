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
from src.vector_store import query_documents  # noqa: E402

setup_logging()
logger = get_logger(__name__)

# Configure OpenAI-compatible settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key
os.environ["OPENAI_BASE_URL"] = settings.openai_base_url

# Initialize PydanticAI agent with system prompt
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
)

# Streamlit app configuration
st.set_page_config(page_title="Customer Support Chatbot", page_icon="🤖", layout="wide")

st.title("🤖 Customer Support Chatbot")
st.caption("Ask me anything about our products and services!")

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []
    logger.info("Initialized new chat session")

# Display conversation history (all messages up to this point)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User input
if prompt := st.chat_input("Ask a question..."):
    # Add and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    logger.info("Processing user query", query=prompt)

    # Generate assistant response with spinner
    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        with st.spinner("Thinking..."):
            # RAG retrieval: Query ChromaDB for relevant context
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

            # Generate LLM response
            try:
                result = agent.run_sync(context_prompt)
                response = result.output
                logger.info("Generated response", query=prompt)

            except Exception as e:
                response = f"Sorry, I encountered an error: {str(e)}"
                logger.error("Error generating response", error=str(e), query=prompt)

        # Display response in placeholder
        message_placeholder.write(response)

        # Add assistant message to history
        st.session_state.messages.append({"role": "assistant", "content": response})
