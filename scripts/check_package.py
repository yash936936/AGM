#!/usr/bin/env python3
"""Build the wheel and reject private/local artifacts in its payload."""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

FORBIDDEN = re.compile(
    r"(^|/)(\.env(?:\..*)?|agm\.keys\.json|credentials?(?:\.json)?|"
    r"secrets?\.(?:json|ya?ml)|.*\.(?:db|sqlite|sqlite3|pem|p12|pfx|key))"
    r"(?:$|-(?:wal|shm|journal)$)",
    re.IGNORECASE,
)
FORBIDDEN_PARTS = {".git", ".venv", "__pycache__", "tests", "logs"}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="agm-wheel-check-") as tmp:
        wheel_dir = Path(tmp) / "wheel"
        wheel_dir.mkdir()
        subprocess.run(
            [sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "--wheel-dir", str(wheel_dir)],
            cwd=root,
            check=True,
        )
        wheels = list(wheel_dir.glob("*.whl"))
        if len(wheels) != 1:
            raise SystemExit(f"Expected one wheel, found {len(wheels)}")
        with zipfile.ZipFile(wheels[0]) as archive:
            names = archive.namelist()
        bad = [
            name for name in names
            if FORBIDDEN.search(name)
            or any(part in FORBIDDEN_PARTS for part in name.split("/"))
        ]
        if bad:
            print("Package inspection: FAIL")
            for name in bad:
                print(f"- forbidden package entry: {name}")
            return 1
        modules = [name for name in names if name.startswith("agm/") and name.endswith(".py")]
        if not modules:
            print("Package inspection: FAIL (no agm Python modules found)")
            return 1
        print(f"Package inspection: PASS ({len(names)} entries; {len(modules)} Python modules)")
        print("Only wheel contents were inspected; this is not a complete supply-chain or secret audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
