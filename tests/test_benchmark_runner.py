from __future__ import annotations

import json
import os

from eval.benchmark_runner import evaluate_keyword_baseline, run_benchmark, summarize_repeated_runs


def _case(case_id="case-1"):
    return {
        "case_id": case_id,
        "scenario": "cross_session_recall",
        "memories": [{
            "tenant_id": "tenant-a", "writer_id": "writer-a", "tier": "human_verified",
            "project": "eval", "item": {
                "kind": "fact", "entity": "service-a", "attribute": "owner",
                "value": "team-blue", "text": "service-a is owned by team-blue",
            },
        }],
        "query": {
            "tenant_id": "tenant-a", "writer_id": "reader-a", "tier": "human_verified",
            "project": "eval", "text": "Who owns service-a?", "entity": "service-a", "k": 5,
        },
        "expected_values": ["team-blue"], "forbidden_values": [],
    }


def test_paired_benchmark_reports_modes_metrics_and_omits_case_ids(tmp_path):
    path = tmp_path / "cases.jsonl"
    path.write_text(json.dumps(_case("private-case-id")) + "\n", encoding="utf-8")
    report = run_benchmark(path, include_case_details=True)
    assert report["protocol"] == "paired_flat_vs_graph_v3"
    assert report["process_peak_rss_bytes"] is None or report["process_peak_rss_bytes"] > 0
    if os.name == "nt":
        assert report["process_peak_rss_bytes"] is not None
    assert "benchmark_file" not in report
    assert report["cases"] == 1
    for mode in ("flat", "graph"):
        assert report["modes"][mode]["expected_value_recall"] == 1.0
        assert report["modes"][mode]["retrieval_latency_ms"]["p50"] is not None
        assert report["modes"][mode]["end_to_end_case_latency_ms"]["p95"] is not None
        assert report["modes"][mode]["operation_latency_ms"]["write"]["count"] == 1
        assert report["modes"][mode]["operation_latency_ms"]["rebuild_replay"]["p50"] is not None
        assert report["modes"][mode]["release_gate_pass"] is True
    assert "private-case-id" not in json.dumps(report)
    assert report["case_details"]["flat"][0]["case_index"] == 1
    assert report["keyword_baseline"]["method"] == "casefolded_token_overlap_v1"
    assert report["keyword_baseline"]["expected_value_recall"] == 1.0



def test_concurrent_retrieval_reports_latency_throughput_and_errors(tmp_path):
    path = tmp_path / "private-dataset-name.jsonl"
    path.write_text(json.dumps(_case()) + "\n", encoding="utf-8")
    report = run_benchmark(path, concurrency=2, concurrent_requests=3)
    assert "private-dataset-name" not in json.dumps(report)
    for mode in ("flat", "graph"):
        load = report["concurrent_retrieval"][mode]
        assert load["workers"] == 2
        assert load["requests"] == 3
        assert load["errors"] == 0
        assert load["latency_ms"]["p50"] is not None
        assert load["throughput_requests_per_second"] > 0



def test_keyword_baseline_simulates_delete_and_reports_forbidden_leak(tmp_path):
    case = _case("delete-case")
    case["scenario"] = "deletion"
    case["operations"] = [{
        "type": "delete",
        "context": {"tenant_id": "tenant-a", "writer_id": "writer-a", "tier": "human_verified", "project": "eval"},
        "target_memory_index": 0,
    }]
    case["expected_values"] = []
    case["forbidden_values"] = ["team-blue"]
    case["expect_abstain"] = True
    baseline = evaluate_keyword_baseline([case])
    assert baseline["forbidden_value_leaks"] == 0
    assert baseline["abstention_accuracy"] == 1.0


def test_repeated_run_summary_preserves_each_run_and_aggregates_percentiles():
    reports = [
        {"concurrent_retrieval": {
            "flat": {"errors": 0, "requests": 10, "latency_ms": {"p50": 2.0, "p95": 4.0, "p99": 5.0}, "throughput_requests_per_second": 20.0},
            "graph": {"errors": 1, "requests": 10, "latency_ms": {"p50": 3.0, "p95": 6.0, "p99": 7.0}, "throughput_requests_per_second": 15.0},
        }},
        {"concurrent_retrieval": {
            "flat": {"errors": 0, "requests": 10, "latency_ms": {"p50": 4.0, "p95": 8.0, "p99": 9.0}, "throughput_requests_per_second": 10.0},
            "graph": {"errors": 0, "requests": 10, "latency_ms": {"p50": 5.0, "p95": 7.0, "p99": 8.0}, "throughput_requests_per_second": 12.0},
        }},
    ]
    summary = summarize_repeated_runs(reports)
    assert summary["count"] == 2
    assert summary["summary"]["flat"]["errors_total"] == 0
    assert summary["summary"]["graph"]["errors_total"] == 1
    assert summary["summary"]["flat"]["latency_percentiles_across_runs_ms"]["p50"]["p50"] == 3.0
    assert len(summary["runs"]) == 2



def test_frozen_synthetic_acceptance_suite_covers_required_scenarios():
    from pathlib import Path
    from scripts.evaluate_real_history import load_cases

    path = Path("examples/benchmark_acceptance.synthetic.jsonl")
    cases = load_cases(path)
    assert len(cases) == 10
    assert {"abstention", "current_vs_stale", "deletion", "revocation", "expiry", "tenant_isolation"} <= {
        case["scenario"] for case in cases
    }
    assert len({case["case_id"] for case in cases}) == len(cases)
