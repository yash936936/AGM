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

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            kernel32.GetCurrentProcess.argtypes = []
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            psapi.GetProcessMemoryInfo.argtypes = [
                wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD,
            ]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(counters)
            handle = kernel32.GetCurrentProcess()
            ok = psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
            if not ok:
                return None
            value = int(counters.PeakWorkingSetSize)
            return value if value > 0 else None
        except (AttributeError, OSError, TypeError, ValueError):
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
    report["keyword_baseline"] = evaluate_keyword_baseline(cases)
    return report


def _keyword_tokens(value: str) -> set[str]:
    import re
    return {token for token in re.findall(r"[\\w]+", value.casefold()) if len(token) > 1}


def evaluate_keyword_baseline(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate a transparent lexical-overlap baseline on the same labelled fixtures.

    This is an independent fixture-level baseline, not AGM's SQLite FTS implementation
    and not a substitute for comparing against a separately deployed search service.
    """
    rows: list[dict[str, Any]] = []
    total_elapsed = 0.0
    for case in cases:
        started = time.perf_counter()
        active: list[dict[str, Any]] = []
        for memory in case["memories"]:
            active.append({
                "context": {
                    "tenant_id": memory.get("tenant_id"),
                    "project": memory.get("project", "eval"),
                    "writer_id": memory.get("writer_id", "eval-writer"),
                },
                "item": dict(memory["item"]), "created_at": memory.get("created_at"), "active": True,
            })
        for operation in case.get("operations", []):
            op_type = operation["type"]
            if op_type in {"correction", "delete"}:
                target = active[operation["target_memory_index"]]
                target["active"] = False
                if op_type == "correction":
                    active.append({
                        "context": {
                            "tenant_id": operation["context"].get("tenant_id"),
                            "project": operation["context"].get("project", "eval"),
                            "writer_id": operation["context"].get("writer_id", "eval-writer"),
                        },
                        "item": dict(operation["item"]), "created_at": None, "active": True,
                    })
            elif op_type == "revoke_writer":
                from datetime import datetime, timezone
                op_ctx = operation["context"]
                since_text = operation.get("since")
                since = None
                if since_text:
                    since = datetime.fromisoformat(since_text[:-1] + "+00:00" if since_text.endswith("Z") else since_text)
                    if since.tzinfo is None:
                        since = since.replace(tzinfo=timezone.utc)
                for memory in active:
                    if (memory["context"]["tenant_id"] != op_ctx["tenant_id"]
                        or memory["context"]["writer_id"] != operation["writer_id"]):
                        continue
                    created_text = memory["created_at"]
                    if since is not None and created_text:
                        created_text = created_text[:-1] + "+00:00" if created_text.endswith("Z") else created_text
                        created = datetime.fromisoformat(created_text)
                        if created.tzinfo is None:
                            created = created.replace(tzinfo=timezone.utc)
                        if created < since:
                            continue
                    elif since is not None and not created_text:
                        # Seeded writes without an explicit timestamp are created "now"
                        # by AGM, so only include them when the cutoff is not in the future.
                        if since > datetime.now(timezone.utc):
                            continue
                    memory["active"] = False
            elif op_type == "expire_before":
                from datetime import datetime, timezone
                cutoff_text = operation["cutoff"]
                cutoff = datetime.fromisoformat(cutoff_text[:-1] + "+00:00" if cutoff_text.endswith("Z") else cutoff_text)
                if cutoff.tzinfo is None:
                    cutoff = cutoff.replace(tzinfo=timezone.utc)
                for memory in active:
                    created = memory["created_at"]
                    if not created:
                        continue
                    created_text = created[:-1] + "+00:00" if created.endswith("Z") else created
                    created_dt = datetime.fromisoformat(created_text)
                    if created_dt.tzinfo is None:
                        created_dt = created_dt.replace(tzinfo=timezone.utc)
                    item_ctx = memory["context"]
                    if (item_ctx["tenant_id"] == operation["context"]["tenant_id"]
                        and item_ctx["project"] == operation["context"].get("project", "eval")
                        and created_dt <= cutoff
                        and (operation.get("include_pinned", False) or memory["item"].get("pin") is not True)):
                        memory["active"] = False
        query = case["query"]
        retrieve_started = time.perf_counter()
        query_text = str(query["text"]) + " " + str(query.get("entity", ""))
        query_tokens = _keyword_tokens(query_text)
        candidates = []
        for index, memory in enumerate(active):
            if not memory["active"]:
                continue
            ctx = memory["context"]
            if ctx["tenant_id"] != query["tenant_id"] or ctx["project"] != query.get("project", "eval"):
                continue
            item = memory["item"]
            document = " ".join(str(item.get(key, "")) for key in ("kind", "entity", "attribute", "value", "text"))
            tokens = _keyword_tokens(document)
            overlap = len(query_tokens & tokens)
            if overlap:
                candidates.append((overlap / max(1, len(query_tokens)), -index, item))
        candidates.sort(key=lambda row: (row[0], row[1]), reverse=True)
        top = candidates[:query.get("k", 5)]
        retrieved_values = {str(row[2].get("value")) for row in top if row[2].get("value") is not None}
        expected = set(case.get("expected_values", []))
        forbidden = set(case.get("forbidden_values", []))
        missing, leaked = expected - retrieved_values, forbidden & retrieved_values
        expected_abstain = case.get("expect_abstain")
        abstain_ok = expected_abstain is None or (not top) is expected_abstain
        latency_ms = (time.perf_counter() - retrieve_started) * 1000.0
        total_elapsed += (time.perf_counter() - started)
        rows.append({
            "latency_ms": latency_ms, "expected": len(expected), "missing": len(missing),
            "forbidden": len(forbidden), "leaks": len(leaked), "abstain_checked": expected_abstain is not None,
            "abstain_ok": abstain_ok, "passed": not missing and not leaked and abstain_ok,
        })
    count = len(rows)
    expected_count = sum(row["expected"] for row in rows)
    missing_count = sum(row["missing"] for row in rows)
    checked = [row for row in rows if row["abstain_checked"]]
    return {
        "method": "casefolded_token_overlap_v1",
        "cases": count,
        "case_passes": sum(row["passed"] for row in rows),
        "case_pass_rate": round(sum(row["passed"] for row in rows) / count, 6),
        "expected_values": expected_count,
        "missing_expected_values": missing_count,
        "expected_value_recall": None if not expected_count else round((expected_count - missing_count) / expected_count, 6),
        "forbidden_values": sum(row["forbidden"] for row in rows),
        "forbidden_value_leaks": sum(row["leaks"] for row in rows),
        "abstention_cases": len(checked),
        "abstention_accuracy": None if not checked else round(sum(row["abstain_ok"] for row in checked) / len(checked), 6),
        "latency_ms": {f"p{p}": percentile([row["latency_ms"] for row in rows], p / 100) for p in (50, 95, 99)},
        "throughput_cases_per_second": round(count / total_elapsed, 4) if total_elapsed else None,
        "note": "Fixture-level lexical baseline; lifecycle effects are simulated from labelled operations; not AGM SQLite FTS.",
    }


def summarize_repeated_runs(reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate concurrent-load statistics across independent full benchmark runs."""
    result: dict[str, Any] = {"count": len(reports), "runs": []}
    for index, report in enumerate(reports, 1):
        per_run: dict[str, Any] = {"run": index, "modes": {}}
        for mode in ("flat", "graph"):
            load = report.get("concurrent_retrieval", {}).get(mode)
            if load is not None:
                per_run["modes"][mode] = load
        result["runs"].append(per_run)
    repeated_modes: dict[str, Any] = {}
    for mode in ("flat", "graph"):
        loads = [report.get("concurrent_retrieval", {}).get(mode) for report in reports]
        loads = [load for load in loads if load is not None]
        if not loads:
            continue
        repeated_modes[mode] = {
            "runs": len(loads),
            "errors_total": sum(int(load["errors"]) for load in loads),
            "requests_total": sum(int(load["requests"]) for load in loads),
            "latency_percentiles_across_runs_ms": {
                key: {f"p{p}": percentile([float(load["latency_ms"][key]) for load in loads if load["latency_ms"][key] is not None], p / 100)
                      for p in (50, 95, 99)}
                for key in ("p50", "p95", "p99")
            },
            "throughput_requests_per_second_across_runs": {
                f"p{p}": percentile([float(load["throughput_requests_per_second"]) for load in loads if load["throughput_requests_per_second"] is not None], p / 100)
                for p in (50, 95, 99)
            },
        }
    result["summary"] = repeated_modes
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--include-case-details", action="store_true")
    parser.add_argument("--concurrency", type=int, default=0, help="enable concurrent retrieval load with this worker count")
    parser.add_argument("--concurrent-requests", type=int, default=100, help="requests per case and mode when concurrency is enabled")
    parser.add_argument("--repetitions", type=int, default=1, help="repeat the full benchmark this many times; reports per-run concurrent stats")
    parser.add_argument("--min-case-pass-rate", type=float, default=DEFAULT_MIN_CASE_PASS_RATE)
    parser.add_argument("--min-expected-recall", type=float, default=DEFAULT_MIN_EXPECTED_RECALL)
    parser.add_argument("--min-abstention-accuracy", type=float, default=DEFAULT_MIN_ABSTENTION_ACCURACY)
    args = parser.parse_args()
    try:
        if args.repetitions < 1 or args.repetitions > 50:
            raise ValueError("repetitions must be between 1 and 50")
        reports = [run_benchmark(
            args.benchmark, min_case_pass_rate=args.min_case_pass_rate,
            min_expected_recall=args.min_expected_recall,
            min_abstention_accuracy=args.min_abstention_accuracy,
            include_case_details=args.include_case_details, concurrency=args.concurrency,
            concurrent_requests=args.concurrent_requests,
        ) for _ in range(args.repetitions)]
        report = reports[0]
        if len(reports) > 1:
            report["repeated_concurrent_retrieval"] = summarize_repeated_runs(reports)
            report["repetitions"] = len(reports)
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
