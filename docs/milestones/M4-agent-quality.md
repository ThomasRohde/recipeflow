# M4 — Agent authoring quality

## Goal

Add formatting, migrations, semantic diff, repair hints, skill evaluations and critic workflow.

## Required work

The detailed scope, sequencing and dependencies are defined in [`../ROADMAP.md`](../ROADMAP.md). Break this milestone into independently deliverable issues, each with tests and a demonstrable artifact.

## Exit criterion

Autonomous author/critic runs reach the target fidelity score on the benchmark corpus.

## Quality gate

- Public behavior is covered by tests.
- Schema changes are reviewed and versioned.
- Library APIs remain independent of CLI and acquisition mechanisms.
- Documentation and examples are updated.
- Codex can verify the milestone using commands in `AGENTS.md`.
