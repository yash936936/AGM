#!/usr/bin/env python3
"""Create a self-contained AGM source archive using only the standard library.

If PHASE2_REPORT.md exists, create dist/agm-phase2.zip. Otherwise preserve the
Phase 1 behavior and create dist/agm-phase1.zip.
"""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "dist"}
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
    phase2_report = ROOT / "PHASE2_REPORT.md"
    phase1_report = ROOT / "PHASE1_REPORT.md"
    if phase2_report.exists():
        report = phase2_report
        destination = ROOT / "dist" / "agm-phase2.zip"
    else:
        report = phase1_report
        destination = ROOT / "dist" / "agm-phase1.zip"
    if not report.exists():
        raise SystemExit(f"{report.name} must exist before packaging")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if included(path):
                archive.write(path, (Path("agm") / path.relative_to(ROOT)).as_posix())
    print(f"Created {destination} ({destination.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
