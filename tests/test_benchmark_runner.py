from __future__ import annotations

import json

from eval.benchmark_runner import run_benchmark


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
