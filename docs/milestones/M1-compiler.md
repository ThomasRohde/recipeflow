# M1 - Validated graph compiler

## Deliverables

- YAML and JSON parsing with structured syntax and structure diagnostics;
- semantic validation for identifiers, references, finals, usage, and cycles;
- deterministic canonical material/operation graph;
- topology and usage analysis;
- text, Mermaid, and JSON output;
- a source-independent Codex authoring skill.

## Evidence

Simple sequence, setup, branch, and join fixtures must produce equivalent public-library and
CLI results. Equivalent source mapping order must not change canonical graph bytes.

## Exit

An author can repair all diagnostics and compile representative recipes without editing a
graph by hand.
