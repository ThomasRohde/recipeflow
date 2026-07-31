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
| espresso-brownies | `257a87157d37` | `31cbb2a27e1b` | Pass | Pass | Pass: compact table | Setup dependencies, inputs, and time range visible |
| long-text | `9e3ed45091f4` | `07273c9ba26d` | Pass | Pass | Pass: wrapped evidence | Setup dependencies, inputs, and time range visible |
| measurement-systems | `9c393414d452` | `2e2ec1a4ba8b` | Pass | Pass | Pass: dry inputs grouped before later additions | Dry-only `whisk` inputs explicit |
| branch-and-join | `7a93eb064ba7` | `d21c623a7469` | Pass | Pass | Pass: independent branches join | Setup dependencies, inputs, and time range visible |
| split-and-reserve | `f2ade7355bbd` | `0d9f264e9f5a` | Pass | Pass | Pass: reserved input rejoins | Correct 250/50 mL branch quantities |
| multiple-outputs | `36eda904c3b5` | `8096cf4dbfe0` | Pass | Pass | Pass: distinct useful outputs | Direct inputs and yield visible |
| setup-heavy | `9758472e4999` | `ef6851728a14` | Pass | Pass | Pass: setup cards and guides | Each card names its dependent operation |
| many-narrow-operations | `805ee6a365cd` | `6f16187e9e0a` | Pass | Pass | Pass: dense operation sequence | Correct allocations and explicit `Time: 5 to 7 min` |
| long-completion-criteria | `92850a11cd58` | `9db88dc66efc` | Pass | Pass | Pass: wrapped criteria | Direct inputs, yield, and time ranges visible |
| unicode | `3680712fd17f` | `a3135e77ccfe` | Pass | Pass | Pass: accents and non-Latin text | Setup dependencies and time ranges visible |
| compact | `43a1775a01e7` | `d39446689abc` | Pass | Pass | Pass: minimal graph | `Time: 3 to 5 min` is unambiguous |
| large | `cef1757305b8` | `1bfe650103b8` | Pass | Pass | Pass: large multi-branch graph | Stock-to-sauce input, setup dependencies, and time ranges explicit |

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
