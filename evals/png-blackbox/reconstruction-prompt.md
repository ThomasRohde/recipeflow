# PNG-only reconstruction prompt

The run coordinator substitutes the agent ID, assigned PNG paths, and output directory into
this prompt. The schema is intentionally neutral and is not the RecipeFlow document schema.

> Inspect only the assigned PNG files. Do not read RecipeFlow YAML, layouts, SVG, HTML,
> manifests, documentation, tests, source code, or another agent's output. Do not communicate
> with other agents. Reconstruct the recipe meaning visible in each PNG: ingredients,
> quantities, preparation, setup prerequisites, operations, material flow, durations,
> temperatures, completion criteria, repeats, intermediate roles, and final outputs. Preserve
> visible ambiguity and do not invent missing facts.
>
> Write one `<slug>.reconstruction.json` per PNG using
> `recipeflow.png-reconstruction/v1`:

```json
{
  "schema_version": "recipeflow.png-reconstruction/v1",
  "slug": "example",
  "title": "Visible title",
  "yield_text": null,
  "setup": [
    {
      "id": "setup-id",
      "action": "Visible setup action",
      "target": null,
      "temperature": null,
      "duration": null,
      "produces": "prerequisite-id",
      "required_by": ["operation-id"]
    }
  ],
  "ingredients": [
    {
      "id": "ingredient-id",
      "label": "ingredient",
      "quantity": "visible quantity",
      "source_text": "visible source line",
      "preparation": null,
      "optional": false
    }
  ],
  "operations": [
    {
      "id": "operation-id",
      "action": "Visible action",
      "inputs": ["ingredient-id"],
      "outputs": [
        {
          "id": "output-id",
          "label": "visible output",
          "role": "final"
        }
      ],
      "requires": ["prerequisite-id"],
      "duration": null,
      "temperature": null,
      "until": null,
      "repeat": null
    }
  ],
  "final_output_ids": ["output-id"],
  "ambiguities": [],
  "evidence_notes": []
}
```

> Allowed output roles are `intermediate`, `final`, `reserved`, `waste`, and `garnish`.
> References must resolve within the JSON. After writing all candidates, write
> `agent-result.json` containing the exact assigned PNG basenames:

```json
{
  "input_boundary": "png-only",
  "other_repo_files_read": false,
  "files": ["example.tabular.png"]
}
```
