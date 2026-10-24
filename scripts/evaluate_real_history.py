#!/usr/bin/env python3
"""Evaluate AGM retrieval against a consented, de-identified JSONL benchmark.

This tool stores each case in a temporary SQLite database, closes/reopens the
store before querying, and prints aggregate metrics only. It never prints case
content or retrieved memory text.

Input schema (one JSON object per line):
{
  "case_id": "opaque-case-001",
  "memories": [
    {
      "tenant_id": "pseudonym-tenant-1",
      "writer_id": "eval-writer",
      "tier": "human_verified",
      "project": "eval",
      "item": {
        "kind": "fact",
        "entity": "service-a",
        "attribute": "owner",
        "value": "team-blue",
        "text": "service-a is owned by team-blue"
      }
    }
  ],
  "query": {
    "tenant_id": "pseudonym-tenant-1",
    "writer_id": "eval-reader",
    "tier": "human_verified",
    "project": "eval",
    "text": "Who owns service-a?",
    "entity": "service-a",
    "k": 5
  },
  "expected_values": ["team-blue"],
  "forbidden_values": [],
  "expect_abstain": false
}

`expected_values` means every listed value must appear in retrieved items.
`forbidden_values` means none may appear. For stale-value tests, put the old
value in `forbidden_values`. For tenant-isolation tests, put the other tenant's
distinctive value in `forbidden_values`.

Only use explicitly consented, de-identified histories. Keep raw histories and
identity maps outside the repository. The evaluator outputs aggregate counts
and rates, not per-case content.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any

from agm import Ctx, MemoryStore, WriteItem

ALLOWED_TIERS = {"human_verified", "tool_verified", "trusted_agent", "untrusted"}


def _nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _ctx(data: dict[str, Any], prefix: str) -> Ctx:
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
            for key in ("expected_values", "forbidden_values"):
                values = case.get(key, [])
                if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
                    raise ValueError(f"case {case_id}: {key} must be a list of strings")
            if "expect_abstain" in case and not isinstance(case["expect_abstain"], bool):
                raise ValueError(f"case {case_id}: expect_abstain must be boolean")
            cases.append(case)
    if not cases:
        raise ValueError("benchmark contains no cases")
    return cases


def evaluate_case(case: dict[str, Any], db_path: Path) -> dict[str, Any]:
    case_id = str(case["case_id"])
    with MemoryStore(str(db_path)) as store:
        for index, memory in enumerate(case["memories"]):
            if not isinstance(memory, dict) or not isinstance(memory.get("item"), dict):
                raise ValueError(f"case {case_id}: memory {index} must contain an item object")
            ctx = _ctx(memory, f"case {case_id}.memories[{index}]")
            item = WriteItem.model_validate(memory["item"])
            result = store.write(ctx, item)
            if result.status == "quarantined":
                raise ValueError(f"case {case_id}: a benchmark memory was quarantined; review the de-identified fixture")
    # Reopen to test durable cross-session recall rather than same-instance cache behavior.
    query = case["query"]
    query_ctx = _ctx(query, f"case {case_id}.query")
    with MemoryStore(str(db_path)) as store:
        result = store.retrieve(
            query_ctx,
            query["text"],
            entity=query.get("entity"),
            k=int(query.get("k", 5)),
            expand=bool(query.get("expand", True)),
        )
    retrieved_values = {node.value for node in result.items if node.value is not None}
    expected = set(case.get("expected_values", []))
    forbidden = set(case.get("forbidden_values", []))
    missing = expected - retrieved_values
    leaked = forbidden & retrieved_values
    expected_abstain = case.get("expect_abstain")
    abstain_ok = expected_abstain is None or result.abstain is expected_abstain
    return {
        "case_id": case_id,
        "expected_count": len(expected),
        "missing_count": len(missing),
        "forbidden_count": len(forbidden),
        "leak_count": len(leaked),
        "abstain_checked": expected_abstain is not None,
        "abstain_ok": abstain_ok,
        "pass": not missing and not leaked and abstain_ok,
    }


def evaluate(path: Path) -> dict[str, Any]:
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
    return {
        "benchmark_file": path.name,
        "cases": total,
        "case_passes": sum(bool(r["pass"]) for r in results),
        "case_pass_rate": sum(bool(r["pass"]) for r in results) / total,
        "expected_value_recall": None if expected_total == 0 else (expected_total - missing_total) / expected_total,
        "expected_values": expected_total,
        "missing_expected_values": missing_total,
        "forbidden_values": forbidden_total,
        "forbidden_value_leaks": leak_total,
        "abstention_cases": len(abstain_checked),
        "abstention_accuracy": None if not abstain_checked else abstain_pass / len(abstain_checked),
        "release_blocking_violations": leak_total,
        "all_cases_pass": all(bool(r["pass"]) for r in results),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", type=Path, help="JSONL benchmark; keep private datasets out of Git")
    parser.add_argument("--output", type=Path, help="optional path for aggregate JSON report")
    args = parser.parse_args()
    try:
        report = evaluate(args.benchmark)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    encoded = json.dumps(report, indent=2, sort_keys=True)
    print(encoded)
    if args.output:
        args.output.write_text(encoded + "\n", encoding="utf-8")
    return 0 if report["all_cases_pass"] and report["release_blocking_violations"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
