# Architecture

## Product boundary

RecipeFlow owns a recipe authoring language, deterministic validation, graph compilation, analysis, layout and rendering. It does not retrieve URLs, scrape pages, invoke models, perform OCR or decide how Codex acquires source material.

## Dependency rule

```text
CLI / HTTP / desktop adapters
            ↓
       public API
            ↓
parsing, validation, compilation, analysis, layout, rendering
            ↓
        domain models
```

Imports must never point upward.

## Core representations

- `RecipeDocument`: concise authoring representation written by Codex or humans.
- `RecipeGraph`: canonical normalized bipartite graph of material and operation nodes.
- `Diagnostic`: stable machine-readable feedback.
- `GraphAnalysis`: derived topology and quality information.
- `LayoutModel`: renderer-independent geometry for applications.

## Public API policy

The root `recipeflow` package exposes supported APIs. Internal modules may change. Public models include explicit schema-version fields. Expected invalid input returns diagnostics rather than raising.

## Portability

Pydantic models are the reference implementation. Committed JSON Schemas and golden fixtures allow future TypeScript, Rust or Kotlin implementations to match the same contracts.
