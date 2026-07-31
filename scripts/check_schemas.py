"""Verify all reviewed public schemas regenerate byte-for-byte."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = (
    "document",
    "graph",
    "diagnostic",
    "analysis",
    "tabular-layout",
    "render-result",
    "cli-result",
)


def main() -> int:
    errors: list[str] = []
    for contract in CONTRACTS:
        path = ROOT / "schemas" / f"recipeflow-{contract}-v1.schema.json"
        if not path.is_file():
            errors.append(f"missing public schema: {path.relative_to(ROOT)}")
            continue
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "recipeflow.cli.main",
                "schema",
                "--contract",
                contract,
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            errors.append(f"{contract}: schema export failed: {completed.stderr}")
            continue
        expected = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        actual = completed.stdout.replace("\r\n", "\n")
        if actual != expected:
            errors.append(f"{contract}: committed schema differs from deterministic export")

    if errors:
        print("\n".join(errors))
        return 1
    print(f"Schema determinism check passed: {len(CONTRACTS)} contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
