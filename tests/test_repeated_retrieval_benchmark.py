from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _run_repeated(*args: str) -> subprocess.CompletedProcess[str]:
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    src = str(root / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return subprocess.run(
        [sys.executable, str(root / "eval" / "repeated_retrieval_benchmark.py"), *args],
        cwd=root, env=env, capture_output=True, text=True, check=False, timeout=180,
    )


def test_repeated_benchmark_reports_per_run_medians_and_intervals() -> None:
    result = _run_repeated(
        "--runs", "2", "--repeats", "1", "--archive-size", "0", "--format", "json",
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["benchmark_type"] == "synthetic_diagnostic_not_production_benchmark"
    assert payload["metadata"]["runs"] == 2
    assert payload["metadata"]["archive_size_per_mode"] == 0
    assert len(payload["raw_runs"]) == 2
    assert set(payload["summary"]) == {"flat", "graph"}
    for mode in payload["summary"].values():
        assert mode["runs"] == 2
        for metric in ("latency_p50_ms", "latency_p95_ms", "latency_p99_ms", "throughput_qps"):
            item = mode[metric]
            assert len(item["per_run"]) == 2
            interval = item["bootstrap_95pct_ci_for_median"]
            assert interval["lower"] <= interval["upper"]
            assert item["median"] >= 0
    assert any("not held-out real-history" in caveat for caveat in payload["caveats"])


def test_repeated_benchmark_rejects_zero_runs() -> None:
    result = _run_repeated("--runs", "0")
    assert result.returncode == 2
    assert "--runs must be at least 1" in result.stderr
