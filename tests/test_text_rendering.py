from __future__ import annotations

from recipeflow import build, render

SOURCE = """\
recipeflow: 1
recipe:
  id: readable-text
  title: Readable Text Recipe
  description: A small recipe used to prove that text output is safe to follow.
  source:
    title: Test kitchen card
    author: RecipeFlow
    url: https://example.com/readable-text
  yield: 2 portions
  tags: [test, baked]
  notes: [Serve while warm.]
  ambiguity:
    - description: The source does not specify a pan shape.
ingredients:
  flour:
    label: all-purpose flour
    quantity: 1 cup
    source_text: 1 cup all-purpose flour, spooned and levelled
    annotations: [Spoon into the cup rather than scooping.]
  salt:
    label: fine salt
    quantity: 1 pinch
    optional: true
setup:
  - id: heat-oven
    action: preheat
    label: preheat the oven
    target: oven
    temperature: 200 C
    produces: hot-oven
operations:
  - id: z-mix
    action: mix the flour and optional salt
    inputs: [flour, {material: salt, optional: true}]
    outputs:
      dough: {label: rough dough}
    notes: [Do not overmix.]
    ambiguity:
      - description: The source does not define how rough the dough should look.
  - id: a-bake
    action: bake the dough
    inputs: [dough]
    requires: [hot-oven]
    duration: 20 min
    until: golden at the edges
    repeat:
      count: 2
    outputs:
      portions: {label: baked portions, quantity: "2", final: true}
"""


def test_text_render_is_self_contained_and_topological() -> None:
    result = build(SOURCE)
    assert result.ok and result.graph is not None

    artifact = render(result.graph, "text")
    assert isinstance(artifact.content, str)
    text = artifact.content

    assert "Yield: 2 portions" in text
    assert "Source: RecipeFlow · Test kitchen card · https://example.com/readable-text" in text
    assert "Ingredients\n-----------" in text
    assert "Note: Serve while warm." in text
    assert "Ambiguity: The source does not specify a pan shape." in text
    assert "1 cup all-purpose flour" in text
    assert "Source wording: 1 cup all-purpose flour, spooned and levelled" in text
    assert "1 pinch fine salt [optional]" in text
    assert "Standing conditions\n-------------------" in text
    assert "Required by: step 2" in text
    assert "Temperature: 200 C" in text
    assert text.index("1. mix the flour") < text.index("2. bake the dough")
    assert "Uses: 1 cup all-purpose flour; 1 pinch fine salt [optional]" in text
    assert "Time: 20 min" in text
    assert "Until: golden at the edges" in text
    assert "Repeat: 2 times" in text
    assert "Note: Do not overmix." in text
    assert "Ambiguity: The source does not define" in text
    assert "Final: 2 baked portions" in text


def test_text_render_does_not_duplicate_counts_already_in_labels() -> None:
    result = build(SOURCE)
    assert result.ok and result.graph is not None
    graph = result.graph.model_copy(
        update={
            "nodes": tuple(
                node.model_copy(update={"label": "two baked portions"})
                if getattr(node, "id", None) == "portions"
                else node
                for node in result.graph.nodes
            )
        }
    )

    text = render(graph, "text").content
    assert isinstance(text, str)
    assert "2 two baked portions" not in text
    assert "Final: two baked portions" in text


def test_text_render_never_exposes_internal_operation_or_material_ids() -> None:
    result = build(SOURCE)
    assert result.ok and result.graph is not None

    text = render(result.graph, "text").content
    assert isinstance(text, str)
    assert "z-mix" not in text
    assert "a-bake" not in text
    assert "hot-oven" not in text
