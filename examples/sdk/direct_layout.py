"""Use the renderer-neutral TabularLayout directly."""

from recipeflow import build, create_tabular_layout

SOURCE = """
recipeflow: 1
recipe: {id: fruit-bowl, title: Fruit Bowl}
ingredients:
  apple: {label: apple, quantity: "1"}
  pear: {label: pear, quantity: "1"}
operations:
  - id: combine
    action: combine
    inputs: [apple, pear]
    outputs:
      fruit-bowl: {label: fruit bowl, role: final, final: true}
"""


def main() -> None:
    result = build(SOURCE)
    assert result.graph is not None

    layout = create_tabular_layout(result.graph)
    payload = layout.model_dump(mode="json")
    assert payload["schema_version"] == "recipeflow.tabular-layout/v1"
    assert payload["width"] > 0
    assert payload["height"] > 0
    print(payload["schema_version"], payload["width"], payload["height"])


if __name__ == "__main__":
    main()
