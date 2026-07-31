"""Inspect built distributions for required public artifacts and unsafe files."""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
REQUIRED_WHEEL = {
    "recipeflow/contracts/recipeflow-contracts.d.ts",
    "recipeflow/examples/espresso-brownies.recipe.yaml",
    "recipeflow/schemas/recipeflow-analysis-v1.schema.json",
    "recipeflow/schemas/recipeflow-cli-result-v1.schema.json",
    "recipeflow/schemas/recipeflow-diagnostic-v1.schema.json",
    "recipeflow/schemas/recipeflow-document-v1.schema.json",
    "recipeflow/schemas/recipeflow-graph-v1.schema.json",
    "recipeflow/schemas/recipeflow-render-result-v1.schema.json",
    "recipeflow/schemas/recipeflow-tabular-layout-v1.schema.json",
}
FORBIDDEN_SUFFIXES = (".key", ".pem", ".p12", ".pfx")


def main() -> int:
    wheels = sorted(DIST.glob("recipeflow-*.whl"))
    sdists = sorted(DIST.glob("recipeflow-*.tar.gz"))
    errors: list[str] = []
    if len(wheels) != 1:
        errors.append(f"expected one wheel, found {len(wheels)}")
    if len(sdists) != 1:
        errors.append(f"expected one source distribution, found {len(sdists)}")

    if wheels:
        with zipfile.ZipFile(wheels[0]) as archive:
            names = set(archive.namelist())
        missing = sorted(REQUIRED_WHEEL - names)
        if missing:
            errors.append(f"wheel is missing public artifacts: {', '.join(missing)}")
        forbidden = sorted(name for name in names if name.lower().endswith(FORBIDDEN_SUFFIXES))
        if forbidden:
            errors.append(f"wheel contains forbidden sensitive files: {', '.join(forbidden)}")

    if sdists:
        with tarfile.open(sdists[0], mode="r:gz") as archive:
            names = [member.name for member in archive.getmembers()]
        forbidden = sorted(name for name in names if name.lower().endswith(FORBIDDEN_SUFFIXES))
        if forbidden:
            errors.append(f"sdist contains forbidden sensitive files: {', '.join(forbidden)}")

    if errors:
        print("\n".join(errors))
        return 1
    print("Package check passed: wheel and source distribution")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
