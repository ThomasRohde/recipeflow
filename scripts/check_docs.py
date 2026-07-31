"""Check required documentation structure and local Markdown links."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md",
    "AGENTS.md",
    "CHANGELOG.md",
    "docs/ARCHITECTURE.md",
    "docs/LANGUAGE.md",
    "docs/ROADMAP.md",
    "docs/TABULAR-NOTATION.md",
    "docs/LAYOUT-ENGINE.md",
    "docs/PUBLIC-API.md",
    "docs/CLI.md",
    "docs/SCHEMA-VERSIONING.md",
    "docs/VISUAL-QUALITY.md",
    "docs/ACCESSIBILITY.md",
    "docs/CONTRIBUTING.md",
    "docs/SECURITY.md",
    "docs/PERFORMANCE.md",
    "docs/RELEASING.md",
)
README_HEADINGS = (
    "Install",
    "First document",
    "Python library",
    "CLI",
    "Codex authoring skill",
    "Supported semantics",
    "Current limitations",
    "Development",
)
LINK_RE = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)


def local_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    if target.startswith(("http://", "https://", "mailto:", "#", "data:")):
        return None
    target = unquote(target.split("#", 1)[0])
    return target or None


def main() -> int:
    errors: list[str] = []
    markdown_files: list[Path] = []

    for relative in REQUIRED:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing required documentation: {relative}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in README_HEADINGS:
        if f"## {heading}" not in readme:
            errors.append(f"README is missing heading: {heading}")

    markdown_files.extend(
        path
        for path in ROOT.rglob("*.md")
        if not any(part in {".git", ".venv", ".mypy_cache", ".pytest_cache"} for part in path.parts)
    )
    checked_links = 0
    for path in markdown_files:
        text = FENCE_RE.sub("", path.read_text(encoding="utf-8"))
        for match in LINK_RE.finditer(text):
            target = local_target(match.group(1))
            if target is None:
                continue
            checked_links += 1
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errors.append(
                    f"{path.relative_to(ROOT)}: broken local link {match.group(1)!r}"
                )

    if errors:
        print("\n".join(errors))
        return 1

    print(f"Documentation check passed: {len(markdown_files)} files, {checked_links} local links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
