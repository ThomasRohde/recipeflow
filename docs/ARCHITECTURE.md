# Architecture

## Product boundary

RecipeFlow owns an authoring language, deterministic validation, graph compilation,
analysis, layout, rendering, migration, and semantic comparison. It does not retrieve URLs,
scrape pages, run OCR, invoke models, or decide how an author acquires source material.

```text
external source reader / person / authoring agent
                       |
                       v
             RecipeFlow document text
                       |
                       v
CLI / service adapter -> public application services
                              |
                 parse -> validate -> compile
                              |
                     canonical graph
                        /          \
                 analysis          layout
                                      |
                               SVG / HTML / PNG
```

Dependencies point downward. Domain and service modules must never import CLI modules.
Filesystem access belongs to adapters; core services accept strings or typed in-memory
objects.

## Representations

`RecipeDocument`
: Authored, evidence-preserving recipe representation. It favors readable identifiers and
  source wording over premature normalization.

`RecipeGraph`
: Canonical bipartite graph of material and operation nodes connected by typed edges.
  Ordering and generated identifiers are deterministic. Collection fields are deeply
  read-only, and reusable components are retained as independently compiled subrecipe
  boundaries with explicit parent-material input bindings.

`Diagnostic`
: Structured authoring feedback with a stable RF family code, severity, path, related
  paths, suggestions, and optional fix metadata.

`GraphAnalysis`
: Derived topology and planning facts such as joins, branches, unused materials, parallel
  work, and critical path where inputs are known.

`TabularLayout`
: Renderer-neutral, serializable geometry. It includes measured text blocks, boxes, lines,
  accessibility strings, canvas bounds, and validation diagnostics.

`RenderArtifact`
: Media type, format, dimensions or encoding metadata, and text or binary content. Layout
  diagnostics are returned by `render_check`. Rendering never mutates the document or graph.

## Pipeline and failure model

Parsing validates syntax and the versioned structural contract. Semantic validation runs
named rules over a typed document. Compilation is attempted only after blocking diagnostics
are resolved. Analysis and rendering operate on the canonical graph.

Expected authoring, compatibility, layout, and I/O problems are returned as diagnostics or
result envelopes. Unexpected invariant violations may raise a typed RecipeFlow exception;
the CLI catches those at its boundary and maps them to the documented internal-error exit
code.

## Determinism

For identical logical input and options:

- canonical document formatting is byte-identical;
- node, edge, diagnostic, and analysis ordering is stable;
- layout coordinates and rendered bytes are stable on supported platforms;
- schema and TypeScript declaration generation is byte-identical;
- rendering does not mutate input models.

Locale-sensitive formatting, current time, random values, network data, and host font
discovery do not participate in canonical output.

## Layout responsibilities

Typography measures and wraps text. The tabular layout engine assigns lanes and operation
columns, negotiates sizes, routes material lines, and validates collisions. Renderers
serialize an already-complete layout. PNG rasterizes SVG and does not calculate geometry.
See [LAYOUT-ENGINE.md](LAYOUT-ENGINE.md).

## Public boundary

Supported imports originate from `recipeflow` and are listed in
[PUBLIC-API.md](PUBLIC-API.md). Internal module paths may change between minor releases.
Every portable result has an explicit `schema_version`; package version and contract version
are related but not interchangeable.

## Extension boundary

Extensions may add validators, renderers, or analysis projections through documented
interfaces. They must not change core interpretation silently, replace stable diagnostic
codes, perform source retrieval inside core services, or mutate canonical models. See
[EXTENSIONS.md](EXTENSIONS.md).
