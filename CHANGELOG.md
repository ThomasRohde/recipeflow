# Changelog

All notable changes are recorded here. RecipeFlow follows
[Semantic Versioning](https://semver.org/) for the Python package and separately versions
its serialized contracts as described in
[docs/SCHEMA-VERSIONING.md](docs/SCHEMA-VERSIONING.md).

## 1.1.0 - 2026-07-31

### Added

- Add a public, explicitly registered layout-strategy API with the original `flow`
  notation as the backward-compatible default.
- Add an original-inspired `compact-table` notation whose ingredient rows and nested,
  linked operation spans expose recipe participation directly in the grid geometry.
- Expose notation selection consistently through the Python API and the `render` and
  `render-check` CLI commands while keeping visual themes orthogonal.

### Fixed

- Render recipe yield, setup targets, split-output quantities, and edge-specific input
  allocations so the tabular PNG does not omit recipe semantics needed to reconstruct the
  recipe.
- Route setup dependencies through distinct corridors and operation anchors instead of an
  ambiguous shared guide, and state each dependency in the setup card text.
- List direct source-material inputs inside operation cells so dense row spans cannot hide
  which operation consumes a material.
- Render authored duration ranges as explicit `Time: … to …` text in human-facing output
  while preserving the original range string in the structured layout contract.
- Group an operation's source lanes together so unrelated later ingredients do not appear
  to feed an earlier operation.

## 1.0.0 - 2026-07-30

### Added

- Complete recipe semantics for non-linear flows, evidence, ambiguity, and subrecipes.
- Versioned result envelopes, schema migration, semantic diff, and application services.
- Renderer-neutral tabular layouts with classic and modern SVG, HTML, and PNG output.
- Visual bounds validation, a representative golden corpus, and author/critic skill flow.
- Executable SDK examples, TypeScript declaration generation, compatibility policy, and
  release-quality documentation.
- Cross-platform CI gates for coverage, schemas, documentation, packaging, and Windows.

### Changed

- Refactored the initial fixed-size renderer into typed typography, layout, and rendering
  responsibilities.
- Expanded CLI machine mode and documented stable exit codes.

### Compatibility

- Existing `recipeflow: 1` documents remain readable.
- Any migration that changes serialized form must preserve source evidence and report
  structured RF6xx diagnostics.

## 0.1.0 - Initial scaffold

### Added

- Library-first package boundary.
- YAML and JSON parsing, validation, graph compilation, and analysis.
- Text, Mermaid, canonical JSON, and baseline tabular rendering.
- Thin Typer CLI and initial Codex authoring skill.
- Initial document, graph, and diagnostic schemas.

This release is a development scaffold, not a stable 1.0 format promise.
