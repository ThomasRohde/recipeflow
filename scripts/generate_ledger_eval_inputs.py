"""Generate deterministic 300-DPI color, greyscale, and 1-bit ledger PNGs."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

from recipeflow.api import compile_document, parse_yaml
from recipeflow.layout import create_tabular_layout, validate_tabular_layout
from recipeflow.models.layout import TabularLayout
from recipeflow.renderers import RenderOptions, render_tabular_png

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEDGER_ROOT = PROJECT_ROOT / "examples" / "golden" / "ledger"
SLUGS = (
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
VARIANTS = ("color", "greyscale", "1bit")
PRINT_SCALE = 300 / 96


def _variant_png(source: bytes, variant: str) -> bytes:
    if variant == "color":
        return source
    with Image.open(BytesIO(source)) as image:
        image.load()
        grayscale = ImageOps.grayscale(image)
        if variant == "greyscale":
            output_image = grayscale
        else:
            output_image = grayscale.point(
                lambda value: 255 if value >= 224 else 0,
                mode="1",
            )
        output = BytesIO()
        output_image.save(
            output,
            format="PNG",
            dpi=(300, 300),
            compress_level=9,
        )
        return output.getvalue()


def generate(
    output_root: Path,
    *,
    check: bool,
    selected_slugs: tuple[str, ...] | None = None,
    source_overrides: Mapping[str, Path] | None = None,
) -> int:
    slugs = selected_slugs or SLUGS
    unknown = sorted(set(slugs) - set(SLUGS))
    if unknown:
        raise ValueError(f"Unknown ledger fixtures: {', '.join(unknown)}")
    if not check:
        output_root.mkdir(parents=True, exist_ok=True)
    options = RenderOptions(
        notation="ledger",
        theme="classic",
        scale=PRINT_SCALE,
        dpi=300,
        page_size="A4",
        orientation="portrait",
        print_mode=True,
        outer_margin=40,
    )
    stale: list[Path] = []
    written = 0
    for slug in slugs:
        override = (source_overrides or {}).get(slug)
        if override is None:
            layout = TabularLayout.model_validate_json(
                (LEDGER_ROOT / f"{slug}.tabular-layout.json").read_text(
                    encoding="utf-8"
                )
            )
        else:
            parsed = parse_yaml(override.read_text(encoding="utf-8"))
            if parsed.document is None:
                raise ValueError(f"{slug}: override recipe does not parse: {override}")
            compiled = compile_document(parsed.document, strict=True)
            if compiled.graph is None or compiled.diagnostics:
                details = "; ".join(
                    f"{item.code} {item.path}: {item.message}"
                    for item in compiled.diagnostics
                )
                raise ValueError(f"{slug}: override recipe does not compile: {details}")
            layout = create_tabular_layout(
                compiled.graph,
                options.to_layout_options(),
            )
            diagnostics = (*layout.diagnostics, *validate_tabular_layout(layout))
            if diagnostics:
                details = "; ".join(
                    f"{item.code} {item.path}: {item.message}" for item in diagnostics
                )
                raise ValueError(f"{slug}: override layout is invalid: {details}")
        color = render_tabular_png(layout, options)
        for variant in VARIANTS:
            path = output_root / f"{slug}--{variant}.tabular.png"
            content = _variant_png(color, variant)
            if path.is_file() and path.read_bytes() == content:
                continue
            if check:
                stale.append(path)
            else:
                path.write_bytes(content)
                written += 1
    if stale:
        for path in stale:
            print(f"stale or missing: {path}")
        return 1
    if check:
        print(f"ledger evaluation inputs are current ({len(slugs) * 3} PNGs)")
    else:
        print(f"ledger evaluation inputs generated ({written} PNGs updated)")
    return 0


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assignments(prefix: str, candidates: tuple[str, ...]) -> dict[str, list[str]]:
    return {
        f"{prefix}-{index:02d}": list(candidates[offset : offset + 3])
        for index, offset in enumerate(range(0, len(candidates), 3), start=1)
    }


def _judge_assignments(prefix: str, candidates: tuple[str, ...]) -> dict[str, list[str]]:
    return {
        f"{prefix}-{index:02d}": list(candidates[offset : offset + 6])
        for index, offset in enumerate(range(0, len(candidates), 6), start=1)
    }


def initialize_run(
    run_root: Path,
    source_overrides: Mapping[str, Path] | None = None,
) -> None:
    run_path = run_root / "run.json"
    if run_path.exists():
        raise FileExistsError(f"refusing to replace immutable run manifest: {run_path}")
    candidates = tuple(f"{slug}--{variant}" for variant in VARIANTS for slug in SLUGS)
    run_id = run_root.name
    reconstruction_assignments = _assignments(
        f"{run_id}-reader",
        candidates,
    )
    judge_assignments = {
        **_judge_assignments(f"{run_id}-judge-a", candidates),
        **_judge_assignments(f"{run_id}-judge-b", candidates),
    }
    input_root = run_root / "inputs"
    manifest = {
        "schema_version": "recipeflow.png-blackbox-run/v1",
        "run_id": run_id,
        "created_on": run_id[:10],
        "input_contract": "png-only",
        "evaluation_profile": "ledger-human-v1",
        "reconstruction_format": "markdown",
        "input_png_root": input_root.relative_to(PROJECT_ROOT).as_posix(),
        "original_root": "examples/golden",
        "original_file_overrides": {
            slug: path.resolve().relative_to(PROJECT_ROOT).as_posix()
            for slug, path in (source_overrides or {}).items()
        },
        "reconstruction_prompt": "evals/png-blackbox/reconstruction-prompt.md",
        "judge_rubric": "evals/png-blackbox/judge-rubric.md",
        "judge_count_per_fixture": 2,
        "equivalence_threshold": 28,
        "core_score_minimum": 3,
        "input_png_sha256": {
            candidate: _sha256(input_root / f"{candidate}.tabular.png")
            for candidate in candidates
        },
        "reconstruction_assignments": reconstruction_assignments,
        "judge_assignments": judge_assignments,
    }
    run_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--fixture", action="append", dest="fixtures")
    parser.add_argument(
        "--source-override",
        action="append",
        default=[],
        metavar="SLUG=PATH",
        help="Render one assigned slug from a different RecipeFlow YAML source.",
    )
    parser.add_argument(
        "--initialize-run",
        action="store_true",
        help="Treat output_root as a run directory, generate inputs/, and create run.json.",
    )
    return parser


def _source_overrides(values: list[str]) -> dict[str, Path]:
    overrides: dict[str, Path] = {}
    for value in values:
        slug, separator, raw_path = value.partition("=")
        if not separator or slug not in SLUGS or not raw_path:
            raise ValueError(f"invalid --source-override: {value}")
        path = (PROJECT_ROOT / raw_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        overrides[slug] = path
    return overrides


def main() -> int:
    args = _parser().parse_args()
    selected = tuple(args.fixtures) if args.fixtures else None
    source_overrides = _source_overrides(args.source_override)
    run_root = args.output_root.resolve()
    output_root = run_root / "inputs" if args.initialize_run else run_root
    result = generate(
        output_root,
        check=args.check,
        selected_slugs=selected,
        source_overrides=source_overrides,
    )
    if result == 0 and args.initialize_run and not args.check:
        initialize_run(run_root, source_overrides)
        print(f"ledger evaluation run initialized ({run_root.name})")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
