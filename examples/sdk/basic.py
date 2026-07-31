"""Build and render a RecipeFlow document entirely in memory."""

from recipeflow import build, render

SOURCE = """
recipeflow: 1
recipe: {id: tea, title: Tea}
ingredients:
  water: {label: water, quantity: 250 ml}
  leaves: {label: tea leaves, quantity: 2 tsp}
operations:
  - id: steep
    action: steep
    inputs: [water, leaves]
    duration: 4 min
    outputs:
      tea: {label: brewed tea, role: final, final: true}
"""


def main() -> None:
    result = build(SOURCE)
    assert result.ok, result.diagnostics
    assert result.graph is not None

    artifact = render(result.graph, "tabular-svg")
    assert artifact.media_type == "image/svg+xml"
    assert "Tea" in artifact.content
    print(result.graph.recipe_id, artifact.media_type)


if __name__ == "__main__":
    main()
