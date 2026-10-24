from __future__ import annotations

import json

import pytest

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


def _write(path, case):
    path.write_text(json.dumps(case) + "\n", encoding="utf-8")
    return path


def test_evaluator_reports_success_for_recalled_value(tmp_path):
    report = evaluate(_write(tmp_path / "benchmark.jsonl", _case()))
    assert report["cases"] == 1
    assert report["all_cases_pass"] is True
    assert report["expected_value_recall"] == 1.0
    assert report["release_blocking_violations"] == 0


def test_evaluator_detects_missing_expected_value(tmp_path, monkeypatch):
    import scripts.evaluate_real_history as evaluator

    original = evaluator.evaluate_case

    def broken(case, db_path):
        result = original(case, db_path)
        result["missing_count"] = result["expected_count"]
        result["pass"] = False
        return result

    monkeypatch.setattr(evaluator, "evaluate_case", broken)
    report = evaluator.evaluate(_write(tmp_path / "missing.jsonl", _case()))
    assert report["missing_expected_values"] == 1
    assert report["expected_value_recall"] == 0.0
    assert report["all_cases_pass"] is False


def test_evaluator_detects_forbidden_value_leak_and_blocks_release(tmp_path, monkeypatch):
    import scripts.evaluate_real_history as evaluator

    original = evaluator.evaluate_case

    def leaking(case, db_path):
        result = original(case, db_path)
        result["leak_count"] = 1
        result["pass"] = False
        return result

    case = _case()
    case["forbidden_values"] = ["tenant-b-marker"]
    monkeypatch.setattr(evaluator, "evaluate_case", leaking)
    report = evaluator.evaluate(_write(tmp_path / "leak.jsonl", case))
    assert report["forbidden_value_leaks"] == 1
    assert report["release_blocking_violations"] == 1
    assert report["all_cases_pass"] is False


def test_evaluator_detects_wrong_abstention(tmp_path, monkeypatch):
    import scripts.evaluate_real_history as evaluator

    original = evaluator.evaluate_case

    def wrong_abstention(case, db_path):
        result = original(case, db_path)
        result["abstain_checked"] = True
        result["abstain_ok"] = False
        result["pass"] = False
        return result

    case = _case()
    case["expect_abstain"] = True
    monkeypatch.setattr(evaluator, "evaluate_case", wrong_abstention)
    report = evaluator.evaluate(_write(tmp_path / "abstention.jsonl", case))
    assert report["abstention_accuracy"] == 0.0
    assert report["all_cases_pass"] is False


def test_evaluator_tenant_isolation_fixture_does_not_leak(tmp_path):
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
    report = evaluate(_write(tmp_path / "tenant.jsonl", case))
    assert report["release_blocking_violations"] == 0
    assert report["all_cases_pass"] is True


@pytest.mark.parametrize(
    "payload, message",
    [
        ('{"case_id":"a","memories":[],"query":{"text":"q","tenant_id":"t"},"expect_abstain":"yes"}',
         "expect_abstain must be boolean"),
        ('{"case_id":"a","memories":[],"query":{"text":"q","tenant_id":"t"},"expected_values":"x"}',
         "expected_values must be a list"),
        ("[]", "must be a JSON object"),
    ],
)
def test_load_cases_rejects_malformed_rows(tmp_path, payload, message):
    path = tmp_path / "bad.jsonl"
    path.write_text(payload + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_cases(path)


def test_load_cases_rejects_duplicate_case_ids(tmp_path):
    path = tmp_path / "duplicate.jsonl"
    row = json.dumps(_case())
    path.write_text(row + "\n" + row + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate case_id"):
        load_cases(path)
