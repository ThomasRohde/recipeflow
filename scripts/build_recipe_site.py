from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from recipeflow import RenderOptions, build, render, render_check
from recipeflow.models import RecipeDocument, Severity
from recipeflow.models.document import MaterialUse, duration_text, quantity_text, temperature_text

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "site"
DEFAULT_OUTPUT = ROOT / "site-dist"
NOTATIONS = {
    "flow": {"label": "Flow", "width": 1400.0},
    "compact-table": {"label": "Compact Table", "width": 1200.0},
    "ledger": {"label": "Kitchen Ledger", "width": 1000.0},
}


def _fail_on_errors(diagnostics: tuple[Any, ...], context: str) -> None:
    errors = [item for item in diagnostics if item.severity == Severity.ERROR]
    if errors:
        details = "\n".join(f"{item.code} {item.path}: {item.message}" for item in errors)
        raise RuntimeError(f"{context} failed:\n{details}")


def _material_label_map(document: RecipeDocument) -> dict[str, str]:
    labels = {material_id: item.label for material_id, item in document.ingredients.items()}
    for operation in document.operations:
        labels.update({material_id: item.label for material_id, item in operation.outputs.items()})
    return labels


def _input_data(value: str | MaterialUse, labels: dict[str, str]) -> dict[str, Any]:
    if isinstance(value, str):
        return {"label": labels.get(value, value), "quantity": None, "optional": False}
    return {
        "label": labels.get(value.material, value.material),
        "quantity": quantity_text(value.quantity),
        "optional": value.optional,
    }


def _recipe_data(
    document: RecipeDocument,
    variants: dict[str, dict[str, Any]],
    text_render: str,
) -> dict[str, Any]:
    metadata = document.recipe
    labels = _material_label_map(document)
    source = metadata.source
    return {
        "slug": metadata.id,
        "title": metadata.title,
        "description": metadata.description,
        "yield": metadata.yield_text,
        "tags": list(metadata.tags),
        "notes": list(metadata.notes),
        "source": {
            "title": source.title if source else None,
            "author": source.author if source else None,
            "url": source.url if source else None,
        },
        "ingredients": [
            {
                "label": item.label,
                "quantity": quantity_text(item.quantity),
                "optional": item.optional,
                "annotations": list(item.annotations),
            }
            for item in document.ingredients.values()
        ],
        "setup": [
            {
                "action": item.action,
                "target": item.target,
                "temperature": temperature_text(item.temperature),
                "duration": duration_text(item.duration),
            }
            for item in document.setup
        ],
        "operations": [
            {
                "action": item.label or item.action,
                "inputs": [_input_data(value, labels) for value in item.inputs],
                "outputs": [output.label for output in item.outputs.values()],
                "duration": duration_text(item.duration),
                "temperature": temperature_text(item.temperature),
                "until": item.until or item.completion_criteria,
                "optional": item.optional,
            }
            for item in document.operations
        ],
        "text": text_render,
        "variants": variants,
        "yaml": f"recipes/{metadata.id}.recipe.yaml",
    }


def build_site(source_dir: Path = DEFAULT_SOURCE, output_dir: Path = DEFAULT_OUTPUT) -> None:
    static_dir = source_dir / "static"
    recipes_dir = source_dir / "recipes"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(static_dir, output_dir)
    (output_dir / "visuals").mkdir()
    (output_dir / "recipes").mkdir()

    recipes: list[dict[str, Any]] = []
    for recipe_path in sorted(recipes_dir.glob("*.recipe.yaml")):
        source = recipe_path.read_text(encoding="utf-8")
        result = build(source, strict=True)
        _fail_on_errors(result.diagnostics, str(recipe_path))
        if result.document is None or result.graph is None:
            raise RuntimeError(f"{recipe_path} did not produce a document and graph")

        slug = result.document.recipe.id
        if not slug:
            raise RuntimeError(f"{recipe_path} has no recipe id")
        variants: dict[str, dict[str, Any]] = {}
        for notation, config in NOTATIONS.items():
            options = RenderOptions(
                notation=notation,
                theme="modern",
                width=config["width"],
                outer_margin=32,
                base_font_size=15,
                minimum_font_size=11,
            )
            check = render_check(result.graph, options)
            _fail_on_errors(check.diagnostics, f"{recipe_path} ({notation}) layout")
            artifact = render(result.graph, "tabular-svg", options)
            destination = output_dir / "visuals" / f"{slug}.{notation}.svg"
            if not isinstance(artifact.content, str):
                raise RuntimeError(f"Expected SVG text for {recipe_path} ({notation})")
            destination.write_text(artifact.content, encoding="utf-8", newline="\n")
            variants[notation] = {
                "label": config["label"],
                "url": f"visuals/{slug}.{notation}.svg",
                "width": artifact.width,
                "height": artifact.height,
            }

        shutil.copy2(recipe_path, output_dir / "recipes" / f"{slug}.recipe.yaml")
        text_artifact = render(result.graph, "text")
        if not isinstance(text_artifact.content, str):
            raise RuntimeError(f"Expected text output for {recipe_path}")
        recipes.append(
            _recipe_data(result.document, variants, text_artifact.content)
        )

    manifest = {
        "title": "Potato Index",
        "recipe_count": len(recipes),
        "notations": [
            {"id": notation, "label": config["label"]}
            for notation, config in NOTATIONS.items()
        ],
        "recipes": recipes,
    }
    (output_dir / "recipes.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")
    shutil.copy2(output_dir / "index.html", output_dir / "404.html")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the RecipeFlow potato recipe site")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build_site(args.source.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
