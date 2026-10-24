from __future__ import annotations

import json

import pytest

from scripts.evaluate_real_history import evaluate, load_cases


def _ctx(tenant="tenant-a", writer="writer-a"):
    return {
        "tenant_id": tenant,
        "writer_id": writer,
        "tier": "human_verified",
        "project": "eval",
    }


def _memory(writer="writer-a", entity="service-a", attribute="owner", value="team-blue",
            text="service-a is owned by team-blue"):
    return {
        **_ctx(writer=writer),
        "item": {
            "kind": "fact",
            "entity": entity,
            "attribute": attribute,
            "value": value,
            "text": text,
        },
    }


def _case(case_id="case-1"):
    return {
        "case_id": case_id,
        "scenario": "cross_session_recall",
        "memories": [_memory()],
        "query": {
            **_ctx(writer="reader-a"),
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
    assert report["release_gate_pass"] is True
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
    assert report["release_gate_pass"] is False


def test_evaluator_detects_forbidden_value_leak_and_blocks_release(tmp_path, monkeypatch):
    import scripts.evaluate_real_history as evaluator

    original = evaluator.evaluate_case

    def leaking(case, db_path):
        result = original(case, db_path)
        result["leak_count"] = 1
        result["pass"] = False
        result["zero_tolerance_violation"] = True
        return result

    case = _case()
    case["scenario"] = "tenant_isolation"
    case["forbidden_values"] = ["tenant-b-marker"]
    monkeypatch.setattr(evaluator, "evaluate_case", leaking)
    report = evaluator.evaluate(_write(tmp_path / "leak.jsonl", case))
    assert report["forbidden_value_leaks"] == 1
    assert report["zero_tolerance_failures"] == 1
    assert report["release_blocking_violations"] == 2
    assert report["all_cases_pass"] is False
    assert report["release_gate_pass"] is False


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
    assert report["release_gate_pass"] is False


def test_evaluator_tenant_isolation_fixture_does_not_leak(tmp_path):
    case = _case()
    case["scenario"] = "tenant_isolation"
    case["memories"].append({
        **_ctx(tenant="tenant-b", writer="writer-b"),
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
    assert report["scenario_coverage"]["tenant_isolation"]["cases"] == 1


def test_evaluator_executes_supersede_and_replay_for_stale_value_case(tmp_path):
    case = _case("correction-case")
    case["scenario"] = "current_vs_stale"
    case["memories"] = [_memory(value="team-red", text="service-a is owned by team-red")]
    case["operations"] = [{
        "type": "correction",
        "context": _ctx(),
        "target_memory_index": 0,
        "reason": "synthetic explicit correction",
        "item": {
            "kind": "fact",
            "entity": "service-a",
            "attribute": "owner",
            "value": "team-blue",
            "text": "service-a is owned by team-blue",
        },
    }]
    case["expected_values"] = ["team-blue"]
    case["forbidden_values"] = ["team-red"]
    report = evaluate(_write(tmp_path / "correction.jsonl", case))
    assert report["all_cases_pass"] is True
    assert report["expected_value_recall"] == 1.0
    assert report["forbidden_value_leaks"] == 0
    assert report["release_gate_pass"] is True


def test_evaluator_executes_hard_delete_then_rebuilds_views(tmp_path):
    case = _case("delete-case")
    case["scenario"] = "deletion"
    case["memories"] = [
        _memory(entity="service-a", attribute="obsolete_marker", value="delete-marker-7f31",
                text="service-a obsolete marker delete-marker-7f31"),
    ]
    case["operations"] = [{
        "type": "delete",
        "context": _ctx(writer="admin-a"),
        "target_memory_index": 0,
    }]
    case["query"] = {
        **_ctx(writer="reader-a"),
        "text": "service-a obsolete marker delete-marker-7f31",
        "entity": "service-a",
        "k": 5,
    }
    case["expected_values"] = []
    case["forbidden_values"] = ["delete-marker-7f31"]
    case["expect_abstain"] = True
    report = evaluate(_write(tmp_path / "delete.jsonl", case))
    assert report["all_cases_pass"] is True
    assert report["forbidden_value_leaks"] == 0
    assert report["zero_tolerance_failures"] == 0
    assert report["release_gate_pass"] is True


def test_evaluator_executes_writer_revocation_then_rebuilds_views(tmp_path):
    case = _case("revoke-case")
    case["scenario"] = "revocation"
    case["memories"] = [
        _memory(writer="writer-b", entity="service-a", attribute="revocation_marker",
                value="revoke-marker-9a62", text="service-a revocation marker revoke-marker-9a62"),
    ]
    case["operations"] = [{
        "type": "revoke_writer",
        "context": _ctx(writer="admin-a"),
        "writer_id": "writer-b",
    }]
    case["query"] = {
        **_ctx(writer="reader-a"),
        "text": "service-a revocation marker revoke-marker-9a62",
        "entity": "service-a",
        "k": 5,
    }
    case["expected_values"] = []
    case["forbidden_values"] = ["revoke-marker-9a62"]
    case["expect_abstain"] = True
    report = evaluate(_write(tmp_path / "revoke.jsonl", case))
    assert report["all_cases_pass"] is True
    assert report["forbidden_value_leaks"] == 0
    assert report["zero_tolerance_failures"] == 0
    assert report["release_gate_pass"] is True


def test_zero_tolerance_scenarios_require_forbidden_sentinels(tmp_path):
    case = _case()
    case["scenario"] = "deletion"
    case["forbidden_values"] = []
    path = _write(tmp_path / "invalid.jsonl", case)
    with pytest.raises(ValueError, match="requires forbidden_values"):
        load_cases(path)


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



@pytest.mark.parametrize(
    "scenario, forbidden, expected_message",
    [
        ("current_vs_stale", [], "requires a correction operation"),
        ("deletion", ["delete-marker"], "requires a delete operation"),
        ("revocation", ["revoke-marker"], "requires a revoke_writer operation"),
    ],
)
def test_mutation_scenarios_require_matching_store_operation(
    tmp_path, scenario, forbidden, expected_message
):
    case = _case()
    case["scenario"] = scenario
    case["forbidden_values"] = forbidden
    path = _write(tmp_path / f"{scenario}.jsonl", case)
    with pytest.raises(ValueError, match=expected_message):
        load_cases(path)
