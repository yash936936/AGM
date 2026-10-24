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
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".db", ".sqlite", ".sqlite3", ".db-wal", ".db-shm", ".db-journal"}
EXCLUDED_ENDINGS = {".egg-info"}

# Phase 6 is evaluation-only and Phase 7 is a patch-based retrieval diagnostic.
# Both are layered onto a supervisor-hardened v0.5.1 tree.
# Keep this overlay intentionally selective so src/agm, the core guard, delete
# durability and repo-hygiene fixes are not overwritten by an older build snapshot.
PHASE6_OVERLAY_FILES = [
    "README.md", "scripts/pack.py", "PHASE6_REPORT.md",
    "docs/decisions.md", "docs/debug.md", "docs/status.md",
    "eval/synthetic_v2.py", "tests/test_eval_v2.py",
]

# Phase 7 ships a unified patch rather than replacement source files. This avoids
# overwriting the owner's D-021–D-023 hardening work with the older builder snapshot.
PHASE7_OVERLAY_FILES = ["PHASE7_PATCH.diff", "PHASE7_REPORT.md"]

# Kept complete for packaging older phases and for the full project ZIP on a checkout
# containing the current source tree.
OVERLAY_FILES = [
    ".gitignore", "README.md", "context.md", "pyproject.toml", "scripts/pack.py",
    "PHASE1_REPORT.md", "PHASE2_REPORT.md", "PHASE3_REPORT.md", "PHASE4_REPORT.md", "PHASE5_REPORT.md",
    "docs/decisions.md", "docs/debug.md", "docs/phases.md", "docs/readme.md", "docs/status.md",
    "docs/phase4_contract_addendum.md",
    "src/agm/__init__.py", "src/agm/__main__.py", "src/agm/api.py", "src/agm/cli.py",
    "src/agm/config.py", "src/agm/db.py", "src/agm/embed.py", "src/agm/events.py",
    "src/agm/guard.py", "src/agm/handoff.py", "src/agm/mcp_server.py", "src/agm/models.py",
    "src/agm/retrieve.py", "src/agm/store.py", "src/agm/trust.py",
    "tests/test_store.py", "tests/test_replay.py", "tests/test_retrieve.py", "tests/test_contested.py",
    "tests/test_trust_phase2.py", "tests/test_trust.py", "tests/test_handoff.py",
    "tests/test_guard.py", "tests/test_e2e_rest.py", "tests/test_mcp_stdio.py",
    "tests/test_lifecycle.py", "tests/test_eval.py", "tests/test_cli.py", "eval/stale_facts.py",
    "examples/agm.keys.example.json", "examples/python_client.py", "examples/curl.md",
    "examples/claude_code_mcp.md", "examples/chatgpt_actions.md",
    "examples/mcp_smoke_client.py", "examples/rest_smoke_client.py",
    "tests/test_guard_core.py", "tests/test_delete_ondisk.py", "tests/test_smoke_clients.py",
    "AGENTS.md", "prompts/builder_system_prompt.md", "prompts/phase_brief_template.md",
    "docs/workflow.md",
]


def latest_phase() -> int:
    for phase in (7, 6, 5, 4, 3, 2, 1):
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

    if phase == 7:
        overlay_files = list(PHASE7_OVERLAY_FILES)
        results_dir = ROOT / "eval" / "results"
        if results_dir.exists():
            overlay_files.extend(
                path.relative_to(ROOT).as_posix()
                for path in sorted(results_dir.glob("*.json")) if path.is_file()
            )
    elif phase == 6:
        overlay_files = list(PHASE6_OVERLAY_FILES)
        results_dir = ROOT / "eval" / "results"
        if results_dir.exists():
            overlay_files.extend(
                path.relative_to(ROOT).as_posix()
                for path in sorted(results_dir.glob("*.json")) if path.is_file()
            )
    else:
        overlay_files = OVERLAY_FILES
    missing = [rel for rel in overlay_files if not (ROOT / rel).is_file()]
    if missing:
        raise SystemExit("Missing Phase overlay files: " + ", ".join(missing))
    with zipfile.ZipFile(overlay_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for rel in overlay_files:
            path = ROOT / rel
            if included(path):
                archive.write(path, rel)

    print(f"Created {workspace_zip} ({workspace_zip.stat().st_size} bytes)")
    print(f"Created {overlay_zip} ({overlay_zip.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
