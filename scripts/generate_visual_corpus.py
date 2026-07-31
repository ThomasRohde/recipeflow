"""Generate the committed RecipeFlow visual-regression corpus.

The recipe documents and manifest are authored inputs. Every layout, SVG, HTML, and PNG
artifact is derived deterministically from the same resolved ``TabularLayout`` instance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from recipeflow.api import compile_document, parse_yaml
from recipeflow.layout import create_tabular_layout, validate_tabular_layout
from recipeflow.renderers import (
    RenderOptions,
    render_tabular_html,
    render_tabular_png,
    render_tabular_svg,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_ROOT = PROJECT_ROOT / "examples" / "golden"
MANIFEST_PATH = GOLDEN_ROOT / "manifest.json"

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
    ".tabular-layout.json",
    ".tabular.svg",
    ".tabular.html",
    ".tabular.png",
)


def _manifest_slugs() -> tuple[str, ...]:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    slugs = tuple(entry["slug"] for entry in payload["fixtures"])
    if slugs != REQUIRED_SLUGS:
        raise RuntimeError(
            "The visual-corpus manifest must list the required fixtures in contract order: "
            f"{REQUIRED_SLUGS!r}; received {slugs!r}."
        )
    return slugs


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _generate(slug: str) -> dict[str, bytes]:
    source_path = GOLDEN_ROOT / f"{slug}.recipe.yaml"
    parsed = parse_yaml(source_path.read_text(encoding="utf-8"))
    if parsed.document is None:
        details = "; ".join(
            f"{item.code} {item.path}: {item.message}" for item in parsed.diagnostics
        )
        raise RuntimeError(f"{slug}: parse failed: {details}")

    compiled = compile_document(parsed.document, strict=True)
    if compiled.graph is None:
        details = "; ".join(
            f"{item.code} {item.path}: {item.message}" for item in compiled.diagnostics
        )
        raise RuntimeError(f"{slug}: strict compilation failed: {details}")
    if compiled.diagnostics:
        details = "; ".join(
            f"{item.code} {item.path}: {item.message}" for item in compiled.diagnostics
        )
        raise RuntimeError(f"{slug}: corpus recipes must compile without diagnostics: {details}")

    options = RenderOptions(theme="classic", scale=2.0, dpi=144)
    layout = create_tabular_layout(compiled.graph, options.to_layout_options())
    diagnostics = validate_tabular_layout(layout)
    if diagnostics or layout.diagnostics:
        details = "; ".join(
            f"{item.code} {item.path}: {item.message}"
            for item in (*layout.diagnostics, *diagnostics)
        )
        raise RuntimeError(f"{slug}: invalid tabular layout: {details}")

    layout_json = layout.model_dump_json(indent=2, by_alias=True) + "\n"
    return {
        ".tabular-layout.json": layout_json.encode("utf-8"),
        ".tabular.svg": render_tabular_svg(layout, options).encode("utf-8"),
        ".tabular.html": render_tabular_html(layout, options).encode("utf-8"),
        ".tabular.png": render_tabular_png(layout, options),
    }


def generate(*, check: bool, selected_slugs: tuple[str, ...] | None = None) -> int:
    slugs = _manifest_slugs()
    selected = selected_slugs or slugs
    unknown = sorted(set(selected) - set(slugs))
    if unknown:
        raise RuntimeError(f"Unknown visual-corpus fixtures: {', '.join(unknown)}")

    stale: list[Path] = []
    written: list[Path] = []
    generated: dict[str, dict[str, bytes]] = {}
    for slug in selected:
        outputs = _generate(slug)
        generated[slug] = outputs
        for suffix in ARTIFACT_SUFFIXES:
            path = GOLDEN_ROOT / f"{slug}{suffix}"
            content = outputs[suffix]
            if path.exists() and path.read_bytes() == content:
                continue
            if check:
                stale.append(path)
            else:
                path.write_bytes(content)
                written.append(path)

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entries = {entry["slug"]: entry for entry in manifest["fixtures"]}
    for slug, outputs in generated.items():
        entries[slug]["artifact_sha256"] = {
            "recipe.yaml": _sha256(
                (GOLDEN_ROOT / f"{slug}.recipe.yaml").read_bytes()
            ),
            **{
                suffix.removeprefix("."): _sha256(content)
                for suffix, content in outputs.items()
            },
        }
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    if MANIFEST_PATH.read_bytes() != manifest_bytes:
        if check:
            stale.append(MANIFEST_PATH)
        else:
            MANIFEST_PATH.write_bytes(manifest_bytes)
            written.append(MANIFEST_PATH)

    if stale:
        for path in stale:
            print(f"stale or missing: {path.relative_to(PROJECT_ROOT)}")
        return 1
    if check:
        print(f"visual corpus is current ({len(selected)} fixtures)")
    else:
        print(
            f"visual corpus generated ({len(selected)} fixtures, "
            f"{len(written)} files updated)"
        )
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail instead of writing when committed artifacts differ.",
    )
    parser.add_argument(
        "--fixture",
        action="append",
        dest="fixtures",
        help="Generate or check one fixture; may be repeated.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    selected = tuple(args.fixtures) if args.fixtures else None
    return generate(check=args.check, selected_slugs=selected)


if __name__ == "__main__":
    raise SystemExit(main())
