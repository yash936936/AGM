from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "eval" / "rest_concurrent_benchmark.py"


def test_rest_concurrent_benchmark_rejects_invalid_workload() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--requests", "0"],
        cwd=ROOT, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 2
    assert "requests/concurrency must be positive" in result.stderr


def test_rest_concurrent_benchmark_reports_end_to_end_http_metrics() -> None:
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--requests", "6", "--concurrency", "2",
         "--warmup", "1", "--seed-items", "3"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    report = json.loads(result.stdout)
    assert report["benchmark"] == "agm_rest_concurrent_retrieval"
    assert report["workload"]["requests_requested"] == 6
    assert report["workload"]["requests_succeeded"] == 6
    assert report["workload"]["concurrency"] == 2
    assert report["workload"]["errors"] == 0
    assert report["latency_ms"]["p50"] is not None
    assert report["latency_ms"]["p95"] is not None
    assert report["latency_ms"]["p99"] is not None
    assert report["throughput"]["successful_requests_per_second"] > 0
    assert report["limitations"]
