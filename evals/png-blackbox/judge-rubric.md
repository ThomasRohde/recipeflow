# Human-proxy recipe equivalence rubric

Compare the reconstructed recipe with the original RecipeFlow YAML. Judge whether a cook
given only the reconstruction would understand materially the same recipe. Do not inspect
the source PNG or another judgment.

Do not penalize IDs, Markdown structure, field placement, harmless reordering of independent
work, wording, abbreviations, or failure to copy `source_text` verbatim when its culinary
meaning survives elsewhere. Do record missing or invented ingredients, quantities, setup,
operations, dependencies, splits, reserves, joins, temperatures, durations, completion
criteria, or outputs.

## Scores

Score each dimension from 0 to 4:

- `4`: complete and faithful;
- `3`: equivalent with only immaterial wording or precision differences;
- `2`: meaningful omission or unsupported inference;
- `1`: severe loss or contradiction;
- `0`: absent or fundamentally wrong.

Dimensions are `metadata`, `ingredients`, `setup`, `operations`, `flow_topology`,
`temporal_completion`, `outputs_roles`, and `evidence_discipline`.

Set `semantically_equivalent` to true only when there are no critical or major findings, the
total is at least 28 of 32, and `ingredients`, `operations`, `flow_topology`, and
`outputs_roles` are each at least 3. A critical finding is a lost or invented material, a
wrong dependency that changes execution, an invalid final product, or an invented
safety-relevant fact. A major finding is another omission or contradiction that could make a
cook execute a materially different recipe. Pure transcription or formatting differences
are minor at most.

Also report the following probes:

- membership precision and recall over the union of ingredients, setup actions, operations,
  and outputs;
- `allocation_arithmetic`;
- `setup_discrimination`;
- `branch_join_interpretation`;
- `direct_input_survival`;
- `output_inventory`;
- `completion_criteria`;
- `round_trip_equivalence`.

Use `pass`, `fail`, or `not_applicable` for status probes. `round_trip_equivalence` means a
cook could recreate the recipe's culinary meaning; it does not require byte-for-byte YAML or
verbatim source evidence.

Write one `<assigned-slug>.judgment.json` per pair using
`recipeflow.png-semantic-judgment/v1`, with
the eight integer scores, their `total_score`, arrays of `critical_findings`,
`major_findings`, and `minor_findings` (each item has `summary` and `evidence`), the boolean
vote, confidence from 0 to 1, rationale, and all nine probe results. After all judgments,
write `agent-result.json` listing the exact candidate/original pairs read, with
`input_boundary` set to `candidate-and-original-only` and `other_repo_files_read` false.
