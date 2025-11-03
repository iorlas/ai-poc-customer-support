.PHONY: check format lint typecheck test

check: format lint typecheck test

format:
	uv run ruff format .

lint:
	uv run ruff check . --fix

typecheck:
	uv run uvx ty check .

test:
	uv run pytest

init:
	uv venv
	uv sync
	uvx prek