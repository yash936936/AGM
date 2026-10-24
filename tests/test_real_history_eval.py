from __future__ import annotations

import json

from scripts.evaluate_real_history import evaluate, load_cases


def _case(case_id="case-1"):
    return {
        "case_id": case_id,
        "memories": [
            {
                "tenant_id": "tenant-a",
                "writer_id": "writer-a",
                "tier": "human_verified",
                "project": "eval",
                "item": {
                    "kind": "fact",
                    "entity": "service-a",
                    "attribute": "owner",
                    "value": "team-blue",
                    "text": "service-a is owned by team-blue",
                },
            }
        ],
        "query": {
            "tenant_id": "tenant-a",
            "writer_id": "reader-a",
            "tier": "human_verified",
            "project": "eval",
            "text": "Who owns service-a?",
            "entity": "service-a",
            "k": 5,
        },
        "expected_values": ["team-blue"],
        "forbidden_values": [],
    }


def test_evaluator_reports_success_for_recalled_value(tmp_path):
    path = tmp_path / "benchmark.jsonl"
    path.write_text(json.dumps(_case()) + "\n", encoding="utf-8")
    report = evaluate(path)
    assert report["cases"] == 1
    assert report["all_cases_pass"] is True
    assert report["expected_value_recall"] == 1.0
    assert report["release_blocking_violations"] == 0


def test_evaluator_detects_tenant_leak_as_forbidden_value(tmp_path):
    case = _case()
    case["memories"].append({
        "tenant_id": "tenant-b",
        "writer_id": "writer-b",
        "tier": "human_verified",
        "project": "eval",
        "item": {
            "kind": "fact",
            "entity": "service-a",
            "attribute": "secret_marker",
            "value": "tenant-b-marker",
            "text": "Synthetic tenant-b marker for isolation testing",
        },
    })
    case["forbidden_values"] = ["tenant-b-marker"]
    path = tmp_path / "benchmark.jsonl"
    path.write_text(json.dumps(case) + "\n", encoding="utf-8")
    report = evaluate(path)
    # The query is tenant-a, so a properly isolated store must not return tenant-b data.
    assert report["release_blocking_violations"] == 0
    assert report["all_cases_pass"] is True


def test_load_cases_rejects_duplicate_case_ids(tmp_path):
    path = tmp_path / "benchmark.jsonl"
    item = json.dumps(_case())
    path.write_text(item + "\n" + item + "\n", encoding="utf-8")
    try:
        load_cases(path)
    except ValueError as exc:
        assert "duplicate case_id" in str(exc)
    else:
        raise AssertionError("duplicate case IDs must be rejected")
