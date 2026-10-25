#!/usr/bin/env python3
"""Paired flat-vs-graph benchmark runner for a frozen AGM JSONL case set."""
from __future__ import annotations

import argparse
import concurrent.futures
import os
import platform
import json
import math
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from agm import MemoryStore
from scripts.evaluate_real_history import _ctx

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


def peak_rss_bytes() -> int | None:
    """Return process peak resident/working-set bytes using the standard library."""
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes
            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ]
            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(counters)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            ok = ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
            return int(counters.PeakWorkingSetSize) if ok else None
        except (AttributeError, OSError):
            return None
    try:
        import resource
        peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return peak if platform.system() == "Darwin" else peak * 1024
    except (ImportError, OSError, ValueError):
        return None


def _concurrent_case_retrieval(case: dict[str, Any], db_path: Path, mode: str,
                               workers: int, requests: int) -> dict[str, Any]:
    query = case["query"]
    ctx = _ctx(query, "query")
    def one_request(_: int) -> float:
        started = time.perf_counter()
        with MemoryStore(str(db_path)) as store:
            store.retrieve(ctx, query["text"], entity=query.get("entity"),
                           as_of=query.get("as_of"), k=query.get("k", 5),
                           expand=mode == "graph", high_stakes=query.get("high_stakes", False))
        return (time.perf_counter() - started) * 1000.0
    started = time.perf_counter()
    latencies: list[float] = []
    errors = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(one_request, index) for index in range(requests)]
        for future in concurrent.futures.as_completed(futures):
            try:
                latencies.append(future.result())
            except Exception:
                errors += 1
    return {"latencies_ms": latencies, "errors": errors,
            "elapsed_seconds": time.perf_counter() - started}


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
    operation_samples: dict[str, list[float]] = {}
    for row in rows:
        for sample in row.get("operation_timings", []):
            operation_samples.setdefault(str(sample["operation"]), []).append(float(sample["latency_ms"]))
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
        "operation_latency_ms": {name: {"count": len(samples), **{f"p{p}": percentile(samples, p / 100) for p in (50, 95, 99)}} for name, samples in sorted(operation_samples.items())},
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
                  include_case_details: bool = False, concurrency: int = 0, concurrent_requests: int = 100) -> dict[str, Any]:
    thresholds = (min_case_pass_rate, min_expected_recall, min_abstention_accuracy)
    if any(not math.isfinite(x) or not 0 <= x <= 1 for x in thresholds):
        raise ValueError("thresholds must be between 0 and 1")
    if type(concurrency) is not int or concurrency < 0 or concurrency > 128:
        raise ValueError("concurrency must be between 0 and 128")
    if type(concurrent_requests) is not int or concurrent_requests < 1:
        raise ValueError("concurrent_requests must be a positive integer")
    cases = load_cases(path)
    rows = {"flat": [], "graph": []}
    concurrent_samples = {"flat": [], "graph": []}
    concurrent_elapsed = {"flat": 0.0, "graph": 0.0}
    concurrent_errors = {"flat": 0, "graph": 0}
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
                db_path = Path(tmp) / "case.db"
                result = evaluate_case(case, db_path)
                duration = (time.perf_counter() - started) * 1000
                if concurrency:
                    load = _concurrent_case_retrieval(case, db_path, mode, concurrency, concurrent_requests)
                    concurrent_samples[mode].extend(load["latencies_ms"])
                    concurrent_elapsed[mode] += load["elapsed_seconds"]
                    concurrent_errors[mode] += load["errors"]
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
        "protocol": "paired_flat_vs_graph_v3", "cases": len(cases),
        "process_peak_rss_bytes": peak_rss_bytes(),
        "modes": modes,
        "comparison": {
            "graph_minus_flat_recall": None if flat_recall is None or graph_recall is None else round(graph_recall - flat_recall, 6),
            "graph_minus_flat_retrieval_p95_ms": None if flat_p95 is None or graph_p95 is None else round(graph_p95 - flat_p95, 4),
        },
    }
    if concurrency:
        report["concurrent_retrieval"] = {mode: {
            "workers": concurrency, "requests_per_case": concurrent_requests,
            "requests": len(concurrent_samples[mode]), "errors": concurrent_errors[mode],
            "latency_ms": {f"p{p}": percentile(concurrent_samples[mode], p / 100) for p in (50, 95, 99)},
            "throughput_requests_per_second": round(len(concurrent_samples[mode]) / concurrent_elapsed[mode], 4) if concurrent_elapsed[mode] else None,
            "elapsed_seconds": round(concurrent_elapsed[mode], 4),
        } for mode in rows}
    if include_case_details:
        report["case_details"] = details
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--include-case-details", action="store_true")
    parser.add_argument("--concurrency", type=int, default=0, help="enable concurrent retrieval load with this worker count")
    parser.add_argument("--concurrent-requests", type=int, default=100, help="requests per case and mode when concurrency is enabled")
    parser.add_argument("--min-case-pass-rate", type=float, default=DEFAULT_MIN_CASE_PASS_RATE)
    parser.add_argument("--min-expected-recall", type=float, default=DEFAULT_MIN_EXPECTED_RECALL)
    parser.add_argument("--min-abstention-accuracy", type=float, default=DEFAULT_MIN_ABSTENTION_ACCURACY)
    args = parser.parse_args()
    try:
        report = run_benchmark(args.benchmark, min_case_pass_rate=args.min_case_pass_rate,
                               min_expected_recall=args.min_expected_recall,
                               min_abstention_accuracy=args.min_abstention_accuracy,
                               include_case_details=args.include_case_details, concurrency=args.concurrency,
                               concurrent_requests=args.concurrent_requests)
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
