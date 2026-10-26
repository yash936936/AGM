#!/usr/bin/env python3
"""Repeated-run wrapper for AGM's synthetic retrieval smoke benchmark.

This adds run-to-run uncertainty summaries; it remains synthetic and sequential.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import random
import subprocess
import sys
from pathlib import Path
from statistics import median
from typing import Any

METRICS = (
    "accuracy", "stale_error", "abstention", "latency_p50_ms",
    "latency_p95_ms", "latency_p99_ms", "throughput_qps", "errors",
)


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * q + 0.5)))
    return ordered[index]


def bootstrap_median_interval(
    values: list[float], *, seed: int, samples: int = 2000, confidence: float = 0.95
) -> dict[str, float]:
    """Percentile bootstrap interval for the median of independent run summaries."""
    if not values:
        return {"lower": 0.0, "upper": 0.0}
    if len(values) == 1:
        return {"lower": values[0], "upper": values[0]}
    rng = random.Random(seed)
    estimates = [
        median([rng.choice(values) for _ in values])
        for _ in range(samples)
    ]
    alpha = (1.0 - confidence) / 2.0
    return {
        "lower": percentile(estimates, alpha),
        "upper": percentile(estimates, 1.0 - alpha),
    }


def run_once(*, k: int, repeats: int, archive_size: int) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    command = [
        sys.executable, str(root / "eval" / "stale_facts.py"),
        "--k", str(k), "--repeats", str(repeats),
        "--archive-size", str(archive_size), "--format", "json",
    ]
    env = os.environ.copy()
    src = str(root / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    result = subprocess.run(
        command, cwd=root, env=env, capture_output=True, text=True,
        check=False, timeout=180,
    )
    if result.returncode:
        raise RuntimeError(
            f"underlying benchmark exited {result.returncode}: {result.stderr.strip()}"
        )
    return json.loads(result.stdout)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=10, help="independent benchmark processes (minimum 2 for uncertainty)")
    parser.add_argument("--repeats", type=int, default=25, help="timed repetitions per scenario in each process")
    parser.add_argument("--archive-size", type=int, default=60, help="unrelated synthetic archive records per mode")
    parser.add_argument("--k", type=int, default=5, help="maximum returned memories per scenario")
    parser.add_argument("--seed", type=int, default=20261026, help="seed for bootstrap resampling")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    if args.runs < 1:
        parser.error("--runs must be at least 1")
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")
    if args.archive_size < 0:
        parser.error("--archive-size must be at least 0")
    if args.k < 1:
        parser.error("--k must be at least 1")

    runs = [run_once(k=args.k, repeats=args.repeats, archive_size=args.archive_size) for _ in range(args.runs)]
    modes = sorted({entry["mode"] for run in runs for entry in run["results"]})
    summary: dict[str, Any] = {}
    for mode_index, mode in enumerate(modes):
        entries = [next(row for row in run["results"] if row["mode"] == mode) for run in runs]
        mode_summary: dict[str, Any] = {"runs": len(entries)}
        for metric in METRICS:
            values = [float(entry[metric]) for entry in entries]
            mode_summary[metric] = {
                "median": median(values),
                "bootstrap_95pct_ci_for_median": bootstrap_median_interval(
                    values, seed=args.seed + mode_index * 100 + len(metric)
                ),
                "per_run": values,
            }
        summary[mode] = mode_summary

    payload = {
        "benchmark": "agm_synthetic_repeated_retrieval_smoke",
        "benchmark_type": "synthetic_diagnostic_not_production_benchmark",
        "metadata": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "git_commit": os.environ.get("GITHUB_SHA", "not-injected"),
            "runs": args.runs,
            "timed_repeats_per_scenario_per_run": args.repeats,
            "archive_size_per_mode": args.archive_size,
            "top_k": args.k,
            "bootstrap_seed": args.seed,
            "bootstrap_resamples": 2000,
            "confidence_level": 0.95,
            "aggregation": "median across independent process-level summaries",
        },
        "summary": summary,
        "raw_runs": runs,
        "caveats": [
            "All cases and archive records are synthetic and hand-authored; this is not held-out real-history evidence.",
            "Confidence intervals describe run-to-run variability for this setup, not uncertainty across users, datasets, hosts, or machines.",
            "The underlying timings measure sequential retrieval calls only; setup, process startup, network, model inference, concurrent load, and end-to-end latency are excluded.",
            "Run count, Python/platform, commit, dependencies, and host load must be controlled before comparing builds.",
            "A one-run result has a degenerate interval and is not a meaningful uncertainty estimate; use at least 10 independent runs for comparisons.",
        ],
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print("AGM repeated synthetic retrieval benchmark (diagnostic only)")
    print(f"runs={args.runs} repeats/run={args.repeats} archive_size={args.archive_size} k={args.k}")
    print("Intervals: 95% percentile bootstrap intervals for the median of independent process-level summaries.")
    print("mode   metric              median       95% interval")
    for mode, metrics in summary.items():
        for metric in ("accuracy", "stale_error", "latency_p50_ms", "latency_p95_ms", "latency_p99_ms", "throughput_qps", "errors"):
            item = metrics[metric]
            interval = item["bootstrap_95pct_ci_for_median"]
            print(f"{mode:<6} {metric:<19} {item['median']:>10.4f} [{interval['lower']:.4f}, {interval['upper']:.4f}]")
    print("Not a production benchmark: no real histories, concurrent workload, or end-to-end latency.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
