.PHONY: install test lint typecheck check schemas
install:
	uv sync --extra dev
test:
	uv run pytest
lint:
	uv run ruff check .
typecheck:
	uv run mypy src
check: lint typecheck test
schemas:
	uv run recipeflow schema --contract document --output schemas/recipeflow-document-v1.schema.json
	uv run recipeflow schema --contract graph --output schemas/recipeflow-graph-v1.schema.json
	uv run recipeflow schema --contract diagnostic --output schemas/recipeflow-diagnostic-v1.schema.json
