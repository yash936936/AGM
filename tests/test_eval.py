from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_synthetic_eval_reports_flat_graph_quality_and_latency_metrics() -> None:
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    src = str(root / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    result = subprocess.run(
        [sys.executable, str(root / "eval" / "stale_facts.py"), "--k", "5", "--repeats", "2"],
        cwd=root, env=env, capture_output=True, text=True, check=False, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "flat" in result.stdout and "graph" in result.stdout
    assert "stale-error" in result.stdout
    assert "abstention" in result.stdout
    assert "p50 ms" in result.stdout and "p95 ms" in result.stdout and "p99 ms" in result.stdout
    assert "q/s" in result.stdout and "errors" in result.stdout
    assert "D-007" in result.stdout and "not evidence" in result.stdout


def test_synthetic_eval_rejects_invalid_repeats() -> None:
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    src = str(root / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    result = subprocess.run(
        [sys.executable, str(root / "eval" / "stale_facts.py"), "--repeats", "0"],
        cwd=root, env=env, capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == 2
    assert "--repeats must be at least 1" in result.stderr
