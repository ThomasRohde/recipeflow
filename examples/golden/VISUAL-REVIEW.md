# Golden visual corpus review

Generated artifacts use the `classic` theme. PNG files are derived from the canonical SVG
through the `resvg-py` backend provided by the `recipeflow[png]` extra. Artifact hashes are
recorded in `manifest.json`; automated geometry and determinism checks are in
`tests/golden/` and `tests/visual/`.

## Review record

Reviewed on **2026-07-31** by **Codex** after semantic-visibility and dependency-routing
corrections. Every regenerated PNG was reopened at original detail; SVG geometry and source
recovery were rechecked against the same layouts.

| Fixture | SVG SHA-256 | PNG SHA-256 | Visible text | SVG/PNG parity | Topology | Defect disposition |
| --- | --- | --- | --- | --- | --- | --- |
| espresso-brownies | `5e07ca6784a3` | `31cbb2a27e1b` | Pass | Pass | Pass: compact table | Setup dependencies, inputs, and time range visible |
| long-text | `6e7bed077792` | `07273c9ba26d` | Pass | Pass | Pass: wrapped evidence | Setup dependencies, inputs, and time range visible |
| measurement-systems | `cea41650dffa` | `2e2ec1a4ba8b` | Pass | Pass | Pass: dry inputs grouped before later additions | Dry-only `whisk` inputs explicit |
| branch-and-join | `17c4885619b5` | `d21c623a7469` | Pass | Pass | Pass: independent branches join | Setup dependencies, inputs, and time range visible |
| split-and-reserve | `e39a28fd49f9` | `0d9f264e9f5a` | Pass | Pass | Pass: reserved input rejoins | Correct 250/50 mL branch quantities |
| multiple-outputs | `5009fdc04270` | `8096cf4dbfe0` | Pass | Pass | Pass: distinct useful outputs | Direct inputs and yield visible |
| setup-heavy | `1ccdbc245eee` | `ef6851728a14` | Pass | Pass | Pass: setup cards and guides | Each card names its dependent operation |
| many-narrow-operations | `96c4ccbc0bfb` | `6f16187e9e0a` | Pass | Pass | Pass: dense operation sequence | Correct allocations and explicit `Time: 5 to 7 min` |
| long-completion-criteria | `9ca9cdec5ae2` | `9db88dc66efc` | Pass | Pass | Pass: wrapped criteria | Direct inputs, yield, and time ranges visible |
| unicode | `2e98ec1fb323` | `a3135e77ccfe` | Pass | Pass | Pass: accents and non-Latin text | Setup dependencies and time ranges visible |
| compact | `e8a803493e62` | `d39446689abc` | Pass | Pass | Pass: minimal graph | `Time: 3 to 5 min` is unambiguous |
| large | `27209b327759` | `1bfe650103b8` | Pass | Pass | Pass: large multi-branch graph | Stock-to-sauce input, setup dependencies, and time ranges explicit |

## Method and findings

- Every committed PNG was opened at original or high detail and compared with the intended
  fixture topology. All visible labels, source evidence, setup notes, operation details, and
  output text remain inside their assigned geometry.
- Every SVG was reviewed through its direct `resvg-py` raster. The PNG is generated from that
  exact committed SVG, so the raster review exercises the SVG geometry and text placement.
  Automated checks independently parse every SVG as XML and verify its title, description,
  view box, accessibility metadata, source-text recovery, and exact PNG dimensions.
- The corpus exposed and now covers renderer regressions including vertically overflowing
  action text, aspect-fit PNG dimension drift, omitted source/preparation evidence, Unicode
  fallback-width mismatch, omitted allocation quantities and targets, collapsed setup
  dependency guides, and misleading source-lane ordering. No unresolved visual defect
  remains in the reviewed artifacts.

## Compact-table notation review

The parallel `compact-table/` corpus was reviewed on **2026-07-31** at original or high
detail after first-use ingredient grouping and linked non-contiguous span handling were
implemented. Its manifest independently pins all four derived artifacts for all 12 source
recipes.

| Fixture | SVG SHA-256 | PNG SHA-256 | Span semantics | Defect disposition |
| --- | --- | --- | --- | --- |
| espresso-brownies | `c93027d98eb5` | `f4a2ad0ce906` | Pass | Nested wet and dry stages are distinct |
| long-text | `f2f214e3c170` | `0a1a53f4fabc` | Pass | Independent pear and custard branches remain distinct; setup notes are explicit |
| measurement-systems | `d93fca9c3e7d` | `eeb849aa3263` | Pass | `whisk` spans and names flour, baking powder, and salt only |
| branch-and-join | `6294d97ca97b` | `282b9081f13c` | Pass | Independent branches converge visibly |
| split-and-reserve | `b4b48617aee8` | `14dbdc380f81` | Pass | Divide and reserved-cream path remain explicit |
| multiple-outputs | `ecdb41d5a288` | `d88016cff1fd` | Pass | Both useful outputs remain separate |
| setup-heavy | `f2857396fba4` | `445665eb10cc` | Pass | Direct butter addition and five setup rows are explicit |
| many-narrow-operations | `7befcdd99bb4` | `960b4b358140` | Pass | Dense sequence stays complete and readable |
| long-completion-criteria | `a2f7ce358ef7` | `731f3a0546cd` | Pass | Full completion criteria remain inside spans |
| unicode | `7b1bcc97af82` | `982ed6d4cd52` | Pass | Accents, Greek, and Japanese remain visible |
| compact | `6cdf23c4339f` | `1f254850ea49` | Pass | Minimal two-row case remains compact |
| large | `ea3d42f761c3` | `a96d8629e415` | Pass | Dependency branches stay grouped without false inputs |
