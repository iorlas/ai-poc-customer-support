import os
import sys
import uuid
from pathlib import Path

# Fix tokenizers warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import streamlit as st
from pydantic_ai import Agent, RunContext

# Add project root to path for imports (required for Streamlit standalone execution)
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import settings  # noqa: E402
from src.logging_config import get_logger, setup_logging  # noqa: E402
from src.models import RetrievalResult  # noqa: E402
from src.ticket_manager import find_ticket, submit_ticket  # noqa: E402
from src.ui_components import (  # noqa: E402
    render_confirmation,
    render_flight_cards,
    render_payment_summary,
    render_references,
    render_seat_cards,
)
from src.vector_store import query_documents  # noqa: E402
from src.workflow.data import (  # noqa: E402
    get_alternative_flights,
    get_change_fee,
    get_seats_for_flight,
    lookup_booking,
)
from src.workflow.models import (  # noqa: E402
    ReschedulingState,
    WorkflowDeps,
    WorkflowStep,
)

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


# Initialize PydanticAI agent with deps_type for workflow state
agent = Agent(
    model=f"openai:{settings.openai_model}",
    system_prompt=load_system_prompt(),
    deps_type=WorkflowDeps,
    history_processors=[keep_recent_messages],
)


# ============================================================================
# WORKFLOW TOOLS (with RunContext for state access)
# ============================================================================


@agent.tool
def start_rescheduling(ctx: RunContext[WorkflowDeps], pnr: str, surname: str) -> str:
    """Start flight rescheduling with PNR and surname.

    Use this when a customer wants to reschedule their flight and provides
    their booking reference (PNR) and surname.

    Args:
        ctx: PydanticAI run context with workflow state
        pnr: The 6-character booking reference (PNR)
        surname: The passenger's last name as on the booking

    Returns:
        Booking details and available alternative flights, or error message
    """
    state = ctx.deps.state
    logger.info("Tool called: start_rescheduling", pnr=pnr, surname=surname)

    # Look up booking
    booking = lookup_booking(pnr, surname)
    if not booking:
        return f"Booking not found for PNR '{pnr}' with surname '{surname}'. Please check your details and try again."

    original_flight = booking["flight"]

    # Get change fee based on fare class
    change_fee = get_change_fee(original_flight.fare_class)
    if change_fee is None:
        return (
            f"Sorry, your fare class ({original_flight.fare_class}) does not allow changes. "
            "Please contact our support line at +90 850 333 25 38 for assistance."
        )

    # Get alternative flights
    alternatives = get_alternative_flights(original_flight.departure, original_flight.arrival)
    if not alternatives:
        return (
            f"No alternative flights available for route {original_flight.departure} → {original_flight.arrival}. Please contact support."
        )

    # Update state
    state.pnr = pnr.upper()
    state.surname = surname.upper()
    state.original_flight = original_flight
    state.alternative_flights = alternatives
    state.change_fee = change_fee
    state.current_step = WorkflowStep.FLIGHT_SELECTION

    return f"""Found your booking!

**Original Flight:** {original_flight.flight_number}
**Route:** {original_flight.departure} → {original_flight.arrival}
**Departure:** {original_flight.departure_time}
**Fare Class:** {original_flight.fare_class}

**Change Fee:** {change_fee:.0f} TRY

I found {len(alternatives)} alternative flights. Please select one from the options below.

SHOW_FLIGHT_CARDS"""


@agent.tool
def select_flight(ctx: RunContext[WorkflowDeps], flight_id: str) -> str:
    """Select an alternative flight from the available options.

    Use this when the customer chooses which flight they want to change to.

    Args:
        ctx: PydanticAI run context with workflow state
        flight_id: The ID of the selected flight

    Returns:
        Confirmation and available seat options, or error message
    """
    state = ctx.deps.state
    logger.info("Tool called: select_flight", flight_id=flight_id, current_step=state.current_step)

    if state.current_step != WorkflowStep.FLIGHT_SELECTION:
        return "Please start the rescheduling process first by providing your PNR and surname."

    # Find selected flight
    flight = next((f for f in state.alternative_flights if f.flight_id == flight_id), None)
    if not flight:
        available_ids = [f.flight_id for f in state.alternative_flights]
        return f"Flight '{flight_id}' not found. Available options: {', '.join(available_ids)}"

    # Get available seats
    seats = get_seats_for_flight(flight_id)
    if not seats:
        return f"No seats available for flight {flight.flight_number}. Please select another flight."

    # Update state
    state.selected_flight = flight
    state.fare_difference = flight.fare_difference
    state.available_seats = seats
    state.current_step = WorkflowStep.SEAT_SELECTION

    return f"""Flight {flight.flight_number} at {flight.departure_time} selected!

**Fare Difference:** {"+" if flight.fare_difference >= 0 else ""}{flight.fare_difference:.0f} TRY

Now please choose your seat from the options below.

SHOW_SEAT_CARDS"""


@agent.tool
def select_seat(ctx: RunContext[WorkflowDeps], seat_id: str) -> str:
    """Select a seat on the new flight.

    Use this when the customer chooses their seat.

    Args:
        ctx: PydanticAI run context with workflow state
        seat_id: The ID of the selected seat

    Returns:
        Payment summary with total amount, or error message
    """
    state = ctx.deps.state
    logger.info("Tool called: select_seat", seat_id=seat_id, current_step=state.current_step)

    if state.current_step != WorkflowStep.SEAT_SELECTION:
        return "Please select a flight first."

    # Find selected seat
    seat = next((s for s in state.available_seats if s.seat_id == seat_id), None)
    if not seat:
        available_ids = [s.seat_id for s in state.available_seats[:5]]
        return f"Seat '{seat_id}' not available. Some options: {', '.join(available_ids)}"

    # Update state
    state.selected_seat = seat
    state.current_step = WorkflowStep.PAYMENT

    # Calculate total
    fare_diff = max(0, state.fare_difference)  # Only charge if positive
    total = fare_diff + state.change_fee + seat.price

    return f"""Seat {seat.seat_number} ({seat.seat_type.title()}) selected!

**Payment Summary:**
- Fare Difference: {"+" if state.fare_difference >= 0 else ""}{state.fare_difference:.0f} TRY
- Change Fee: {state.change_fee:.0f} TRY
- Seat Selection: {seat.price:.0f} TRY
- **TOTAL: {total:.0f} TRY**

How would you like to pay? You can say "credit card" or "Klarna".

SHOW_PAYMENT_SUMMARY"""


@agent.tool
def confirm_payment(ctx: RunContext[WorkflowDeps], payment_method: str) -> str:
    """Confirm payment and complete the flight rescheduling.

    Use this when the customer confirms they want to proceed with payment.

    Args:
        ctx: PydanticAI run context with workflow state
        payment_method: Payment method (credit_card, klarna, etc.)

    Returns:
        Booking confirmation with transaction ID, or error message
    """
    state = ctx.deps.state
    logger.info("Tool called: confirm_payment", payment_method=payment_method, current_step=state.current_step)

    if state.current_step != WorkflowStep.PAYMENT:
        return "Please complete seat selection first."

    # Generate transaction ID
    transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"

    # Update state
    state.transaction_id = transaction_id
    state.current_step = WorkflowStep.COMPLETED

    return f"""Booking confirmed!

**New Flight:** {state.selected_flight.flight_number} at {state.selected_flight.departure_time}
**Route:** {state.selected_flight.departure} → {state.selected_flight.arrival}
**Seat:** {state.selected_seat.seat_number} ({state.selected_seat.seat_type.title()})

**Transaction ID:** {transaction_id}

A confirmation email will be sent to your registered email address shortly.

Is there anything else I can help you with?

SHOW_CONFIRMATION"""


@agent.tool
def cancel_rescheduling(ctx: RunContext[WorkflowDeps]) -> str:
    """Cancel the current flight rescheduling process.

    Use this when the customer decides not to proceed with rescheduling.

    Args:
        ctx: PydanticAI run context with workflow state

    Returns:
        Cancellation confirmation
    """
    state = ctx.deps.state
    logger.info("Tool called: cancel_rescheduling", current_step=state.current_step)

    # Reset state fields (can't reassign ctx.deps.state as it won't affect session_state)
    state.current_step = WorkflowStep.IDLE
    state.pnr = None
    state.surname = None
    state.original_flight = None
    state.alternative_flights = []
    state.selected_flight = None
    state.available_seats = []
    state.selected_seat = None
    state.change_fee = 0.0
    state.fare_difference = 0.0
    state.transaction_id = None

    return "Flight rescheduling cancelled. How else can I help you today?"


# ============================================================================
# EXISTING TOOLS (ticket management)
# ============================================================================


@agent.tool
def submit_support_ticket(ctx: RunContext[WorkflowDeps], message: str) -> str:
    """Submit a support ticket for issues requiring human assistance.

    Use this when the knowledge base cannot answer the question or the user
    explicitly requests to create a ticket or talk to a human.

    Args:
        ctx: PydanticAI run context
        message: The customer's issue or question that requires human assistance

    Returns:
        Confirmation message with ticket ID
    """
    result = submit_ticket(message, conversation_context=None)
    logger.info("Tool called: submit_ticket", ticket_id=result["ticket_id"])
    return result["message"]


@agent.tool
def find_support_ticket(ctx: RunContext[WorkflowDeps], query: str) -> str:
    """Find existing support tickets by ticket ID or search by content.

    Use this when the user asks to view their tickets, search for a specific
    ticket, or check ticket status.

    Args:
        ctx: PydanticAI run context
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


# ============================================================================
# STREAMLIT APP
# ============================================================================

# Streamlit app configuration
st.set_page_config(page_title="AJet Customer Support", page_icon=":airplane:", layout="wide")

st.title(":airplane: AJet Customer Support")
st.caption("I can help you with flight information, rescheduling, and more!")

# Initialize session state for conversation history
if "agent_history" not in st.session_state:
    st.session_state.agent_history = []  # PydanticAI message history (ModelMessage objects)
    logger.info("Initialized new chat session")

# Initialize display messages (user-facing only, no internal prompts)
if "display_messages" not in st.session_state:
    st.session_state.display_messages = []  # List of {"role": str, "content": str}

# Initialize workflow state
if "workflow_state" not in st.session_state:
    st.session_state.workflow_state = ReschedulingState()

# Initialize pending UI action
if "pending_ui_action" not in st.session_state:
    st.session_state.pending_ui_action = None


def get_workflow_deps() -> WorkflowDeps:
    """Get workflow dependencies with current state."""
    return WorkflowDeps(state=st.session_state.workflow_state)


def process_user_input(prompt: str) -> tuple[str, list[RetrievalResult] | None]:
    """Process user input through the agent and return response with references.

    Returns:
        Tuple of (response text, retrieval results used for context or None)
    """
    logger.info(
        "Processing user query",
        query=prompt,
        conversation_turns=len(st.session_state.display_messages) // 2,
        workflow_step=st.session_state.workflow_state.current_step,
    )

    # Build context based on workflow state
    workflow_state = st.session_state.workflow_state
    workflow_context = ""
    retrieval_results: list[RetrievalResult] | None = None

    if workflow_state.current_step != WorkflowStep.IDLE:
        workflow_context = f"""
[WORKFLOW ACTIVE - Step: {workflow_state.current_step.value}]
Keep the customer focused on completing the rescheduling workflow.
If they ask unrelated questions, briefly acknowledge and redirect to the current step.
"""

    # RAG retrieval for non-workflow questions
    if workflow_state.current_step == WorkflowStep.IDLE:
        retrieval_results = query_documents(prompt, n_results=3, similarity_threshold=0.5)

        if retrieval_results:
            context = "\n\n".join([f"[Source: {r.metadata.get('source', 'unknown')}]\n{r.text}" for r in retrieval_results])
            context_prompt = f"""Based on the following knowledge base context, please answer the user's question.

Knowledge Base Context:
{context}

User Question: {prompt}

Answer:"""
        else:
            context_prompt = f"""IMPORTANT: No relevant information was found in the knowledge base for this query.

User Question: {prompt}

Since you don't have relevant context:
1. Acknowledge that you couldn't find specific information
2. If the user mentions flight rescheduling, late flights, or changing bookings, offer to help with that
3. Otherwise, offer to create a support ticket or suggest calling +90 850 333 25 38"""
    else:
        # During workflow, process user input directly
        context_prompt = f"""{workflow_context}

User says: {prompt}

Respond appropriately based on the current workflow step. Use the appropriate tool if needed."""

    # Get workflow deps for agent
    deps = get_workflow_deps()

    # Generate LLM response
    result = agent.run_sync(context_prompt, deps=deps, message_history=st.session_state.agent_history)
    response = result.output

    # Store the new messages from this run for next turn
    st.session_state.agent_history.extend(result.new_messages())

    logger.info(
        "Generated response",
        query=prompt,
        history_messages=len(st.session_state.agent_history),
        workflow_step=st.session_state.workflow_state.current_step,
        references_used=len(retrieval_results) if retrieval_results else 0,
    )

    return response, retrieval_results


def handle_ui_selection(selection_type: str, selection_id: str):
    """Handle UI card selection by calling appropriate tool."""
    deps = get_workflow_deps()

    if selection_type == "flight":
        # Simulate user selecting flight
        result = agent.run_sync(
            f"The customer selected flight {selection_id}. Use the select_flight tool.",
            deps=deps,
            message_history=st.session_state.agent_history,
        )
    elif selection_type == "seat":
        result = agent.run_sync(
            f"The customer selected seat {selection_id}. Use the select_seat tool.",
            deps=deps,
            message_history=st.session_state.agent_history,
        )
    elif selection_type == "payment":
        result = agent.run_sync(
            f"The customer wants to pay with {selection_id}. Use the confirm_payment tool.",
            deps=deps,
            message_history=st.session_state.agent_history,
        )
    else:
        return

    st.session_state.agent_history.extend(result.new_messages())
    st.session_state.display_messages.append({"role": "assistant", "content": result.output})


# Display conversation history (user-facing messages only)
for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"]):
        # Remove UI signals from displayed content
        content = msg["content"]
        for signal in ["SHOW_FLIGHT_CARDS", "SHOW_SEAT_CARDS", "SHOW_PAYMENT_SUMMARY", "SHOW_CONFIRMATION"]:
            content = content.replace(signal, "").strip()
        st.write(content)

        # Show references if available for assistant messages
        if msg["role"] == "assistant" and msg.get("references"):
            render_references(msg["references"])

# Render workflow UI based on current state
workflow_state = st.session_state.workflow_state

if workflow_state.current_step == WorkflowStep.FLIGHT_SELECTION and workflow_state.alternative_flights:
    selected = render_flight_cards(workflow_state.alternative_flights)
    if selected:
        handle_ui_selection("flight", selected)
        st.rerun()

elif workflow_state.current_step == WorkflowStep.SEAT_SELECTION and workflow_state.available_seats:
    selected = render_seat_cards(workflow_state.available_seats)
    if selected:
        handle_ui_selection("seat", selected)
        st.rerun()

elif workflow_state.current_step == WorkflowStep.PAYMENT and workflow_state.selected_flight and workflow_state.selected_seat:
    payment = render_payment_summary(
        fare_difference=workflow_state.fare_difference,
        change_fee=workflow_state.change_fee,
        seat_price=workflow_state.selected_seat.price,
        flight=workflow_state.selected_flight,
        seat=workflow_state.selected_seat,
    )
    if payment:
        handle_ui_selection("payment", payment)
        st.rerun()

elif workflow_state.current_step == WorkflowStep.COMPLETED and workflow_state.transaction_id:
    render_confirmation(
        transaction_id=workflow_state.transaction_id,
        flight=workflow_state.selected_flight,
        seat=workflow_state.selected_seat,
    )
    # Reset workflow after showing confirmation
    if st.button("Start New Conversation"):
        st.session_state.workflow_state = ReschedulingState()
        st.rerun()

# User input
if prompt := st.chat_input("Ask a question or provide your PNR to reschedule..."):
    # Capture workflow state BEFORE processing
    step_before = st.session_state.workflow_state.current_step

    # Add user message to display history
    st.session_state.display_messages.append({"role": "user", "content": prompt})

    # Display user message immediately
    with st.chat_message("user"):
        st.write(prompt)

    # Generate assistant response with spinner
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        references_placeholder = st.empty()

        with st.spinner("Thinking..."):
            try:
                response, references = process_user_input(prompt)

                # Clean response for display (remove UI signals if present)
                display_response = response
                for signal in ["SHOW_FLIGHT_CARDS", "SHOW_SEAT_CARDS", "SHOW_PAYMENT_SUMMARY", "SHOW_CONFIRMATION"]:
                    display_response = display_response.replace(signal, "").strip()

                # Add assistant response to display history with references
                message_data = {"role": "assistant", "content": response}
                if references:
                    message_data["references"] = [
                        {
                            "source": r.metadata.get("source", "unknown"),
                            "url": r.metadata.get("url", ""),
                            "similarity": r.similarity,
                            "text": r.text,
                        }
                        for r in references
                    ]
                st.session_state.display_messages.append(message_data)

                # Display response in placeholder
                message_placeholder.write(display_response)

                # Display references if available
                if references:
                    with references_placeholder.container():
                        render_references(references)

            except Exception as e:
                response = f"Sorry, I encountered an error: {e!s}"
                logger.error("Error generating response", error=str(e), query=prompt)
                message_placeholder.write(response)

    # Trigger rerun if workflow state changed (to show UI cards)
    step_after = st.session_state.workflow_state.current_step
    if step_before != step_after:
        st.rerun()
