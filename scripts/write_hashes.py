"""Write deterministic SHA-256 hashes for built distribution artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
OUTPUT = DIST / "SHA256SUMS"


def main() -> int:
    artifacts = sorted((*DIST.glob("*.whl"), *DIST.glob("*.tar.gz")), key=lambda item: item.name)
    if not artifacts:
        print("No distribution artifacts found")
        return 1
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in artifacts]
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
