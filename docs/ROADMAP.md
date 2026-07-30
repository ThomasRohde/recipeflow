# Full roadmap

## M0 — Foundation and contracts

**Outcome:** installable package, public API boundary, CLI entry point, contract naming and golden-test harness.

- Repository scaffold, CI, lint, typing and tests.
- `RecipeDocument`, `RecipeGraph`, `Diagnostic` and result envelopes.
- YAML and JSON parsing.
- Initial schema export.
- Espresso-brownie fixture.

**Exit:** library imports cleanly; CLI delegates to it; schemas are generated deterministically.

## M1 — Validated recipe graph compiler

**Outcome:** Codex can author a recipe and receive actionable diagnostics.

- Ingredients, setup operations, transformations and outputs.
- `inputs`, `requires`, intermediate states and final outputs.
- Unique IDs, reference checks, unused ingredients, final-output checks and acyclic material flow.
- Canonical graph JSON, text and Mermaid renderers.
- `validate`, `compile`, `inspect`, `render`, `schema` commands.
- `$recipeflow-author` Codex skill.

**Exit:** representative simple recipes compile without manual graph editing.

## M2 — Complete recipe semantics

**Outcome:** accurately represent non-linear recipes.

- Split, reserve, divide and recombine materials.
- Optional ingredients, garnish and waste outputs.
- Multiple useful outputs.
- Sections and reusable subrecipes.
- Repetition metadata and sensory completion conditions.
- Alternatives, substitutions and explicit ambiguity.
- Equipment and reusable resource requirements.
- Stronger provenance at field, node and edge level.

**Exit:** golden corpus covers branches, joins, splits, reservations and subrecipes.

## M3 — Layout engine and original tabular notation

**Outcome:** application-independent structured layouts.

- Stable `TabularLayout` contract.
- Row assignment for source materials.
- Operation-column ordering and spanning cells.
- Branch and split representation.
- Collision detection and deterministic layout.
- SVG, accessible HTML and printable output.
- Snapshot and visual-regression tests.

**Exit:** the espresso-brownie example renders as a compact table without manually positioned elements.

## M4 — Authoring ergonomics and agent quality loop

**Outcome:** Codex creates high-quality models reliably.

- `recipeflow init`, format and migrate commands.
- Source evidence blocks and unresolved-question workflow.
- Semantic diff between document or graph versions.
- Repair suggestions and machine-actionable diagnostic fixes.
- Skill evaluation corpus and rubric.
- Independent critic workflow in the skill, without embedding a model in the library.
- Import/export adapters for Cooklang and Schema.org-derived intermediate data.

**Exit:** benchmark recipes meet a defined fidelity score after an autonomous author/critic loop.

## M5 — Application SDK and service adapters

**Outcome:** easy reuse in end-user products.

- Stable application service layer.
- Incremental validation for editors.
- Change sets and source maps.
- Optional FastAPI adapter in a separate package.
- TypeScript types generated from reviewed schemas.
- Browser viewer components in a separate package.
- Persistence-neutral repository protocols.

**Exit:** a web or desktop editor can use the library without importing CLI code.

## M6 — Multi-recipe planning

**Outcome:** coordinate complete meals and constrained kitchens.

- Recipe composition.
- Resource occupancy for ovens, burners, pans and cooks.
- Duration estimates and dependency-aware scheduling.
- Serving-time back-planning.
- Critical path and parallel-work recommendations.
- Shopping-list and mise-en-place projections as derived views.

**Exit:** several recipes can be scheduled against a target serving time and resource limits.

## M7 — Ecosystem and 1.0

**Outcome:** durable open format and extension ecosystem.

- Formal format specification.
- Compatibility and migration policy.
- Renderer and validator plugin interfaces.
- Cross-language conformance suite.
- Accessibility, localization and unit-system strategy.
- Security review of adapters and source handling.
- Performance targets and large-corpus testing.

**Exit:** stable 1.0 contracts with documented extension points and no required AI provider.
