"""Ticket management functionality for customer support chatbot.

This module provides functions for creating and searching support tickets
using JSON Lines format for storage.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from src.logging_config import get_logger

logger = get_logger(__name__)


class SupportTicket(BaseModel):
    """Support ticket model with conversation context.

    Attributes:
        ticket_id: Unique identifier (UUID4 format)
        timestamp: Creation time (ISO8601 format)
        customer_message: Customer's issue description
        status: Ticket status (always "open" in POC)
        conversation_context: Optional list of prior messages
    """

    ticket_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    customer_message: str
    status: str = "open"
    conversation_context: list[dict] | None = None


def submit_ticket(message: str, conversation_context: list[dict] | None = None) -> dict:
    """Submit a support ticket for human assistance.

    Creates a new support ticket with a unique ID and appends it to tickets.jsonl.
    This is a fail-fast implementation with no error recovery.

    Args:
        message: Customer's issue description
        conversation_context: Optional list of prior conversation messages

    Returns:
        dict with ticket_id, timestamp, status, and confirmation message

    Raises:
        IOError: If tickets.jsonl cannot be written (fail-fast)
    """
    ticket = SupportTicket(customer_message=message, conversation_context=conversation_context)

    # Append to JSON Lines file (fail-fast on error)
    tickets_file = Path("tickets.jsonl")
    with tickets_file.open("a") as f:
        f.write(ticket.model_dump_json() + "\n")

    logger.info("Ticket created", ticket_id=ticket.ticket_id, message_length=len(message))

    return {
        "ticket_id": ticket.ticket_id,
        "timestamp": ticket.timestamp,
        "status": ticket.status,
        "message": f"Ticket {ticket.ticket_id} created successfully. A human agent will review your request.",
    }


def find_ticket(query: str) -> dict:
    """Find support tickets by ID or content search.

    Searches tickets.jsonl for matches in ticket_id or customer_message.
    Returns all matching tickets with count and summary message.

    Args:
        query: Search query (ticket ID or keywords)

    Returns:
        dict with tickets (list), count (int), and message (str)

    Raises:
        FileNotFoundError: If tickets.jsonl doesn't exist (fail-fast)
        json.JSONDecodeError: If file is corrupted (fail-fast)
    """
    tickets_file = Path("tickets.jsonl")

    # Fail-fast if file doesn't exist
    if not tickets_file.exists():
        logger.warning("No tickets file found")
        return {"tickets": [], "count": 0, "message": "No tickets found. The tickets file doesn't exist yet."}

    # Read and parse all tickets (fail-fast on corruption)
    tickets = []
    with tickets_file.open("r") as f:
        for line in f:
            if line.strip():  # Skip empty lines
                ticket_data = json.loads(line)
                tickets.append(ticket_data)

    # Search by ticket ID or content (case-insensitive for content)
    query_lower = query.lower()
    matches = [t for t in tickets if query in t["ticket_id"] or query_lower in t["customer_message"].lower()]

    logger.info("Ticket search", query=query, total_tickets=len(tickets), matches=len(matches))

    if not matches:
        return {"tickets": [], "count": 0, "message": f"No tickets found matching '{query}'."}

    # Format summary message
    ticket_ids = [t["ticket_id"][:8] + "..." for t in matches]  # Show first 8 chars of UUID
    summary = f"Found {len(matches)} ticket(s): {', '.join(ticket_ids)}"

    return {"tickets": matches, "count": len(matches), "message": summary}
