from pathlib import Path
from recipeflow import build, render

FIXTURE=Path(__file__).parents[1]/"examples"/"espresso-brownies.recipe.yaml"

def test_build_example():
    result=build(FIXTURE.read_text(encoding="utf-8"))
    assert result.ok
    assert result.graph is not None
    assert result.graph.final_material_ids==["brownies"]
    assert result.analysis is not None
    assert result.analysis.ingredient_count==9

def test_mermaid_renderer():
    result=build(FIXTURE.read_text(encoding="utf-8"))
    assert result.graph is not None
    artifact=render(result.graph,"mermaid")
    assert artifact.content.startswith("flowchart LR")
    assert "brownies" in artifact.content
