"""Check package, changelog, and optional Git tag version agreement."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    version = str(project["version"])
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    errors: list[str] = []

    if f"## {version} " not in changelog and f"## {version}\n" not in changelog:
        errors.append(f"CHANGELOG.md has no release heading for {version}")

    ref_name = os.environ.get("GITHUB_REF_NAME", "")
    if ref_name.startswith("v") and ref_name[1:] != version:
        errors.append(f"tag {ref_name} does not match package version {version}")

    if errors:
        print("\n".join(errors))
        return 1
    print(f"Release metadata check passed: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
