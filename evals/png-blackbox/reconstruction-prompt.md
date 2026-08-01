# PNG-only human-proxy reconstruction prompt

The run coordinator substitutes the agent ID, assigned PNG paths, and output directory into
this prompt. It intentionally does not explain the notation or prescribe a recipe schema.

> Inspect only the assigned PNG files. For each image, write a standalone recipe in
> `<recipe-name>.reconstruction.md` that a cook could follow. Use only meaning you can obtain from
> the image; preserve uncertainty and do not invent missing facts. Do not explain the visual
> notation. Do not read RecipeFlow YAML, layouts, SVG, HTML, manifests, documentation, tests,
> source code, or another agent's output, and do not communicate with other agents.
>
> After writing all recipes, write `agent-result.json` with the exact assigned PNG basenames:

```json
{
  "input_boundary": "png-only",
  "other_repo_files_read": false,
  "files": ["example--color.tabular.png"]
}
```

The Markdown has no required headings or field names. Its purpose is to capture what an
unbriefed reader believes the image says, not the reader's ability to reproduce RecipeFlow's
data model.
