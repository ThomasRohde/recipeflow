"""Validate the RecipeFlow author skill structure and executable examples."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "recipeflow-author"
REQUIRED = (
    "SKILL.md",
    "agents/openai.yaml",
    "assets/recipe.flow.template.yaml",
    "references/modeling-rules.md",
    "references/visual-review.md",
    "references/critic-rubric.md",
)


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.update(PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    return subprocess.run(
        [sys.executable, "-m", "recipeflow.cli.main", *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        encoding="utf-8",
        env=environment,
    )


def check_structure() -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (SKILL / relative).is_file():
            errors.append(f"missing skill resource: {relative}")

    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    if not skill_text.startswith("---\n"):
        errors.append("SKILL.md must begin with YAML frontmatter")
    else:
        _, frontmatter, _ = skill_text.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        if set(metadata or {}) != {"name", "description"}:
            errors.append("SKILL.md frontmatter must contain only name and description")
        elif metadata["name"] != "recipeflow-author":
            errors.append("SKILL.md name must be recipeflow-author")

    examples = sorted((SKILL / "examples").glob("*.recipe.yaml"))
    if len(examples) < 3:
        errors.append("skill must include at least three complete RecipeFlow examples")
    for example in examples:
        try:
            data = load_yaml(example)
        except yaml.YAMLError as exc:
            errors.append(f"{example.name}: invalid YAML: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{example.name}: expected a mapping")
            continue
        for key in ("recipe", "ingredients", "operations"):
            if key not in data:
                errors.append(f"{example.name}: missing {key}")

    openai = load_yaml(SKILL / "agents" / "openai.yaml")
    default_prompt = (openai or {}).get("interface", {}).get("default_prompt", "")
    if "$recipeflow-author" not in default_prompt:
        errors.append("agents/openai.yaml default_prompt must mention $recipeflow-author")
    return errors


def check_examples(*, render: bool) -> list[str]:
    errors: list[str] = []
    examples = sorted((SKILL / "examples").glob("*.recipe.yaml"))
    with tempfile.TemporaryDirectory(prefix="recipeflow-skill-") as temporary:
        output_dir = Path(temporary)
        for example in examples:
            validate = run_cli("validate", str(example), "--json")
            if validate.returncode != 0:
                errors.append(
                    f"{example.name}: validate failed: {validate.stdout}{validate.stderr}"
                )
                continue
            try:
                envelope = json.loads(validate.stdout)
            except json.JSONDecodeError as exc:
                errors.append(f"{example.name}: validate --json is not JSON: {exc}")
                continue
            if not envelope.get("ok", envelope.get("valid", False)):
                errors.append(f"{example.name}: validate envelope is not successful")

            if not render:
                continue

            graph = output_dir / f"{example.stem}.graph.json"
            svg = output_dir / f"{example.stem}.tabular.svg"
            png = output_dir / f"{example.stem}.tabular.png"
            commands = (
                ("compile", str(example), "--output", str(graph)),
                ("inspect", str(example), "--json"),
                ("render", str(example), "--format", "text"),
                (
                    "render",
                    str(example),
                    "--format",
                    "tabular-svg",
                    "--theme",
                    "classic",
                    "--output",
                    str(svg),
                ),
                (
                    "render",
                    str(example),
                    "--format",
                    "tabular-png",
                    "--theme",
                    "classic",
                    "--output",
                    str(png),
                ),
                ("render-check", str(example), "--json"),
            )
            for command in commands:
                completed = run_cli(*command)
                if completed.returncode != 0:
                    errors.append(
                        f"{example.name}: {' '.join(command)} failed: "
                        f"{completed.stdout}{completed.stderr}"
                    )
                    break
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--structure-only",
        action="store_true",
        help="Check skill metadata and YAML examples without invoking unfinished CLI hooks.",
    )
    parser.add_argument(
        "--semantic-only",
        action="store_true",
        help="Also validate examples, but skip render hooks that may be under development.",
    )
    arguments = parser.parse_args()

    errors = check_structure()
    if not arguments.structure_only and not errors:
        errors.extend(check_examples(render=not arguments.semantic_only))
    if errors:
        print("\n".join(errors))
        return 1

    if arguments.structure_only:
        mode = "structure"
    elif arguments.semantic_only:
        mode = "structure and semantic examples"
    else:
        mode = "structure and full examples"
    print(f"RecipeFlow author skill check passed: {mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
