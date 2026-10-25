#!/usr/bin/env python3
"""Paired flat-vs-graph benchmark runner for a frozen AGM JSONL case set."""
from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from scripts.evaluate_real_history import (
    DEFAULT_MIN_ABSTENTION_ACCURACY, DEFAULT_MIN_CASE_PASS_RATE,
    DEFAULT_MIN_EXPECTED_RECALL, ZERO_TOLERANCE_SCENARIOS,
    evaluate_case, load_cases,
)


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    position = (len(values) - 1) * p
    lo, hi = math.floor(position), math.ceil(position)
    if lo == hi:
        return round(values[lo], 4)
    return round(values[lo] * (hi - position) + values[hi] * (position - lo), 4)


def summarize(rows: list[dict[str, Any]], elapsed: float, thresholds: tuple[float, float, float]) -> dict[str, Any]:
    count = len(rows)
    expected = sum(r["expected_count"] for r in rows)
    missing = sum(r["missing_count"] for r in rows)
    leaks = sum(r["leak_count"] for r in rows)
    passed = sum(bool(r["pass"]) for r in rows)
    checked = [r for r in rows if r["abstain_checked"]]
    recall = None if not expected else (expected - missing) / expected
    abstention = None if not checked else sum(bool(r["abstain_ok"]) for r in checked) / len(checked)
    zero_leaks = sum(r["scenario"] in ZERO_TOLERANCE_SCENARIOS and r["leak_count"] > 0 for r in rows)
    case_rate = passed / count
    failures = []
    if case_rate < thresholds[0]:
        failures.append("case_pass_rate")
    if recall is not None and recall < thresholds[1]:
        failures.append("expected_value_recall")
    if abstention is not None and abstention < thresholds[2]:
        failures.append("abstention_accuracy")
    if zero_leaks:
        failures.append("zero_tolerance_scenario_leak")
    retrieval = [float(r["retrieve_latency_ms"]) for r in rows]
    cases = [float(r["case_latency_ms"]) for r in rows]
    return {
        "cases": count, "case_passes": passed, "case_pass_rate": round(case_rate, 6),
        "expected_values": expected, "missing_expected_values": missing,
        "expected_value_recall": None if recall is None else round(recall, 6),
        "forbidden_values": sum(r["forbidden_count"] for r in rows),
        "forbidden_value_leaks": leaks, "zero_tolerance_failures": zero_leaks,
        "abstention_cases": len(checked),
        "abstention_accuracy": None if abstention is None else round(abstention, 6),
        "retrieval_latency_ms": {f"p{p}": percentile(retrieval, p / 100) for p in (50, 95, 99)},
        "end_to_end_case_latency_ms": {f"p{p}": percentile(cases, p / 100) for p in (50, 95, 99)},
        "throughput_cases_per_second": round(count / elapsed, 4) if elapsed else None,
        "elapsed_seconds": round(elapsed, 4),
        "database_size_bytes_max": max((int(r["database_size_bytes"]) for r in rows), default=0),
        "thresholds": {"min_case_pass_rate": thresholds[0], "min_expected_recall": thresholds[1],
                       "min_abstention_accuracy": thresholds[2]},
        "threshold_failures": failures,
        "release_gate_pass": not failures and all(bool(r["pass"]) for r in rows),
    }


def run_benchmark(path: Path, *, min_case_pass_rate: float = DEFAULT_MIN_CASE_PASS_RATE,
                  min_expected_recall: float = DEFAULT_MIN_EXPECTED_RECALL,
                  min_abstention_accuracy: float = DEFAULT_MIN_ABSTENTION_ACCURACY,
                  include_case_details: bool = False) -> dict[str, Any]:
    thresholds = (min_case_pass_rate, min_expected_recall, min_abstention_accuracy)
    if any(not math.isfinite(x) or not 0 <= x <= 1 for x in thresholds):
        raise ValueError("thresholds must be between 0 and 1")
    cases = load_cases(path)
    rows = {"flat": [], "graph": []}
    elapsed = {"flat": 0.0, "graph": 0.0}
    details = {"flat": [], "graph": []}
    # Alternate order per case to reduce systematic warm-up bias.
    for index, original in enumerate(cases):
        order = ("flat", "graph") if index % 2 == 0 else ("graph", "flat")
        for mode in order:
            case = json.loads(json.dumps(original))
            case.setdefault("query", {})["expand"] = mode == "graph"
            with tempfile.TemporaryDirectory(prefix=f"agm-bench-{mode}-") as tmp:
                started = time.perf_counter()
                result = evaluate_case(case, Path(tmp) / "case.db")
                duration = (time.perf_counter() - started) * 1000
            result["case_latency_ms"] = duration
            rows[mode].append(result)
            elapsed[mode] += duration / 1000
            details[mode].append({
                "case_index": index + 1, "scenario": result["scenario"],
                "pass": result["pass"], "missing_count": result["missing_count"],
                "leak_count": result["leak_count"],
                "retrieve_latency_ms": result["retrieve_latency_ms"],
                "case_latency_ms": round(duration, 4),
            })
    modes = {mode: summarize(rows[mode], elapsed[mode], thresholds) for mode in rows}
    flat_recall, graph_recall = (modes[m]["expected_value_recall"] for m in ("flat", "graph"))
    flat_p95, graph_p95 = (modes[m]["retrieval_latency_ms"]["p95"] for m in ("flat", "graph"))
    report = {
        "protocol": "paired_flat_vs_graph_v1", "benchmark_file": path.name, "cases": len(cases),
        "modes": modes,
        "comparison": {
            "graph_minus_flat_recall": None if flat_recall is None or graph_recall is None else round(graph_recall - flat_recall, 6),
            "graph_minus_flat_retrieval_p95_ms": None if flat_p95 is None or graph_p95 is None else round(graph_p95 - flat_p95, 4),
        },
    }
    if include_case_details:
        report["case_details"] = details
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--include-case-details", action="store_true")
    parser.add_argument("--min-case-pass-rate", type=float, default=DEFAULT_MIN_CASE_PASS_RATE)
    parser.add_argument("--min-expected-recall", type=float, default=DEFAULT_MIN_EXPECTED_RECALL)
    parser.add_argument("--min-abstention-accuracy", type=float, default=DEFAULT_MIN_ABSTENTION_ACCURACY)
    args = parser.parse_args()
    try:
        report = run_benchmark(args.benchmark, min_case_pass_rate=args.min_case_pass_rate,
                               min_expected_recall=args.min_expected_recall,
                               min_abstention_accuracy=args.min_abstention_accuracy,
                               include_case_details=args.include_case_details)
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    output = json.dumps(report, indent=2, sort_keys=True)
    print(output)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    return 0 if all(mode["release_gate_pass"] for mode in report["modes"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
