from __future__ import annotations

import html
import json
from pathlib import Path
from runpy import run_path

SCRIPT = run_path(str(Path(__file__).parents[1] / "scripts" / "build_recipe_site.py"))
NOTATIONS = SCRIPT["NOTATIONS"]
build_site = SCRIPT["build_site"]


def test_recipe_site_builds_every_recipe_in_every_notation(tmp_path: Path) -> None:
    output = tmp_path / "site"
    build_site(output_dir=output)

    manifest = json.loads((output / "recipes.json").read_text(encoding="utf-8"))
    assert manifest["recipe_count"] == 18
    assert manifest["recipes"][0]["slug"] == "aligot"
    assert {item["slug"] for item in manifest["recipes"]} == {
        "aligot",
        "batata-harra",
        "boxty",
        "colcannon",
        "confit-potatoes",
        "dauphine-potatoes",
        "gatto-di-patate",
        "greek-lemon-potatoes",
        "hasselback-potatoes",
        "latkes-with-applesauce",
        "papas-arrugadas",
        "patatas-a-la-importancia",
        "pommes-anna",
        "potato-gnocchi",
        "potato-knishes",
        "potatoes-romanoff",
        "rosti",
        "tortilla-espanola",
    }

    for recipe in manifest["recipes"]:
        assert set(recipe["variants"]) == set(NOTATIONS)
        assert recipe["ingredients"]
        assert recipe["operations"]
        assert (output / recipe["yaml"]).is_file()
        for notation, variant in recipe["variants"].items():
            svg = (output / variant["url"]).read_text(encoding="utf-8")
            assert f'data-recipeflow-notation="{notation}"' in svg
            assert recipe["title"] in html.unescape(svg)
            assert variant["width"] > 0
            assert variant["height"] > 0

    assert (output / "index.html").read_bytes() == (output / "404.html").read_bytes()
    assert (output / ".nojekyll").is_file()
    index = (output / "index.html").read_text(encoding="utf-8")
    javascript = (output / "app.js").read_text(encoding="utf-8")
    assert 'id="recipe-search"' in index
    assert "state.manifest.recipe_count" in javascript
