.PHONY: install test coverage lint typecheck boundaries benchmark schemas schema-check types types-check docs-check readme-check skill-check sdk-check png-blackbox-check build package-check release-check check

install:
	uv sync --extra dev --extra png

test:
	uv run pytest

coverage:
	uv run pytest --cov=recipeflow --cov-report=term-missing --cov-fail-under=90

lint:
	uv run ruff check .

typecheck:
	uv run mypy src

boundaries:
	uv run python scripts/check_boundaries.py

benchmark:
	uv run python scripts/benchmark_recipeflow.py --check

schemas:
	uv run recipeflow schema --contract document --output schemas/recipeflow-document-v1.schema.json
	uv run recipeflow schema --contract graph --output schemas/recipeflow-graph-v1.schema.json
	uv run recipeflow schema --contract diagnostic --output schemas/recipeflow-diagnostic-v1.schema.json
	uv run recipeflow schema --contract analysis --output schemas/recipeflow-analysis-v1.schema.json
	uv run recipeflow schema --contract tabular-layout --output schemas/recipeflow-tabular-layout-v1.schema.json
	uv run recipeflow schema --contract render-result --output schemas/recipeflow-render-result-v1.schema.json
	uv run recipeflow schema --contract cli-result --output schemas/recipeflow-cli-result-v1.schema.json

schema-check:
	uv run python scripts/check_schemas.py

types:
	uv run python scripts/generate_typescript.py

types-check:
	uv run python scripts/generate_typescript.py --check

docs-check:
	uv run python scripts/check_docs.py

readme-check:
	uv run python scripts/check_readme_examples.py

skill-check:
	uv run python scripts/check_skill.py

sdk-check:
	uv run python scripts/check_sdk_examples.py

png-blackbox-check:
	uv run python scripts/check_png_blackbox_eval.py

build:
	uv build

package-check: build
	uv run python scripts/check_package.py

release-check:
	uv run python scripts/check_release_version.py

check: lint typecheck boundaries coverage schema-check types-check docs-check readme-check skill-check sdk-check png-blackbox-check package-check release-check
