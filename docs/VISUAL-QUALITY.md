# Visual quality and release evidence

Visual completion requires both automated geometry checks and inspection of actual SVG and
PNG artifacts. String-presence assertions alone are not evidence.

## Automated invariants

Every golden fixture must prove:

- all text boxes, opaque boxes, and lines lie within the canvas;
- no text reports overflow or is silently truncated;
- unrelated content boxes do not overlap;
- text does not intersect unrelated operations or borders;
- setup and final-output content stays within its semantic area;
- SVG `viewBox` encloses all content;
- PNG dimensions match options and contain non-background pixels;
- full source strings remain recoverable;
- SVG, HTML, layout JSON, and PNG derive from one layout;
- repeated output is byte-identical.

## Required corpus

Each slug produces `.tabular-layout.json`, `.tabular.svg`, `.tabular.html`, and
`.tabular.png`. Narrow and wide variants insert `.narrow` or `.wide` before `.tabular`.

| Fixture | Required stress |
| --- | --- |
| `espresso-brownies` | Compact original-style table |
| `long-text` | Long ingredients, setup, and labels |
| `measurement-systems` | Metric and imperial source quantities |
| `branch-and-join` | Independent paths and convergence |
| `split-and-reserve` | Explicit portions and later recombination |
| `multiple-outputs` | Several useful outputs |
| `setup-heavy` | Several prerequisite cards |
| `many-narrow-operations` | Dense operation columns |
| `long-completion-criteria` | Duration, temperature, and `until` wrapping |
| `unicode` | Accents and non-ASCII scripts |
| `compact` | Small recipe at ordinary size |
| `large` | Many materials and operations |

## Manual inspection checklist

For every row above, the release reviewer must:

- [ ] open the SVG;
- [ ] open the PNG at actual size;
- [ ] compare SVG and PNG placement;
- [ ] read every visible ingredient, intermediate, operation, metadata, setup, and output
  string;
- [ ] confirm branch, join, split, and reservation topology;
- [ ] record the reviewer, date, artifact hash, and any defect disposition.

The checked boxes belong in release evidence after inspection; this policy document does not
pre-claim them. Critical or major findings block release.

## PNG-only semantic reconstruction

Geometry checks and manual inspection are complemented by the
[PNG black-box evaluation](../evals/png-blackbox/README.md). Fresh reconstruction agents
receive committed PNGs only and describe the recipe through a neutral JSON contract. Separate
fresh judges compare those descriptions with the original RecipeFlow YAML.

Each fixture receives two independent judgments. The deterministic checker validates the
recorded information-boundary attestations, candidate graph references, score arithmetic,
equivalence policy, corpus coverage, and aggregate report without invoking a model:

```powershell
uv run python scripts/check_png_blackbox_eval.py
```

Use `--require-all-pass` when unanimous semantic equivalence is an acceptance gate. A split
decision remains `review`, rather than being silently treated as a pass.

## Espresso-brownie acceptance

The reference example must retain:

- dense ingredient rows;
- left-to-right execution;
- operation cells spanning combined ingredients;
- setup above the main flow;
- oven temperature and baking time grouped with baking;
- minimal decoration;
- legibility at ordinary display size.

It is an information-architecture target, not a pixel-copy requirement.
