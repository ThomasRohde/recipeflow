# PNG black-box evaluation: 2026-08-01-ledger-v2

Status: **failed and superseded**.

This run preserved 36 PNG-only reconstructions and 72 independent comparison judgments.
It is retained as failure evidence, but it is not a release-gate result.

## Product findings

- The consumed column displayed `source_text` instead of the canonical ingredient label.
  When those fields carried distinct meaning, the image could omit facts. The long-text
  fixture exposed this by losing “with no bitter papery fragments remaining” from the
  hazelnut description.
- One 1-bit reconstruction omitted the setup-heavy fixture's 15-minute chilling condition
  and 200 °C preheat condition. The values were present but not explicitly labeled in the
  standing-conditions band, so the renderer was revised to label setup time and temperature.

## Harness finding

The structured reconstruction schema had no quantity field for operation outputs. A reader
could see that the split produced 250 mL mousse cream and 50 mL held cream, but could not
record that mapping in the prescribed output structure. Several judgments therefore
reported an allocation failure that was created by the test harness, not the PNG.

Other judgments treated a null `source_text` field as semantic failure even when the same
culinary meaning was preserved in ordinary ingredient wording. That measured schema
compliance rather than human readability.

## Corrective action

- Render canonical ingredient labels and authored source lines together when both exist.
- Prefix setup parameters with `Time` and `Temperature`.
- Replace schema-shaped reconstruction with a minimal, ordinary Markdown recipe task.
- Judge culinary equivalence, not byte-for-byte source evidence or RecipeFlow field usage.

No v2 rate is presented as a product-quality claim. The corrected renderer requires a fresh
run with new readers and judges.
