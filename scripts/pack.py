#!/usr/bin/env python3
"""Create the self-contained Phase 1 source archive using only the stdlib."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "dist" / "agm-phase1.zip"
EXCLUDED_DIRS = {".venv", "__pycache__", ".pytest_cache", "dist"}
EXCLUDED_SUFFIXES = {".pyc", ".db"}
EXCLUDED_ENDINGS = {".egg-info"}


def included(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    if any(part.endswith(ending) for part in rel.parts for ending in EXCLUDED_ENDINGS):
        return False
    return path.is_file()


def main() -> int:
    report = ROOT / "PHASE1_REPORT.md"
    if not report.exists():
        raise SystemExit("PHASE1_REPORT.md must exist before packaging")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(DEST, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if included(path):
                archive.write(path, (Path("agm") / path.relative_to(ROOT)).as_posix())
    print(f"Created {DEST} ({DEST.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
