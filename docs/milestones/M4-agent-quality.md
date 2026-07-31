# M4 - Authoring ergonomics and agent quality

## Deliverables

Deterministic init, format, migrate, semantic diff, repair suggestions, strong JSON
diagnostics, render checking, and an author/critic workflow.

## Evidence

Every bundled skill example validates, compiles, renders classic SVG and PNG, passes
render-check, and is visually inspected. Migration dry-run performs no write; formatting is
idempotent; semantic diff ignores formatting-only changes.

## Exit

A fresh authoring agent can produce and repair a faithful document using only the skill and
public tools, with no embedded model behavior in RecipeFlow.
