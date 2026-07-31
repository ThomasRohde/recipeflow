# Extension interfaces

Extensions are optional adapters around stable RecipeFlow contracts. Core interpretation
remains deterministic when no extension is installed.

Supported extension categories may include:

- additional validation rules with namespaced diagnostic codes;
- renderers consuming a public layout or graph;
- analysis projections that do not mutate canonical models;
- import/export adapters in separate packages.

Extensions must:

- declare supported contract versions;
- avoid monkey-patching core models or diagnostic meanings;
- accept and return public models or portable mappings;
- preserve source evidence;
- be deterministic for equal input and options;
- report expected failures as diagnostics;
- keep URL retrieval and model invocation outside core execution.

An extension cannot silently relax core validation. The v1 core models reject unknown
fields. Extension packages therefore wrap public models or store namespaced data outside
the v1 document; adding an in-document extension field requires an explicit contract
revision and migration policy.
