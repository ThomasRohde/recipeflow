# Schema versioning and compatibility

RecipeFlow versions serialized contracts independently from the Python package. Consumers
must inspect the contract's discriminator rather than infer it from `recipeflow.__version__`.

## Required v1 contracts

| Contract discriminator | Committed schema |
| --- | --- |
| `recipeflow.document/v1` | `schemas/recipeflow-document-v1.schema.json` |
| `recipeflow.graph/v1` | `schemas/recipeflow-graph-v1.schema.json` |
| `recipeflow.diagnostic/v1` | `schemas/recipeflow-diagnostic-v1.schema.json` |
| `recipeflow.analysis/v1` | `schemas/recipeflow-analysis-v1.schema.json` |
| `recipeflow.tabular-layout/v1` | `schemas/recipeflow-tabular-layout-v1.schema.json` |
| `recipeflow.render-result/v1` | `schemas/recipeflow-render-result-v1.schema.json` |
| `recipeflow.cli-result/v1` | `schemas/recipeflow-cli-result-v1.schema.json` |

Additional diff, migration, and planning result schemas may be published without weakening
these core contracts.

## Compatibility rules

Within a contract major version, a change may:

- add an optional field with a semantic default;
- add a diagnostic code;
- clarify prose without changing accepted meaning;
- extend an open extension namespace.

A change requires a new contract major version when it:

- removes or renames a field;
- changes a field's type or meaning;
- makes previously valid data invalid without an explicit policy version;
- changes canonical ordering or identifier generation;
- reinterprets an existing enum value or diagnostic code.

Schemas use `additionalProperties: false` for core objects. Extensibility must use a
documented extension field rather than accepting arbitrary misspellings.

## Package policy

Before 1.0, the changelog must identify any compatibility-impacting change and provide a
migration. At 1.0 and later:

- package patch releases preserve all public contracts;
- package minor releases may add backward-compatible fields or capabilities;
- package major releases may introduce a new contract major version;
- readers continue supporting the previous document major for the documented deprecation
  window.

## Migration

`recipeflow migrate`:

- detects the source version;
- rejects unknown versions with RF6xx diagnostics;
- preserves source data and provenance;
- reports every semantic or representational change;
- produces deterministic output;
- supports `--dry-run`;
- never overwrites the original without explicit authorization.

Formatting is not migration. `recipeflow format` may reorder and normalize presentation but
must preserve the same parsed meaning.

## Deterministic generation

Schemas are generated from reviewed reference models and committed. The check:

```powershell
uv run python scripts/check_schemas.py
```

regenerates all required contracts in memory and fails on missing or byte-different files.
TypeScript declarations are derived from the committed schemas:

```powershell
uv run python scripts/generate_typescript.py --check
```

Schema and declaration diffs receive the same review as source changes.
