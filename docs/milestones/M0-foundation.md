# M0 - Foundation and contracts

## Deliverables

- installable Python package and thin CLI entry point;
- public in-memory service boundary and typed result models;
- stable diagnostic structure and deterministic schema export;
- Windows and Linux CI for lint, typing, tests, coverage, docs, and build;
- first semantic and visual fixture.

## Evidence

M0 is complete only when a clean checkout passes `uv sync --frozen --extra dev --extra png`,
the commands in [AGENTS.md](../../AGENTS.md), and an isolated wheel smoke test. Generated
schemas and declarations must leave no diff.

## Risks to reject

Do not put recipe semantics in CLI commands, depend on filesystem access from core services,
or treat a successful source import as packaging evidence.
