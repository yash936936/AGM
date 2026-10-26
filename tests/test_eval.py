from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _run_eval(*args: str) -> subprocess.CompletedProcess[str]:
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    src = str(root / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return subprocess.run(
        [sys.executable, str(root / "eval" / "stale_facts.py"), *args],
        cwd=root, env=env, capture_output=True, text=True, check=False, timeout=60,
    )


def test_synthetic_eval_reports_flat_graph_quality_and_latency_metrics() -> None:
    result = _run_eval("--k", "5", "--repeats", "2")
    assert result.returncode == 0, result.stderr
    assert "flat" in result.stdout and "graph" in result.stdout
    assert "stale-error" in result.stdout
    assert "abstention" in result.stdout
    assert "p50 ms" in result.stdout and "p95 ms" in result.stdout and "p99 ms" in result.stdout
    assert "q/s" in result.stdout and "errors" in result.stdout
    assert "D-007" in result.stdout and "not evidence" in result.stdout


def test_synthetic_eval_json_is_machine_readable_and_caveated() -> None:
    result = _run_eval("--k", "5", "--repeats", "2", "--format", "json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["benchmark_type"] == "synthetic_smoke_not_production_benchmark"
    assert payload["metadata"]["timed_queries_per_mode"] == 8
    assert payload["metadata"]["top_k"] == 5
    assert payload["metadata"]["synthetic_archive_size_per_mode"] == 60
    assert all(mode["archive_size"] == 60 for mode in payload["results"])
    assert len(payload["results"]) == 2
    for mode in payload["results"]:
        assert mode["mode"] in {"flat", "graph"}
        assert {"accuracy", "stale_error", "abstention", "latency_p50_ms", "latency_p95_ms", "latency_p99_ms", "throughput_qps", "queries", "errors"} <= mode.keys()
    assert any("not evidence" in caveat for caveat in payload["caveats"])


def test_synthetic_eval_rejects_invalid_repeats() -> None:
    result = _run_eval("--repeats", "0")
    assert result.returncode == 2
    assert "--repeats must be at least 1" in result.stderr


def test_synthetic_eval_accepts_archive_size_and_reports_it() -> None:
    result = _run_eval("--k", "3", "--repeats", "1", "--archive-size", "0", "--format", "json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["metadata"]["synthetic_archive_size_per_mode"] == 0
    assert all(mode["archive_size"] == 0 for mode in payload["results"])


def test_synthetic_eval_rejects_negative_archive_size() -> None:
    result = _run_eval("--archive-size", "-1")
    assert result.returncode == 2
    assert "--archive-size must be at least 0" in result.stderr
