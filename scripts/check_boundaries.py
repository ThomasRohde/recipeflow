"""Enforce the library-first and no-acquisition architecture boundaries."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "recipeflow"
PROHIBITED_IMPORTS = {
    "anthropic",
    "bs4",
    "httpx",
    "openai",
    "playwright",
    "requests",
    "selenium",
    "urllib.request",
}
PROHIBITED_DEPENDENCIES = {
    "anthropic",
    "beautifulsoup4",
    "httpx",
    "openai",
    "playwright",
    "requests",
    "selenium",
}


def imported_modules(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.lineno, node.module))
    return imports


def dependency_name(requirement: str) -> str:
    for separator in ("[", "<", ">", "=", "!", "~", " "):
        requirement = requirement.split(separator, 1)[0]
    return requirement.lower().replace("_", "-")


def main() -> int:
    errors: list[str] = []
    for path in sorted(PACKAGE.rglob("*.py")):
        relative = path.relative_to(ROOT)
        for line, module in imported_modules(path):
            if module == "recipeflow.cli" or module.startswith("recipeflow.cli."):
                if "cli" not in path.relative_to(PACKAGE).parts:
                    errors.append(f"{relative}:{line}: core code imports recipeflow.cli")
            if module in PROHIBITED_IMPORTS or any(
                module.startswith(f"{name}.") for name in PROHIBITED_IMPORTS
            ):
                errors.append(f"{relative}:{line}: prohibited acquisition/model import {module}")

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    dependencies = {
        dependency_name(requirement) for requirement in project.get("dependencies", ())
    }
    forbidden_dependencies = sorted(dependencies & PROHIBITED_DEPENDENCIES)
    if forbidden_dependencies:
        errors.append(
            "core dependencies contain prohibited acquisition/model packages: "
            + ", ".join(forbidden_dependencies)
        )

    if errors:
        print("\n".join(errors))
        return 1
    print("Architecture boundary check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
