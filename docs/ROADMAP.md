# Roadmap and release gates

RecipeFlow is developed as one coherent library rather than a set of disconnected command
demos. A milestone is complete only when its implementation, portable contracts, tests,
documentation, and demonstrable artifacts pass together.

## M0 - Foundation and contracts

Deliver an installable package, intentional public API, typed result envelopes, thin CLI,
cross-platform CI, deterministic schema generation, and the first golden fixture.

Exit gate: clean install, import, package build, schema determinism, CLI/API equivalence,
and quality checks pass.

## M1 - Validated recipe graph compiler

Deliver YAML and JSON parsing, actionable diagnostics, deterministic graph compilation,
analysis, text/Mermaid/JSON rendering, and the Codex authoring workflow.

Exit gate: representative simple recipes validate and compile through both library and CLI.

## M2 - Complete recipe semantics

Deliver branches, joins, splits, reservations, optional paths, garnish, waste, multiple
outputs, repetition, completion conditions, resources, subrecipes, provenance, and explicit
ambiguity.

Exit gate: the nonlinear semantic corpus compiles without ID reuse or semantic workarounds.

## M3 - Production tabular layout

Deliver real text measurement, wrapping, dynamic row and column sizing, collision
resolution, classic and modern themes, renderer-neutral geometry, and SVG/HTML/PNG output.

Exit gate: all twelve visual fixtures pass automated bounds and collision checks and are
manually inspected at ordinary display size.

## M4 - Authoring ergonomics

Deliver deterministic init/format/migrate/diff workflows, repair suggestions, strong JSON
diagnostics, visual render checking, and an author/critic skill loop.

Exit gate: skill examples and independent evaluations reach semantic and visual acceptance
without hidden manual graph repair.

## M5 - Application SDK

Deliver stable application services, incremental validation, source maps, portable
envelopes, direct layout access, TypeScript declarations, and executable integration
examples.

Exit gate: an in-memory service and editor loop use every core capability without importing
CLI modules.

## M6 - Multi-recipe planning

Deliver recipe composition, shared resource occupancy, duration-aware scheduling, target
serving time, critical path, parallel work, mise-en-place, and shopping projections outside
the core single-recipe graph.

Exit gate: several recipes produce a deterministic, dependency-aware preparation plan.

## M7 - 1.0 readiness

Deliver the formal format and compatibility policy, extension interfaces, localization and
unit strategies, accessibility and security review, performance benchmarks, conformance
fixtures, release automation, changelog, and semantic versioning.

Exit gate: the mandatory gauntlet in `GOAL.md` passes from a clean checkout and the release
artifacts are independently reviewable.

## Honest status

Version `1.0.0` completed M0-M7. Version `1.1.0` added scalable, explicitly registered
layout strategies and the `compact-table` notation. Version `1.2.0` adds the Kitchen
Ledger notation, deterministic print pagination, strategy diagnostics, and the additive
public `allocation-balance` text role without changing the v1 document or layout schema
identifiers. The package version and
[CHANGELOG.md](../CHANGELOG.md) remain the release-status authority. Visual inspection
evidence is recorded in the golden-corpus manifest and review checklist; roadmap prose is
never a substitute for those gates.
