# RecipeFlow authoring language

This document is the human-readable format specification for `recipeflow.document/v1`.
The committed JSON Schema is the structural authority; this document defines semantic
meaning that JSON Schema alone cannot express.

## Document identity

A YAML or JSON document declares its format version and recipe metadata:

```yaml
recipeflow: 1
recipe:
  id: vegetable-pie
  title: Vegetable Pie
  description: A filled pie assembled from pastry and cooked vegetables.
  yield: one 23 cm pie
  locale: en-GB
  source:
    url: https://example.test/vegetable-pie
    title: Original vegetable pie
  notes:
    - Source temperatures are preserved as written.
  tags: [baking, savoury]
```

Identifiers are stable, case-sensitive, and unique in their namespace. Use short
lowercase-hyphenated IDs. Labels remain human-readable and may contain Unicode.

## Evidence and ambiguity

Source text, provenance, and explicit ambiguity are data. Preserve them when a source is
unclear; do not replace uncertainty with an invented fact. Normalized values may sit beside
source wording but never erase it.

Strict validation may require provenance for selected fields. Non-strict validation still
rejects contradictory or structurally impossible semantics.

## Materials

Materials represent physical state that can flow between operations:

- `ingredient`: source material;
- `intermediate`: produced material used later;
- `final`: useful completed output;
- `garnish`: material applied at or near serving;
- `waste`: intentionally discarded output;
- `reserved`: a separated portion held for later use;
- `optional`: material or path that may be omitted explicitly.

Each material preserves a label and may include source quantity text, normalized quantity
and unit, preparation or temperature state, annotations, provenance, and ambiguity.

An ingredient must be consumed by a reachable operation unless it is explicitly optional.
Every non-ingredient material has exactly one producer in a single-recipe graph.

## Operations

Operations transform materials or establish prerequisites. A transformation declares:

```yaml
- id: make-filling
  action: simmer
  label: simmer the vegetable filling
  inputs: [chopped-vegetables, stock]
  requires: [heated-hob]
  equipment: [large-pan]
  duration: 20 min
  temperature: medium heat
  until: vegetables are tender and liquid is reduced
  outputs:
    filling:
      label: reduced vegetable filling
  notes:
    - Stir occasionally.
```

`inputs` are consumed material-flow dependencies. `requires` are non-material
prerequisites, such as a heated oven or prepared tin. These edge types are not
interchangeable.

An operation may produce multiple named outputs for division, reservation, useful
co-products, garnish, or waste. Repetition is metadata on an acyclic operation; never model
repetition by introducing a graph cycle.

## Setup

Setup prepares equipment, workspaces, or environmental conditions:

```yaml
setup:
  - id: preheat-oven
    action: preheat
    target: oven
    temperature: 200 C
    produces: heated-oven
```

The produced prerequisite may be referenced by `requires`. It is not a consumable material.

## Branch, join, split, and reserve

A branch is created when independent operations can proceed from distinct materials. A join
is an operation with multiple inputs. A split or reservation is one operation with multiple
outputs, each named for its resulting state:

```yaml
- id: divide-sauce
  action: divide
  inputs: [finished-sauce]
  outputs:
    serving-sauce: {label: sauce for serving}
    reserved-sauce: {label: sauce reserved for glazing, role: reserved}
```

Every portion that matters later must be explicit. Do not reuse the pre-split material ID
after dividing it.

## Final, garnish, and waste

At least one useful final output is required. Multiple finals are valid when intentional.
Mark discarded outputs as waste and decorative or serving additions as garnish rather than
silently dropping them.

## Subrecipes and reusable components

A subrecipe has its own identity and graph boundary. A parent recipe references one exposed
output and binds each required nested ingredient to a material explicitly listed in the
invoking operation's `inputs`:

```yaml
subrecipe:
  id: sauce
  output: prepared-sauce
  inputs:
    tomatoes: chopped-tomatoes
```

The binding keys are subrecipe ingredient IDs; values are parent material IDs. Compiled
graphs retain typed input bindings and source paths, while `RecipeGraph.subrecipes` carries
each independently compiled boundary. Recursive subrecipe cycles are invalid.

## Quantities, units, temperature, and time

Authored source strings are always permitted when safe normalization is impossible. A
normalized field records value and unit without claiming a conversion the source does not
support. Ranges, approximate amounts, and qualitative values remain explicit.

See [UNITS.md](UNITS.md) for normalization and display policy.

## Compatibility and canonical formatting

Unknown document versions are not guessed. They produce RF6xx compatibility diagnostics.
`recipeflow migrate` performs explicit, deterministic version changes; `recipeflow format`
changes presentation without changing meaning. See
[SCHEMA-VERSIONING.md](SCHEMA-VERSIONING.md).
