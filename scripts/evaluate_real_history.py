#!/usr/bin/env python3
"""Evaluate a consented, de-identified JSONL benchmark against AGM retrieval.

Only aggregate metrics are emitted. Each case is evaluated in a fresh temporary
SQLite database. Initial writes and each requested operation are followed by a
close/reopen boundary; the final query runs after view rebuild/replay. Synthetic
fixtures are smoke tests only, not evidence of real-history quality.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agm import Ctx, MemoryStore, WriteItem

ALLOWED_TIERS = {"human_verified", "tool_verified", "trusted_agent", "untrusted"}
VALID_SCENARIOS = {
    "cross_session_recall", "tenant_isolation", "current_vs_stale",
    "deletion", "revocation", "expiry", "abstention", "relevance",
}
VALID_OPERATIONS = {"correction", "delete", "revoke_writer", "expire_before"}
DEFAULT_MIN_CASE_PASS_RATE = 0.95
DEFAULT_MIN_EXPECTED_RECALL = 0.95
DEFAULT_MIN_ABSTENTION_ACCURACY = 0.95
ZERO_TOLERANCE_SCENARIOS = {"tenant_isolation", "deletion", "revocation", "expiry"}


def _nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _validate_timestamp(value: Any, field: str) -> str:
    text = _nonempty_string(value, field)
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00" if text.endswith("Z") else text)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _ctx(data: dict[str, Any], prefix: str) -> Ctx:
    if not isinstance(data, dict):
        raise ValueError(f"{prefix} must be an object")
    tier = data.get("tier", "human_verified")
    if tier not in ALLOWED_TIERS:
        raise ValueError(f"{prefix}.tier has an unsupported value")
    return Ctx(
        tenant_id=_nonempty_string(data.get("tenant_id"), f"{prefix}.tenant_id"),
        writer_id=_nonempty_string(data.get("writer_id", "eval-writer"), f"{prefix}.writer_id"),
        tier=tier,
        project=_nonempty_string(data.get("project", "eval"), f"{prefix}.project"),
        agent=str(data.get("agent", "")),
    )


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    seen: set[str] = set()
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line_number} is not valid JSON") from exc
            if not isinstance(case, dict):
                raise ValueError(f"line {line_number} must be a JSON object")
            case_id = _nonempty_string(case.get("case_id"), f"line {line_number}.case_id")
            if case_id in seen:
                raise ValueError(f"duplicate case_id at line {line_number}")
            seen.add(case_id)
            if not isinstance(case.get("memories"), list):
                raise ValueError(f"case {case_id}: memories must be a list")
            query = case.get("query")
            if not isinstance(query, dict):
                raise ValueError(f"case {case_id}: query must be an object")
            _nonempty_string(query.get("text"), f"case {case_id}.query.text")
            _nonempty_string(query.get("tenant_id"), f"case {case_id}.query.tenant_id")
            _nonempty_string(query.get("project", "eval"), f"case {case_id}.query.project")
            if type(query.get("k", 5)) is not int or query.get("k", 5) < 1:
                raise ValueError(f"case {case_id}: query.k must be a positive integer")
            scenario = case.get("scenario", "cross_session_recall")
            if scenario not in VALID_SCENARIOS:
                raise ValueError(f"case {case_id}: unsupported scenario")
            for key in ("expected_values", "forbidden_values"):
                values = case.get(key, [])
                if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
                    raise ValueError(f"case {case_id}: {key} must be a list of strings")
            if "expect_abstain" in case and not isinstance(case["expect_abstain"], bool):
                raise ValueError(f"case {case_id}: expect_abstain must be boolean")
            if scenario in ZERO_TOLERANCE_SCENARIOS and not case.get("forbidden_values"):
                raise ValueError(f"case {case_id}: scenario {scenario} requires forbidden_values")
            for index, memory in enumerate(case["memories"]):
                if not isinstance(memory, dict) or not isinstance(memory.get("item"), dict):
                    raise ValueError(f"case {case_id}: memory {index} must contain an item object")
                _ctx(memory, f"case {case_id}.memories[{index}]")
                if "created_at" in memory:
                    _validate_timestamp(memory["created_at"], f"case {case_id}.memories[{index}].created_at")
            operations = case.get("operations", [])
            if not isinstance(operations, list):
                raise ValueError(f"case {case_id}: operations must be a list")
            operation_types = set()
            for op_index, operation in enumerate(operations):
                prefix = f"case {case_id}.operations[{op_index}]"
                if not isinstance(operation, dict):
                    raise ValueError(f"{prefix} must be an object")
                op_type = operation.get("type")
                if op_type not in VALID_OPERATIONS:
                    raise ValueError(f"{prefix}.type is unsupported")
                operation_types.add(op_type)
                _ctx(operation.get("context"), f"{prefix}.context")
                if op_type in {"correction", "delete"}:
                    target = operation.get("target_memory_index")
                    if type(target) is not int or not 0 <= target < len(case["memories"]):
                        raise ValueError(f"{prefix}.target_memory_index must reference a memory")
                if op_type == "correction":
                    if not isinstance(operation.get("item"), dict):
                        raise ValueError(f"{prefix}.item must be an object")
                    _nonempty_string(operation.get("reason"), f"{prefix}.reason")
                if op_type == "revoke_writer":
                    _nonempty_string(operation.get("writer_id"), f"{prefix}.writer_id")
                if op_type == "expire_before":
                    _validate_timestamp(operation.get("cutoff"), f"{prefix}.cutoff")
                    if "include_pinned" in operation and not isinstance(operation["include_pinned"], bool):
                        raise ValueError(f"{prefix}.include_pinned must be boolean")
            required_operation = {
                "current_vs_stale": "correction",
                "deletion": "delete",
                "revocation": "revoke_writer",
                "expiry": "expire_before",
            }.get(scenario)
            if required_operation and required_operation not in operation_types:
                raise ValueError(
                    f"case {case_id}: scenario {scenario} requires a {required_operation} operation"
                )
            if scenario == "expiry":
                expiry_operation = next(op for op in operations if op["type"] == "expire_before")
                cutoff_dt = datetime.fromisoformat(
                    _validate_timestamp(expiry_operation["cutoff"], f"case {case_id}.operations.cutoff").replace("Z", "+00:00")
                )
                due_non_pinned = []
                for memory in case["memories"]:
                    created_at = memory.get("created_at")
                    item_data = memory.get("item", {})
                    if not created_at or not isinstance(item_data, dict):
                        continue
                    created_dt = datetime.fromisoformat(
                        _validate_timestamp(created_at, f"case {case_id}.memories.created_at").replace("Z", "+00:00")
                    )
                    pinned = item_data.get("pin") is True
                    if created_dt <= cutoff_dt and (not pinned or expiry_operation.get("include_pinned", False)):
                        due_non_pinned.append(memory)
                if not due_non_pinned:
                    raise ValueError(
                        f"case {case_id}: expiry scenario requires a memory older than cutoff eligible for purge"
                    )
            cases.append(case)
    if not cases:
        raise ValueError("benchmark contains no cases")
    return cases


def evaluate_case(case: dict[str, Any], db_path: Path) -> dict[str, Any]:
    case_id = str(case["case_id"])
    scenario = case.get("scenario", "cross_session_recall")
    item_ids: list[str] = []

    # Stage 1: seed memories.
    with MemoryStore(str(db_path)) as store:
        for index, memory in enumerate(case["memories"]):
            ctx = _ctx(memory, f"case {case_id}.memories[{index}]")
            item = WriteItem.model_validate(memory["item"])
            result = store.write(ctx, item)
            if result.status == "quarantined":
                raise ValueError(f"case {case_id}: a benchmark memory was quarantined; review fixture quality")
            if not result.item_id:
                raise ValueError(f"case {case_id}: a benchmark write returned no item id")
            item_ids.append(result.item_id)
            if "created_at" in memory:
                store.conn.execute(
                    "UPDATE events SET created_at = ? WHERE id = "
                    "(SELECT event_id FROM nodes WHERE id = ?)",
                    (_validate_timestamp(memory["created_at"], f"case {case_id}.memories[{index}].created_at"), result.item_id),
                )
        if any("created_at" in memory for memory in case["memories"]):
            store.conn.commit()

    # Stage 2: execute actual lifecycle operations through MemoryStore methods.
    # Open/close around every operation so the next step cannot rely on the same connection.
    for op_index, operation in enumerate(case.get("operations", [])):
        prefix = f"case {case_id}.operations[{op_index}]"
        op_ctx = _ctx(operation["context"], f"{prefix}.context")
        with MemoryStore(str(db_path)) as store:
            op_type = operation["type"]
            if op_type == "correction":
                target_id = item_ids[operation["target_memory_index"]]
                write_item = WriteItem.model_validate(operation["item"])
                result = store.supersede(op_ctx, target_id, write_item, operation["reason"])
                if result.status != "superseded":
                    raise ValueError(f"{prefix}: correction did not supersede the target memory")
            elif op_type == "delete":
                target_id = item_ids[operation["target_memory_index"]]
                result = store.delete(op_ctx, target_id)
                if not result.deleted:
                    raise ValueError(f"{prefix}: requested memory deletion did not occur")
            elif op_type == "revoke_writer":
                result = store.revoke_writer(op_ctx, operation["writer_id"], since=operation.get("since"))
                if not result.revoked:
                    raise ValueError(f"{prefix}: writer revocation did not occur")
            elif op_type == "expire_before":
                result = store.expire_before(
                    op_ctx, operation["cutoff"],
                    include_pinned=operation.get("include_pinned", False),
                )
                if not result.expired_ids and not result.scrubbed_orphan_events:
                    raise ValueError(f"{prefix}: expiry operation did not purge any eligible memory")
            else:  # schema validation rejects this branch
                raise ValueError(f"{prefix}: unsupported operation")

    # Stage 3: reopen, rebuild views from the event log, then retrieve.
    query = case["query"]
    query_ctx = _ctx(query, f"case {case_id}.query")
    with MemoryStore(str(db_path)) as store:
        store.rebuild_views()
        result = store.retrieve(
            query_ctx,
            query["text"],
            entity=query.get("entity"),
            as_of=query.get("as_of"),
            k=query.get("k", 5),
            expand=query.get("expand", True),
            high_stakes=query.get("high_stakes", False),
        )
    retrieved_values = {str(node.value) for node in result.items if node.value is not None}
    expected = set(case.get("expected_values", []))
    forbidden = set(case.get("forbidden_values", []))
    missing = expected - retrieved_values
    leaked = forbidden & retrieved_values
    expected_abstain = case.get("expect_abstain")
    abstain_checked = expected_abstain is not None
    abstain_ok = not abstain_checked or result.abstain is expected_abstain
    zero_tolerance_violation = scenario in ZERO_TOLERANCE_SCENARIOS and bool(leaked)
    return {
        "case_id": case_id,
        "scenario": scenario,
        "expected_count": len(expected),
        "missing_count": len(missing),
        "forbidden_count": len(forbidden),
        "leak_count": len(leaked),
        "abstain_checked": abstain_checked,
        "abstain_ok": abstain_ok,
        "zero_tolerance_violation": zero_tolerance_violation,
        "pass": not missing and not leaked and abstain_ok,
    }


def evaluate(
    path: Path,
    *,
    min_case_pass_rate: float = DEFAULT_MIN_CASE_PASS_RATE,
    min_expected_recall: float = DEFAULT_MIN_EXPECTED_RECALL,
    min_abstention_accuracy: float = DEFAULT_MIN_ABSTENTION_ACCURACY,
) -> dict[str, Any]:
    for name, value in (
        ("min_case_pass_rate", min_case_pass_rate),
        ("min_expected_recall", min_expected_recall),
        ("min_abstention_accuracy", min_abstention_accuracy),
    ):
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be between 0 and 1")
    cases = load_cases(path)
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="agm-m1-eval-") as tmp:
        for index, case in enumerate(cases):
            results.append(evaluate_case(case, Path(tmp) / f"case-{index}.db"))
    total = len(results)
    expected_total = sum(r["expected_count"] for r in results)
    missing_total = sum(r["missing_count"] for r in results)
    forbidden_total = sum(r["forbidden_count"] for r in results)
    leak_total = sum(r["leak_count"] for r in results)
    abstain_checked = [r for r in results if r["abstain_checked"]]
    abstain_pass = sum(bool(r["abstain_ok"]) for r in abstain_checked)
    scenario_counts: dict[str, dict[str, int]] = {}
    for row in results:
        slot = scenario_counts.setdefault(row["scenario"], {"cases": 0, "passes": 0, "leaks": 0})
        slot["cases"] += 1
        slot["passes"] += int(bool(row["pass"]))
        slot["leaks"] += int(row["leak_count"])
    case_pass_rate = sum(bool(r["pass"]) for r in results) / total
    recall = None if expected_total == 0 else (expected_total - missing_total) / expected_total
    abstention_accuracy = None if not abstain_checked else abstain_pass / len(abstain_checked)
    zero_tolerance_failures = sum(bool(r["zero_tolerance_violation"]) for r in results)
    threshold_failures = []
    if case_pass_rate < min_case_pass_rate:
        threshold_failures.append("case_pass_rate")
    if recall is not None and recall < min_expected_recall:
        threshold_failures.append("expected_value_recall")
    if abstention_accuracy is not None and abstention_accuracy < min_abstention_accuracy:
        threshold_failures.append("abstention_accuracy")
    if zero_tolerance_failures:
        threshold_failures.append("zero_tolerance_scenario_leak")
    return {
        "benchmark_file": path.name,
        "cases": total,
        "case_passes": sum(bool(r["pass"]) for r in results),
        "case_pass_rate": case_pass_rate,
        "expected_value_recall": recall,
        "expected_values": expected_total,
        "missing_expected_values": missing_total,
        "forbidden_values": forbidden_total,
        "forbidden_value_leaks": leak_total,
        "zero_tolerance_failures": zero_tolerance_failures,
        "abstention_cases": len(abstain_checked),
        "abstention_accuracy": abstention_accuracy,
        "scenario_coverage": scenario_counts,
        "thresholds": {
            "min_case_pass_rate": min_case_pass_rate,
            "min_expected_recall": min_expected_recall,
            "min_abstention_accuracy": min_abstention_accuracy,
        },
        "threshold_failures": threshold_failures,
        "release_blocking_violations": leak_total + zero_tolerance_failures,
        "all_cases_pass": all(bool(r["pass"]) for r in results),
        "release_gate_pass": not threshold_failures and all(bool(r["pass"]) for r in results),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", type=Path, help="JSONL benchmark; keep private datasets out of Git")
    parser.add_argument("--output", type=Path, help="optional path for aggregate JSON report")
    parser.add_argument("--min-case-pass-rate", type=float, default=DEFAULT_MIN_CASE_PASS_RATE)
    parser.add_argument("--min-expected-recall", type=float, default=DEFAULT_MIN_EXPECTED_RECALL)
    parser.add_argument("--min-abstention-accuracy", type=float, default=DEFAULT_MIN_ABSTENTION_ACCURACY)
    args = parser.parse_args()
    try:
        report = evaluate(
            args.benchmark,
            min_case_pass_rate=args.min_case_pass_rate,
            min_expected_recall=args.min_expected_recall,
            min_abstention_accuracy=args.min_abstention_accuracy,
        )
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    encoded = json.dumps(report, indent=2, sort_keys=True)
    print(encoded)
    if args.output:
        args.output.write_text(encoded + "\n", encoding="utf-8")
    return 0 if report["release_gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
