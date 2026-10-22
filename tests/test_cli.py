from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_demo_reports_current_phase_and_completes_handoff() -> None:
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    src = str(root / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    result = subprocess.run(
        [sys.executable, "-m", "agm", "demo"],
        cwd=root, env=env, capture_output=True, text=True, check=False, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "agm.phase = Phase 5" in result.stdout
    assert "Phase 3" not in result.stdout
    assert "Handoff readback passed: True" in result.stdout
