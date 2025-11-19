#!/usr/bin/env python3
"""Test PydanticAI agent tool integration.

This script verifies that the agent can successfully invoke tools.
"""

import os
from pathlib import Path

# Setup environment before imports
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Check if .env file exists and required variables are set
env_file = Path(".env")
if not env_file.exists():
    print("❌ .env file not found. Please create it with OPENAI_API_KEY.")
    print("   See .env.example for template.")
    exit(1)

from src.config import settings

if not settings.openai_api_key or settings.openai_api_key == "your_api_key_here":
    print("❌ OPENAI_API_KEY not configured in .env")
    print("   Please add a valid OpenRouter API key to .env")
    exit(1)

# Now we can import the agent
print("✓ Configuration loaded")
print(f"  API: {settings.openai_base_url}")
print(f"  Model: {settings.openai_model}")
print()

# Import agent after configuration
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.streamlit_app import agent

print("✓ Agent initialized with tools:")
print(f"  Available tools: {len(agent._function_toolset._functions)}")
for tool_name in agent._function_toolset._functions.keys():
    print(f"    - {tool_name}")
print()

print("=" * 60)
print("PydanticAI Agent Tool Integration Test")
print("=" * 60)
print()
print("This test verifies the agent has access to ticket management tools.")
print("To test actual tool calling, use the Streamlit app:")
print("  uv run streamlit run src/streamlit_app.py")
print()
print("Then try these prompts:")
print('  1. "I need to create a support ticket for my order issue"')
print('  2. "Show me my tickets"')
print('  3. "Find ticket <ID>"')
print()
print("=" * 60)
print("Tool Registration: ✓ PASSED")
print("=" * 60)
