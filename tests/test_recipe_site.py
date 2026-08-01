from __future__ import annotations

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
    assert manifest["recipe_count"] == 6
    assert manifest["recipes"][0]["slug"] == "greek-lemon-potatoes"
    assert {item["slug"] for item in manifest["recipes"]} == {
        "greek-lemon-potatoes",
        "hasselback-potatoes",
        "pommes-anna",
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
            assert recipe["title"] in svg
            assert variant["width"] > 0
            assert variant["height"] > 0

    assert (output / "index.html").read_bytes() == (output / "404.html").read_bytes()
    assert (output / ".nojekyll").is_file()
