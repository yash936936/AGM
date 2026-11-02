#!/usr/bin/env python3
"""Turn a small hand-written JSON file into evaluator cases (JSONL) for scripts/evaluate_real_history.py.

Run this on the machine that holds the data. Output stays local; only the aggregate report is ever shared.
Supports four case types: recall, stale (correction), deletion, abstention. Anything else (tenant isolation,
revocation, expiry) can be authored directly in the evaluator's JSONL schema.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.evaluate_real_history import load_cases  # noqa: E402


def _fact(m: dict[str, Any]) -> dict[str, Any]:
    item = {"kind": "fact", "entity": m["entity"], "attribute": m["attribute"], "value": m["value"],
            "text": m.get("text") or f"{m['entity']} {m['attribute']} is {m['value']}."}
    for key in ("valid_from", "confidence"):
        if key in m:
            item[key] = m[key]
    return item


def build(doc: dict[str, Any]) -> list[dict[str, Any]]:
    tenant, project = doc.get("tenant", "local-eval"), doc.get("project", "eval")
    writer = {"tenant_id": tenant, "writer_id": "eval-writer", "tier": "human_verified", "project": project}
    reader = {"tenant_id": tenant, "writer_id": "eval-reader", "tier": "human_verified", "project": project}
    cases = []
    for raw in doc["cases"]:
        memories = [{**writer, "item": _fact(m)} for m in raw.get("memories", [])]
        query: dict[str, Any] = {**reader, "text": raw["query"], "k": raw.get("k", 5)}
        if raw.get("entity"):
            query["entity"] = raw["entity"]
        case: dict[str, Any] = {"case_id": raw["id"], "memories": memories, "query": query,
                                "expected_values": list(raw.get("expected", [])),
                                "forbidden_values": list(raw.get("forbidden", []))}
        operations = []
        if "correction" in raw:
            c = raw["correction"]
            target = int(c.get("target", 0))
            operations.append({"type": "correction", "context": writer, "target_memory_index": target,
                               "item": _fact(c["item"]), "reason": c.get("reason", "corrected")})
            case["scenario"] = "current_vs_stale"
            if not case["forbidden_values"]:
                case["forbidden_values"] = [raw["memories"][target]["value"]]
            if not case["expected_values"]:
                case["expected_values"] = [c["item"]["value"]]
        elif "delete" in raw:
            target = int(raw["delete"])
            operations.append({"type": "delete", "context": writer, "target_memory_index": target})
            case["scenario"] = "deletion"
            if not case["forbidden_values"]:
                case["forbidden_values"] = [raw["memories"][target]["value"]]
        elif raw.get("abstain"):
            case["scenario"] = "abstention"
        else:
            case["scenario"] = "cross_session_recall"
        if "abstain" in raw:
            case["expect_abstain"] = bool(raw["abstain"])
        elif case["scenario"] == "cross_session_recall":
            case["expect_abstain"] = False
        if operations:
            case["operations"] = operations
        cases.append(case)
    return cases


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("authoring_json", type=Path); ap.add_argument("output_jsonl", type=Path)
    args = ap.parse_args()
    try:
        cases = build(json.loads(args.authoring_json.read_text(encoding="utf-8")))
        args.output_jsonl.write_text("".join(json.dumps(c, sort_keys=True) + "\n" for c in cases), encoding="utf-8")
        load_cases(args.output_jsonl)  # validate with the evaluator's own schema checks
    except (OSError, KeyError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {len(cases)} validated case(s) to {args.output_jsonl}. Keep it local; do not commit or share it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
