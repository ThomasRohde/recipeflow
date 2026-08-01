# PNG reconstruction black-box evaluation

This evaluation measures whether a RecipeFlow PNG communicates enough recipe meaning for a
fresh agent to reconstruct the recipe without access to its source document.

It is deliberately outside `src/recipeflow`: RecipeFlow never invokes a model. Codex or
another external evaluation runner supplies fresh agents and records their outputs.

## Information boundary

A reconstruction agent receives:

- one or more committed `.tabular.png` files;
- the minimal human-proxy instruction from
  [reconstruction-prompt.md](reconstruction-prompt.md), embedded in its prompt;
- an output directory.

It must not read RecipeFlow YAML, layouts, SVG, HTML, manifests, documentation, tests, source
code, or another agent's output. It may not communicate with other agents.

The agent writes an ordinary Markdown recipe with no prescribed headings or fields. This
keeps the score about whether the image is self-explanatory to a reader, rather than whether
the reader follows a schema or has been taught the notation. Prompt or serialization defects
are evaluation-harness defects and never count as renderer failures.

The run coordinator partitions the corpus across fresh agents and records the exact input
basenames in each `agent-result.json`. The agents do not share context or communicate.

## Independent judging

Reconstruction and judging are separate phases with fresh agents. Each judge receives only:

- one reconstruction Markdown file;
- the corresponding original RecipeFlow YAML;
- [judge-rubric.md](judge-rubric.md)'s scoring contract.

Each reconstruction receives two independent judgments. A recorded result is:

- `pass` when both judges mark it semantically equivalent;
- `fail` when neither does;
- `review` when the judges disagree.

IDs and harmless wording differences do not matter. Missing ingredients, false joins,
incorrect splits, lost setup dependencies, invented facts, or wrong outputs do.

The judge prompt embeds [judge-rubric.md](judge-rubric.md); judges do not need to read any
other evaluation file.

## Recorded runs

Every run is immutable evidence under `runs/<date>-<name>/`:

```text
run.json
candidates/<agent>/<slug>.reconstruction.md
candidates/<agent>/agent-result.json
judgments/<judge>/<slug>.judgment.json
judgments/<judge>/agent-result.json
REPORT.md
```

New runs pin the SHA-256 digest of every input PNG in `run.json`. The checker refuses to
attribute a recorded judgment to a subsequently regenerated image. Runs recorded before
hash pinning remain readable as legacy evidence but are not selected as the default gate.

Run the deterministic integrity and aggregation check with:

```powershell
uv run python scripts/check_png_blackbox_eval.py evals/png-blackbox/runs/2026-08-01-ledger-v5 --require-all-pass
```

Notation-specific runs set `input_png_root` in `run.json`; the final compact-table gate is
recorded under `runs/2026-07-31-compact-table-v4`: 12 fixtures, 24 independent judgments,
12 passes, no reviews, and no failures. Earlier compact-table runs exposed a missing direct
butter input and a misleading non-contiguous branch span; both findings drove renderer fixes
before the final fresh run.

The checker validates corpus coverage, non-empty reconstructions, reconstruction and judge
boundary attestations, exact candidate/original assignments, judgment score arithmetic,
equivalence-rule consistency, two-judge coverage, notation-specific semantic probes, and the
aggregate report. It does not invoke a model. Legacy JSON reconstruction runs remain
supported and immutable.

A run may use `original_file_overrides` when an evaluation recipe intentionally corrects an
authoring defect in a shared geometry fixture. The input generator takes the matching
`--source-override SLUG=PATH`; both the image hash and exact judge source path remain pinned.
This keeps historical shared-notation artifacts byte-stable while evaluating the recipe
that the current authoring skill would produce.

The final ledger gate is `runs/2026-08-01-ledger-v5`: 36 fresh Markdown reconstructions,
72 independent judgments, 36 passes, zero reviews or failures, 100% membership precision
and recall, exact targeted allocation/output probes, and 24/24 equivalence votes in each of
color, greyscale, and 1-bit. Runs v1-v4 remain preserved failure evidence for renderer,
harness, and authoring-fixture corrections.

Add `--require-all-pass` to make any `review` or `fail` result return a non-zero status.
