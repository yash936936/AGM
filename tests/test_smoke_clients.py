"""Run the REST smoke client as a real subprocess (real HTTP)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "examples" / script)],
        capture_output=True, text=True, timeout=120, cwd=ROOT,
    )


def test_rest_smoke_client_passes():
    result = _run("rest_smoke_client.py")
    assert result.returncode == 0, result.stdout + result.stderr
