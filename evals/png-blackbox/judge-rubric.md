# PNG reconstruction semantic-equivalence rubric

Judge the reconstruction against the original recipe, not against IDs, formatting, or exact
schema shape. Do not inspect the source PNG or another judgment.

## Scores

Score each dimension from 0 to 4:

- `4`: semantically complete and faithful;
- `3`: equivalent with only immaterial wording or precision differences;
- `2`: partial fidelity with a meaningful omission or unsupported inference;
- `1`: severe loss or contradiction;
- `0`: absent or fundamentally wrong.

Dimensions:

1. `metadata`: title, yield, locale-relevant wording, and identity.
2. `ingredients`: ingredient coverage, quantities, preparation states, and optionality.
3. `setup`: setup actions, conditions, and the operations that depend on them.
4. `operations`: action coverage, sequence, and operation-level meaning.
5. `flow_topology`: material producers/consumers, branches, joins, splits, reservations,
   recombination, and prerequisites.
6. `temporal_completion`: durations, temperatures, repetition, and completion criteria.
7. `outputs_roles`: intermediate labels, final outputs, useful co-outputs, garnish, reserved
   portions, and waste.
8. `evidence_discipline`: no invented facts and explicit ambiguity where the image cannot
   resolve a fact.

## Findings and equivalence

Classify findings:

- `critical`: lost material, wrong dependency that changes the recipe, invalid final
  product, or invented safety-relevant fact;
- `major`: missing ingredient or operation, false branch/join/split/reservation, material
  confused with setup, wrong output role, or significant fidelity loss;
- `minor`: naming or wording difference that does not change recipe meaning.

Set `semantically_equivalent` to `true` only when:

- there are no critical or major findings;
- the total score is at least 28 of 32;
- `ingredients`, `operations`, `flow_topology`, and `outputs_roles` are each at least 3.

The deterministic checker recomputes this rule.

After all judgments, the judge records the exact candidate/original pairs it read in
`agent-result.json`, with `input_boundary` set to `candidate-and-original-only` and
`other_repo_files_read` set to `false`.
