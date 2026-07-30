# M0 — Foundation and contracts

## Goal

Establish the package, public contracts, CI, fixtures and compatibility rules.

## Required work

The detailed scope, sequencing and dependencies are defined in [`../ROADMAP.md`](../ROADMAP.md). Break this milestone into independently deliverable issues, each with tests and a demonstrable artifact.

## Exit criterion

Package imports; schemas generate; CLI is a thin adapter; first golden fixture passes.

## Quality gate

- Public behavior is covered by tests.
- Schema changes are reviewed and versioned.
- Library APIs remain independent of CLI and acquisition mechanisms.
- Documentation and examples are updated.
- Codex can verify the milestone using commands in `AGENTS.md`.
