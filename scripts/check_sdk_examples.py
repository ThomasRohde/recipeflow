"""Execute the documented SDK examples as smoke tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = (
    ROOT / "examples" / "sdk" / "basic.py",
    ROOT / "examples" / "sdk" / "fastapi_style.py",
    ROOT / "examples" / "sdk" / "incremental_editor.py",
    ROOT / "examples" / "sdk" / "direct_layout.py",
)


def main() -> int:
    errors: list[str] = []
    for example in EXAMPLES:
        completed = subprocess.run(
            [sys.executable, str(example)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            errors.append(f"{example.name}: {completed.stdout}{completed.stderr}")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"SDK example check passed: {len(EXAMPLES)} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
