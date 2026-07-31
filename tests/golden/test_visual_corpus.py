from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from recipeflow.api import compile_document, parse_yaml
from recipeflow.layout import create_tabular_layout
from recipeflow.renderers import (
    RenderOptions,
    render_tabular_html,
    render_tabular_png,
    render_tabular_svg,
)

pytestmark = pytest.mark.golden

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_ROOT = PROJECT_ROOT / "examples" / "golden"
REQUIRED_SLUGS = (
    "espresso-brownies",
    "long-text",
    "measurement-systems",
    "branch-and-join",
    "split-and-reserve",
    "multiple-outputs",
    "setup-heavy",
    "many-narrow-operations",
    "long-completion-criteria",
    "unicode",
    "compact",
    "large",
)
ARTIFACT_SUFFIXES = (
    ".recipe.yaml",
    ".tabular-layout.json",
    ".tabular.svg",
    ".tabular.html",
    ".tabular.png",
)


def _compiled_graph(slug: str):
    parsed = parse_yaml(
        (GOLDEN_ROOT / f"{slug}.recipe.yaml").read_text(encoding="utf-8")
    )
    assert parsed.document is not None, parsed.diagnostics
    compiled = compile_document(parsed.document, strict=True)
    assert compiled.graph is not None, compiled.diagnostics
    assert compiled.diagnostics == ()
    return compiled.graph


def _document_and_graph(slug: str):
    parsed = parse_yaml(
        (GOLDEN_ROOT / f"{slug}.recipe.yaml").read_text(encoding="utf-8")
    )
    assert parsed.document is not None, parsed.diagnostics
    compiled = compile_document(parsed.document, strict=True)
    assert compiled.graph is not None, compiled.diagnostics
    assert compiled.diagnostics == ()
    return parsed.document, compiled.graph


def test_manifest_and_directory_contain_exactly_the_required_corpus() -> None:
    manifest = json.loads((GOLDEN_ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["schema_version"] == "recipeflow.visual-corpus/v1"
    assert manifest["theme"] == "classic"
    assert manifest["png"] == {
        "engine": "resvg-py",
        "scale": 2.0,
        "dpi": 144,
        "background": None,
    }
    assert tuple(item["slug"] for item in manifest["fixtures"]) == REQUIRED_SLUGS
    assert len({item["stress"] for item in manifest["fixtures"]}) == len(REQUIRED_SLUGS)

    for fixture in manifest["fixtures"]:
        slug = fixture["slug"]
        assert fixture["artifact_sha256"] == {
            suffix.removeprefix("."): hashlib.sha256(
                (GOLDEN_ROOT / f"{slug}{suffix}").read_bytes()
            ).hexdigest()
            for suffix in ARTIFACT_SUFFIXES
        }

    for suffix in ARTIFACT_SUFFIXES:
        discovered = {
            path.name.removesuffix(suffix)
            for path in GOLDEN_ROOT.glob(f"*{suffix}")
        }
        assert discovered == set(REQUIRED_SLUGS)


@pytest.mark.parametrize("slug", REQUIRED_SLUGS)
def test_recipe_compiles_strictly_and_artifacts_match_one_resolved_layout(
    slug: str,
) -> None:
    graph = _compiled_graph(slug)
    options = RenderOptions(theme="classic", scale=2.0, dpi=144)
    layout = create_tabular_layout(graph, options.to_layout_options())

    expected_layout = layout.model_dump_json(indent=2, by_alias=True) + "\n"
    expected_svg = render_tabular_svg(layout, options)
    expected_html = render_tabular_html(layout, options)
    expected_png = render_tabular_png(layout, options)

    assert layout.theme == "classic"
    assert not layout.diagnostics
    assert (GOLDEN_ROOT / f"{slug}.tabular-layout.json").read_text(
        encoding="utf-8"
    ) == expected_layout
    assert (GOLDEN_ROOT / f"{slug}.tabular.svg").read_text(
        encoding="utf-8"
    ) == expected_svg
    assert (GOLDEN_ROOT / f"{slug}.tabular.html").read_text(
        encoding="utf-8"
    ) == expected_html
    assert (GOLDEN_ROOT / f"{slug}.tabular.png").read_bytes() == expected_png


@pytest.mark.parametrize("slug", REQUIRED_SLUGS)
def test_textual_artifact_rendering_is_byte_deterministic(slug: str) -> None:
    graph = _compiled_graph(slug)
    options = RenderOptions(theme="classic", scale=2.0, dpi=144)
    first = create_tabular_layout(graph, options.to_layout_options())
    second = create_tabular_layout(graph, options.to_layout_options())

    assert first.model_dump_json(by_alias=True) == second.model_dump_json(by_alias=True)
    assert render_tabular_svg(first, options) == render_tabular_svg(second, options)
    assert render_tabular_html(first, options) == render_tabular_html(second, options)


@pytest.mark.parametrize("slug", REQUIRED_SLUGS)
def test_authored_source_and_preparation_text_is_preserved_in_layout(
    slug: str,
) -> None:
    document, graph = _document_and_graph(slug)
    layout = create_tabular_layout(graph)
    by_role: dict[str, set[str]] = {}
    for block in layout.text_blocks:
        by_role.setdefault(block.role, set()).add(block.source_text)

    for ingredient in document.ingredients.values():
        if ingredient.source_text:
            assert ingredient.source_text in by_role["ingredient-source"]
        if ingredient.preparation_state:
            assert (
                ingredient.preparation_state
                in by_role["ingredient-preparation"]
            )
        if ingredient.temperature_state:
            assert ingredient.temperature_state in by_role["ingredient-preparation"]
        for annotation in ingredient.annotations:
            assert annotation in by_role["ingredient-annotation"]

    for setup in document.setup:
        for note in setup.notes:
            assert note in by_role["setup-note"]
