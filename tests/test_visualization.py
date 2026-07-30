from pathlib import Path

from recipeflow import build, render


def test_tabular_svg_is_a_real_self_contained_visualization() -> None:
    source = Path("examples/espresso-brownies.recipe.yaml").read_text(encoding="utf-8")
    result = build(source)
    assert result.ok and result.graph is not None
    artifact = render(result.graph, "tabular-svg")
    assert artifact.media_type == "image/svg+xml"
    assert artifact.content.startswith("<svg")
    assert "Espresso Brownies" in artifact.content
    assert "melt" in artifact.content
    assert artifact.content.count("class=\"op\"") >= 4
    assert "115 g" in artifact.content


def test_tabular_layout_is_portable_json() -> None:
    source = Path("examples/espresso-brownies.recipe.yaml").read_text(encoding="utf-8")
    result = build(source)
    assert result.ok and result.graph is not None
    artifact = render(result.graph, "tabular-layout")
    assert artifact.media_type == "application/json"
    assert "recipeflow.tabular-layout/v1" in artifact.content
