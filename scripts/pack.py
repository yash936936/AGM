#!/usr/bin/env python3
"""Create safe AGM source and overlay ZIPs for the latest implemented phase."""
from __future__ import annotations

from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {
    ".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist",
    "build", "site-packages",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".db", ".sqlite", ".sqlite3"}
EXCLUDED_ENDINGS = {".egg-info"}
OVERLAY_FILES = [
    ".gitignore", "README.md", "context.md", "pyproject.toml", "scripts/pack.py",
    "PHASE1_REPORT.md", "PHASE2_REPORT.md", "PHASE3_REPORT.md", "PHASE4_REPORT.md",
    "docs/decisions.md", "docs/debug.md", "docs/phases.md", "docs/readme.md", "docs/status.md",
    "docs/phase4_contract_addendum.md",
    "src/agm/__init__.py", "src/agm/__main__.py", "src/agm/api.py", "src/agm/cli.py",
    "src/agm/config.py", "src/agm/db.py", "src/agm/embed.py", "src/agm/events.py",
    "src/agm/guard.py", "src/agm/handoff.py", "src/agm/mcp_server.py", "src/agm/models.py",
    "src/agm/retrieve.py", "src/agm/store.py", "src/agm/trust.py",
    "tests/test_store.py", "tests/test_replay.py", "tests/test_retrieve.py", "tests/test_contested.py",
    "tests/test_trust_phase2.py", "tests/test_trust.py", "tests/test_handoff.py",
    "tests/test_guard.py", "tests/test_e2e_rest.py", "tests/test_mcp_stdio.py",
    "examples/agm.keys.example.json", "examples/python_client.py", "examples/curl.md",
    "examples/claude_code_mcp.md", "examples/chatgpt_actions.md",
]


def latest_phase() -> int:
    for phase in (5, 4, 3, 2, 1):
        if (ROOT / f"PHASE{phase}_REPORT.md").is_file():
            return phase
    raise SystemExit("A PHASEN_REPORT.md must exist before packaging")


def included(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    if any(part.endswith(ending) for part in rel.parts for ending in EXCLUDED_ENDINGS):
        return False
    if path.name == "agm.keys.json" or path.name == ".env":
        return False
    if path.name.startswith(".env.") and path.name not in {".env.example"}:
        return False
    return path.is_file()


def main() -> int:
    phase = latest_phase()
    report = ROOT / f"PHASE{phase}_REPORT.md"
    if not report.is_file():
        raise SystemExit(f"{report.name} must exist before Phase {phase} packaging")

    dist = ROOT / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    workspace_zip = dist / f"agm-phase{phase}.zip"
    overlay_zip = dist / f"agm-phase{phase}-overlay.zip"

    with zipfile.ZipFile(workspace_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if included(path):
                archive.write(path, (Path("agm") / path.relative_to(ROOT)).as_posix())

    missing = [rel for rel in OVERLAY_FILES if not (ROOT / rel).is_file()]
    if missing:
        raise SystemExit("Missing Phase overlay files: " + ", ".join(missing))
    with zipfile.ZipFile(overlay_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for rel in OVERLAY_FILES:
            path = ROOT / rel
            if included(path):
                archive.write(path, rel)

    print(f"Created {workspace_zip} ({workspace_zip.stat().st_size} bytes)")
    print(f"Created {overlay_zip} ({overlay_zip.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
