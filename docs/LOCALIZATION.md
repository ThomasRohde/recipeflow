# Localization strategy

Canonical identifiers, enum values, schema fields, and diagnostic codes are
locale-independent. Human labels, source strings, and translated messages are separate.

- Preserve the recipe's declared locale and original Unicode.
- Do not translate authored ingredient or operation text during parse or compile.
- Localize presentation messages through adapter catalogs keyed by stable diagnostic code.
- Keep JSON machine output stable regardless of process locale.
- Use Unicode-aware wrapping and measurement; never assume Latin script or whitespace-only
  word boundaries.
- Record language and text direction in accessible HTML when known.

Localization may change displayed wording but never graph identity, ordering, quantities, or
semantic diff results.
