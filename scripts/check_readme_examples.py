"""Execute the README's document, Python, and CLI examples."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from recipeflow import build

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def fenced_block(text: str, heading: str, language: str) -> str:
    section = text.split(f"## {heading}", 1)[1].split("\n## ", 1)[0]
    match = re.search(rf"```{re.escape(language)}\n(.*?)```", section, re.DOTALL)
    if match is None:
        raise ValueError(f"README section {heading!r} has no {language!r} block")
    return match.group(1)


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "recipeflow.cli.main", *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--library-only",
        action="store_true",
        help="Skip CLI/render hooks that may be under active development.",
    )
    arguments = parser.parse_args()
    text = README.read_text(encoding="utf-8")

    document = fenced_block(text, "First document", "yaml")
    built = build(document)
    if not built.ok:
        print(f"README document failed: {built.diagnostics}")
        return 1

    python_example = fenced_block(text, "Python library", "python")
    exec(compile(python_example, "README.md:Python library", "exec"), {})

    if arguments.library_only:
        print("README library examples passed")
        return 0

    fixture = ROOT / "examples" / "espresso-brownies.recipe.yaml"
    with tempfile.TemporaryDirectory(prefix="recipeflow-readme-") as temporary:
        output = Path(temporary)
        commands = (
            ("validate", str(fixture), "--json"),
            ("compile", str(fixture), "--output", str(output / "brownies.graph.json")),
            (
                "render",
                str(fixture),
                "--format",
                "tabular-svg",
                "--output",
                str(output / "brownies.svg"),
            ),
            (
                "render",
                str(fixture),
                "--format",
                "tabular-html",
                "--output",
                str(output / "brownies.html"),
            ),
            (
                "render",
                str(fixture),
                "--format",
                "tabular-png",
                "--output",
                str(output / "brownies.png"),
            ),
            ("render-check", str(fixture), "--json"),
        )
        for command in commands:
            completed = run_cli(*command)
            if completed.returncode != 0:
                print(
                    f"README CLI example failed: {' '.join(command)}\n"
                    f"{completed.stdout}{completed.stderr}"
                )
                return 1

    print("README examples passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
