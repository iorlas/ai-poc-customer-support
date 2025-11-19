#!/usr/bin/env python3
"""Manual test script for ticket management tools.

This script tests the submit_ticket and find_ticket functionality
without requiring the full Streamlit UI.
"""

import json
from pathlib import Path

from src.ticket_manager import find_ticket, submit_ticket


def test_submit_ticket():
    """Test ticket submission workflow."""
    print("\n=== Testing submit_ticket ===")

    # Test 1: Create a ticket without conversation context
    result1 = submit_ticket("I need help with my order #12345")
    print("✓ Created ticket without context:")
    print(f"  Ticket ID: {result1['ticket_id']}")
    print(f"  Timestamp: {result1['timestamp']}")
    print(f"  Message: {result1['message']}\n")

    # Test 2: Create a ticket with conversation context
    conversation = [
        {"role": "user", "content": "What are your business hours?"},
        {"role": "assistant", "content": "We're open 9-5 weekdays."},
        {"role": "user", "content": "I need to speak to a human about a billing issue."},
    ]
    result2 = submit_ticket("Billing question - need human assistance", conversation_context=conversation)
    print("✓ Created ticket with conversation context:")
    print(f"  Ticket ID: {result2['ticket_id']}")
    print(f"  Timestamp: {result2['timestamp']}")
    print(f"  Context messages: {len(conversation)}\n")

    return result1["ticket_id"], result2["ticket_id"]


def test_find_ticket(ticket_id1: str, ticket_id2: str):
    """Test ticket search workflow."""
    print("\n=== Testing find_ticket ===")

    # Test 1: Find ticket by ID
    result1 = find_ticket(ticket_id1)
    print(f"✓ Search by ticket ID '{ticket_id1[:8]}...':")
    print(f"  Found: {result1['count']} ticket(s)")
    print(f"  Message: {result1['message']}\n")

    # Test 2: Search by content
    result2 = find_ticket("billing")
    print("✓ Search by content 'billing':")
    print(f"  Found: {result2['count']} ticket(s)")
    print(f"  Message: {result2['message']}\n")

    # Test 3: Search with no matches
    result3 = find_ticket("nonexistent-query-xyz")
    print("✓ Search with no matches:")
    print(f"  Found: {result3['count']} ticket(s)")
    print(f"  Message: {result3['message']}\n")

    # Test 4: View all tickets in file
    tickets_file = Path("tickets.jsonl")
    if tickets_file.exists():
        with tickets_file.open("r") as f:
            all_tickets = [json.loads(line) for line in f if line.strip()]
        print(f"✓ Total tickets in file: {len(all_tickets)}")
        for ticket in all_tickets:
            print(f"  - {ticket['ticket_id'][:8]}... | {ticket['customer_message'][:50]}")
    print()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Manual Tool Testing for Customer Support Chatbot")
    print("=" * 60)

    # Run tests
    ticket_id1, ticket_id2 = test_submit_ticket()
    test_find_ticket(ticket_id1, ticket_id2)

    print("=" * 60)
    print("All tests completed successfully! ✓")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Launch the Streamlit app: uv run streamlit run src/streamlit_app.py")
    print("2. Test the tools through the chat interface:")
    print("   - Ask a question the chatbot can't answer")
    print("   - Say 'create a support ticket'")
    print("   - Say 'show me my tickets'")
    print()


if __name__ == "__main__":
    main()
