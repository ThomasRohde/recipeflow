# Contributing

## Setup

```powershell
uv sync --extra dev --extra png
uv run recipeflow validate examples/espresso-brownies.recipe.yaml --json
```

Python workflows must work on Windows and Linux. Do not require Bash from Python code or
ordinary user instructions.

## Before changing a contract

1. Identify the affected public models, schemas, diagnostics, CLI envelope, and docs.
2. Decide whether the change is backward compatible under
   [SCHEMA-VERSIONING.md](SCHEMA-VERSIONING.md).
3. Add contract and golden fixtures before or with implementation.
4. Preserve unknown source evidence and real ambiguity.
5. Add migration behavior for an intentional breaking change.

## Tests

Keep test responsibilities explicit:

```text
tests/unit
tests/contract
tests/golden
tests/cli
tests/visual
tests/integration
```

Add property tests for arbitrary text, Unicode, acyclic topology, deterministic ordering,
and bounds where useful. Never weaken an invariant or snapshot merely to make a change pass.

## Visual changes

Generate all four artifacts for affected fixtures, run layout validation, and open the SVG
and PNG. Compare actual content at ordinary display size and record review evidence in the
release report. Do not accept truncation, invisible text, or a huge canvas as a fix.

## Full gate

Run the commands in [AGENTS.md](../AGENTS.md), including coverage, schemas, TypeScript
declarations, documentation, skill examples, build, and CLI smoke checks.

## Pull requests

Describe:

- user-visible and contract changes;
- diagnostics or migration behavior;
- commands and results;
- generated artifacts inspected;
- compatibility and security impact;
- known limitations.

Keep generated schemas, declarations, and golden artifacts in the same change as their
source.
