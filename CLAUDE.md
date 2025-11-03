# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**customer_support** is a customer support bot which provides Streamlit interface.

## Development Setup

### Initial Setup
```bash
make init  # Creates venv, syncs dependencies, installs pre-commit hooks
```

This will:
- Create a virtual environment using `uv venv`
- Sync all dependencies with `uv sync`
- Install pre-commit hooks with `uvx prek`

### Environment Configuration
Copy `.env.example` to `.env` and configure:
- `OPENAI_API_KEY`: Your OpenAI-compatible API key
- `OPENAI_BASE_URL`: API endpoint (default: https://openrouter.ai/api/v1)
- `OPENAI_MODEL`: Model to use (default: openai/gpt-4o)

## Common Commands

### Quality Checks
```bash
make check      # Run all checks (format, lint, typecheck, test)
make format     # Format code with ruff
make lint       # Lint and auto-fix with ruff
make typecheck  # Type check with ty
make test       # Run pytest test suite
```

### Running Individual Tools
```bash
uv run ruff format .              # Format only
uv run ruff check . --fix         # Lint only
uvx ty check .                    # Type check only
uv run pytest                     # All tests
uv run pytest tests/path/to/test  # Single test file
uv run pytest -k test_name        # Single test by name
uv run pytest -m unit             # Run only unit tests
uv run pytest -m integration      # Run only integration tests
uv run pytest -m contract         # Run only contract tests
```

## Architecture

### Technology Stack
- **Python 3.12+**: Required minimum version
- **OpenAI SDK**: LLM integration (supports OpenAI-compatible APIs)
- **Pydantic**: Data validation and settings management
- **FastAPI**: REST API interface
- **Streamlit**: Web UI for visualization
- **structlog**: Structured logging

### Data Processing Pipeline
The project processes content through multiple stages:
1. **Extraction**: HTML (BeautifulSoup4), YouTube (yt-dlp, youtube-transcript-api), RSS (feedparser)
2. **Processing**: LLM-based content analysis and summarization
3. **Storage**: Results stored with MLflow tracking
4. **Serving**: FastAPI endpoints and Streamlit dashboards

### Code Quality Tools
- **ruff**: Fast Python linter and formatter (replaces black, isort, flake8)
- **ty**: Type checker for Python (configured in pyproject.toml)
- **pytest**: Testing framework with markers for unit/integration/contract tests
- **pre-commit**: Automated quality checks on commit (format → lint → typecheck)

### Pre-commit Hooks
Hooks run in this order:
1. `ruff format` - Code formatting
2. `ruff check --fix` - Linting with auto-fixes
3. `ty check` - Type checking

All hooks use local tools installed via `uv` (not isolated environments).

## Dependencies

### Core Dependencies
- Content extraction: `beautifulsoup4`, `yt-dlp`, `youtube-transcript-api`, `feedparser`
- LLM integration: `openai`, `tenacity` (for retries)
- Data processing: `pydantic`, `structlog`
- Orchestration: `dagster`, `dagster-webserver`
- ML tracking: `mlflow`
- APIs/UI: `fastapi`, `streamlit`

### Development Dependencies
- Testing: `pytest`, `pytest-asyncio`, `pytest-mock`, `factory-boy`, `faker`
- Quality: `ruff`, `ty` (via uvx)
- Dagster dev tools: `dagster-cloud`

## Testing Strategy

Tests are organized with pytest markers:
- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Tests requiring external services/resources
- `@pytest.mark.contract` - External API verification tests

Test configuration in `pyproject.toml` enforces strict marker usage.

## Project Structure Notes

- Source code expected in `dagster_project/` directory (referenced in pyproject.toml)
- Test files in `tests/` directory
- Build targets wheel packages from `src/` directory
- Artifacts stored in `artifacts/`, `mlruns/` (gitignored)
- Dagster home in `.dagster/` (gitignored)
