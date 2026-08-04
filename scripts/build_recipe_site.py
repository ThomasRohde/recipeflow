from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import yaml

from recipeflow import RenderOptions, build, render, render_check
from recipeflow.models import RecipeDocument, Severity
from recipeflow.models.document import MaterialUse, duration_text, quantity_text, temperature_text

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "site"
DEFAULT_OUTPUT = ROOT / "site-dist"
NOTATIONS = {
    "flow": {
        "label": "Flow",
        "width": 1400.0,
        "blurb": "Flow follows ingredients across time.",
    },
    "compact-table": {
        "label": "Compact Table",
        "width": 1200.0,
        "blurb": "Compact Table compresses the route into a nested ingredient grid.",
    },
    "ledger": {
        "label": "Kitchen Ledger",
        "width": 1000.0,
        "blurb": (
            "Kitchen Ledger audits every entry: what came in, what happened, and what came out."
        ),
    },
}

# Texture is presented as the three categorical choices a shopper can act on;
# the fixed display positions do not pretend that the source supplied a score.
TEXTURE_BANDS = (
    {
        "code": "A",
        "key": "firm",
        "label": "Holds together",
        "position": 18,
        "bag": "firm · waxy · salad · boiling · kogefast",
        "note": (
            "This lot has to survive handling. A firm, waxy potato keeps its edges through "
            "the pan, the toss, and the serving spoon — a floury one will turn the dish into "
            "an accidental purée."
        ),
    },
    {
        "code": "B",
        "key": "balanced",
        "label": "Balanced",
        "position": 50,
        "bag": "all-purpose · yellow · type B · slightly floury",
        "note": (
            "Squarely in the all-purpose middle: creamy enough to give, firm enough to hold. "
            "This is the zone most recipes mean when they name a variety and assume you can "
            "find it."
        ),
    },
    {
        "code": "C",
        "key": "floury",
        "label": "Falls apart",
        "position": 82,
        "bag": "floury · mealy · starchy · baking · melet",
        "note": (
            "Buy the dry, mealy, high-starch sack. This recipe wants the potato to collapse, "
            "absorb, or crisp — and a waxy one will refuse all three politely."
        ),
    },
)


def _band_for(code: str) -> dict[str, Any]:
    normalized = code.strip().upper()
    for band in TEXTURE_BANDS:
        if band["code"] == normalized:
            return band
    raise RuntimeError(f"texture band must be A, B, or C, not {code!r}")


def _sentence(text: str) -> str:
    """Present a stored action phrase as a sentence without rewriting it."""
    cleaned = text.strip()
    if not cleaned:
        return cleaned
    cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned if cleaned[-1] in ".!?" else f"{cleaned}."


def _steps(document: RecipeDocument) -> list[dict[str, str]]:
    """The method in words: standing conditions first, then the operations.

    Each step keeps the source's own action phrasing. Where a setup entry names a
    target or a temperature, those are appended rather than folded into the verb
    phrase, so nothing is invented to make the grammar flow.
    """
    steps: list[dict[str, str]] = []
    for item in document.setup:
        qualifiers = [
            value
            for value in (
                item.target,
                temperature_text(item.temperature),
                duration_text(item.duration),
            )
            if value
        ]
        detail = f"{item.action} — {', '.join(qualifiers)}" if qualifiers else item.action
        steps.append({"kind": "setup", "text": _sentence(detail)})
    for operation in document.operations:
        qualifiers = [
            value
            for value in (
                f"Temperature {temperature_text(operation.temperature)}"
                if operation.temperature
                else None,
                f"Time {duration_text(operation.duration)}" if operation.duration else None,
                f"Until {operation.until}" if operation.until else None,
                (
                    f"Completion: {operation.completion_criteria}"
                    if operation.completion_criteria
                    else None
                ),
            )
            if value
        ]
        if operation.repeat:
            repeat_parts = []
            if operation.repeat.count is not None:
                repeat_parts.append(f"{operation.repeat.count} times")
            if operation.repeat.interval is not None:
                repeat_parts.append(f"every {duration_text(operation.repeat.interval)}")
            if operation.repeat.until:
                repeat_parts.append(f"until {operation.repeat.until}")
            if repeat_parts:
                qualifiers.append(f"Repeat {', '.join(repeat_parts)}")
        if operation.optional:
            qualifiers.append("Optional")
        action = operation.label or operation.action
        detail = f"{action} — {'; '.join(qualifiers)}" if qualifiers else action
        steps.append({"kind": "operation", "text": _sentence(detail)})
    return steps


def _load_curation(source_dir: Path) -> dict[str, dict[str, Any]]:
    path = source_dir / "curation.yaml"
    if not path.is_file():
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise RuntimeError(f"{path} must be a mapping of recipe slug to curation fields")
    return loaded


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
    image_url: str,
    curation: dict[str, Any],
) -> dict[str, Any]:
    metadata = document.recipe
    labels = _material_label_map(document)
    source = metadata.source
    texture_band = curation.get("texture_band")
    if texture_band is not None and not isinstance(texture_band, str):
        raise RuntimeError(f"{metadata.id} texture_band must be A, B, or C")
    return {
        "slug": metadata.id,
        "title": metadata.title,
        "description": metadata.description,
        "yield": metadata.yield_text,
        "tags": list(metadata.tags),
        # Editorial curation, absent for most lots. See site/curation.yaml.
        "band": _band_for(texture_band) if texture_band is not None else None,
        "variety": curation.get("variety"),
        "origin": curation.get("origin"),
        "steps": _steps(document),
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
        "image": {
            "url": image_url,
            "alt": f"Illustrative generated image of the finished {metadata.title} dish.",
            "caption": "AI-generated finished-dish portrait · RecipeFlow Food Portrait template",
        },
        "text": text_render,
        "variants": variants,
        "yaml": f"recipes/{metadata.id}.recipe.yaml",
    }


def build_site(source_dir: Path = DEFAULT_SOURCE, output_dir: Path = DEFAULT_OUTPUT) -> None:
    static_dir = source_dir / "static"
    recipes_dir = source_dir / "recipes"
    curation = _load_curation(source_dir)
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
        image_url = f"images/recipes/{slug}.webp"
        image_path = static_dir / image_url
        if not image_path.is_file():
            raise RuntimeError(f"{recipe_path} has no finished-dish image at {image_path}")
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
            _recipe_data(
                result.document,
                variants,
                text_artifact.content,
                image_url,
                curation.get(slug) or {},
            )
        )

    unknown = sorted(set(curation) - {item["slug"] for item in recipes})
    if unknown:
        raise RuntimeError(f"curation.yaml names recipes that do not exist: {', '.join(unknown)}")

    manifest = {
        "title": "Potato Index",
        "recipe_count": len(recipes),
        "notations": [
            {"id": notation, "label": config["label"], "blurb": config["blurb"]}
            for notation, config in NOTATIONS.items()
        ],
        "bands": [dict(band) for band in TEXTURE_BANDS],
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
