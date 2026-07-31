# PNG reconstruction black-box evaluation

This evaluation measures whether a RecipeFlow PNG communicates enough recipe meaning for a
fresh agent to reconstruct the recipe without access to its source document.

It is deliberately outside `src/recipeflow`: RecipeFlow never invokes a model. Codex or
another external evaluation runner supplies fresh agents and records their outputs.

## Information boundary

A reconstruction agent receives:

- one or more committed `.tabular.png` files;
- the neutral `recipeflow.png-reconstruction/v1` output shape from
  [reconstruction-prompt.md](reconstruction-prompt.md), embedded in its prompt;
- an output directory.

It must not read RecipeFlow YAML, layouts, SVG, HTML, manifests, documentation, tests, source
code, or another agent's output. It may not communicate with other agents.

The neutral reconstruction format prevents knowledge of the RecipeFlow document schema from
becoming part of the image-comprehension score.

The run coordinator partitions the corpus across fresh agents and records the exact input
basenames in each `agent-result.json`. The agents do not share context or communicate.

## Independent judging

Reconstruction and judging are separate phases with fresh agents. Each judge receives only:

- one reconstruction JSON file;
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
candidates/<agent>/<slug>.reconstruction.json
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
uv run python scripts/check_png_blackbox_eval.py evals/png-blackbox/runs/2026-07-31-golden-v5
```

The checker validates corpus coverage, reconstruction and judge boundary attestations,
reconstruction graph references, exact candidate/original assignments, judgment score
arithmetic, equivalence-rule consistency, two-judge coverage, and the aggregate report. It
does not invoke a model.

Add `--require-all-pass` to make any `review` or `fail` result return a non-zero status.
