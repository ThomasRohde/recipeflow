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
    expected_slugs = {
        path.name.removesuffix(".recipe.yaml")
        for path in (Path(__file__).parents[1] / "site" / "recipes").glob("*.recipe.yaml")
    }
    published_slugs = {item["slug"] for item in manifest["recipes"]}
    published_image_slugs = {
        Path(item["image"]["url"]).stem for item in manifest["recipes"]
    }
    assert manifest["recipe_count"] == len(expected_slugs)
    assert published_slugs == expected_slugs
    assert published_image_slugs == expected_slugs
    assert manifest["recipes"][0]["slug"] == min(expected_slugs)
    assert len({item["title"] for item in manifest["recipes"]}) == len(expected_slugs)

    source_ledger = (Path(__file__).parents[1] / "site" / "SOURCES.md").read_text(
        encoding="utf-8"
    )

    for recipe in manifest["recipes"]:
        assert set(recipe["variants"]) == set(NOTATIONS)
        assert recipe["ingredients"]
        assert recipe["operations"]
        assert recipe["source"]["url"] in source_ledger
        assert recipe["text"].startswith(f"{recipe['title']}\n")
        assert "Ingredients\n-----------" in recipe["text"]
        assert "Method\n------" in recipe["text"]
        assert recipe["image"]["alt"] == (
            f"Illustrative generated image of the finished {recipe['title']} dish."
        )
        assert "AI-generated" in recipe["image"]["caption"]
        image = output / recipe["image"]["url"]
        assert image.is_file()
        assert image.read_bytes()[:4] == b"RIFF"
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
    assert 'id="recipe-image"' in index
    assert 'id="recipe-text"' in index
    assert "recipe.image.url" in javascript
    assert "recipe.image.alt" in javascript
    assert "recipe.text" in javascript
    assert 'localStorage.getItem("potato-index-notation") || "ledger"' in javascript
    assert "state.manifest.recipe_count" in javascript
