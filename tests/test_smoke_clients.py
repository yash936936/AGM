"""Run the two end-to-end smoke clients as real subprocesses (real MCP stdio and real HTTP)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "examples" / script)],
        capture_output=True, text=True, timeout=120, cwd=ROOT,
    )


def test_rest_smoke_client_passes():
    result = _run("rest_smoke_client.py")
    assert result.returncode == 0, result.stdout + result.stderr


def test_mcp_smoke_client_passes():
    pytest.importorskip("mcp")
    result = _run("mcp_smoke_client.py")
    assert result.returncode == 0, result.stdout + result.stderr
