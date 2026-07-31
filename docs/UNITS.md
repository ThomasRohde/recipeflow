# Quantity and unit strategy

RecipeFlow preserves what the source says before attempting normalization.

## Source and normalized values

A quantity may include:

- complete source text;
- an optional parsed numeric value or range;
- an optional canonical unit identifier;
- preparation and temperature state;
- provenance and ambiguity.

Normalization is additive. It never discards source text or fabricates precision.

## Conversion

Unit conversion is permitted only when dimensions and assumptions are explicit. Mass and
volume are not interchangeable without ingredient-specific evidence. Qualitative amounts
such as “to taste,” count units, package sizes, and ranges remain representable.

Display systems may select metric or imperial normalized values while retaining source
quantities in the layout or accessibility metadata. Semantic diff distinguishes a display
conversion from an authored quantity change.

## Locale

Parsing may recognize locale-specific decimal notation when the document locale makes it
unambiguous. Canonical machine serialization is locale-independent.
