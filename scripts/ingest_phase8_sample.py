#!/usr/bin/env python3
"""Idempotently ingest the small, mixed-context Phase 8 sample corpus."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from agm import Ctx, MemoryStore, WriteItem
from agm.events import utc_now
from agm.guard import guarded_write
from agm.diagnostics import append_jsonl

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "examples" / "phase8_sample_memory.jsonl"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="./phase8-memory.db", help="SQLite database path")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="JSONL content file")
    parser.add_argument("--tenant", default="phase8-demo")
    parser.add_argument("--project", default="phase8")
    parser.add_argument("--writer", default="phase8-sample-loader")
    parser.add_argument("--log", default="logs/phase8-ingest.jsonl")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    records = []
    for line_number, raw in enumerate(input_path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            parser.error(f"{input_path}:{line_number}: invalid JSON: {exc}")
        scenario = str(record.pop("_scenario", "unspecified"))
        try:
            item = WriteItem.model_validate(record)
        except Exception as exc:
            parser.error(f"{input_path}:{line_number}: invalid WriteItem: {exc}")
        records.append((line_number, scenario, item))

    ctx = Ctx(tenant_id=args.tenant, project=args.project, writer_id=args.writer, tier="human_verified")
    print(f"Corpus: {input_path} ({len(records)} records)")
    print(f"Target: {args.db} | tenant={args.tenant} | project={args.project}")
    if args.dry_run:
        print("Dry run: no data was written.")
        for line_number, scenario, item in records:
            payload = item.model_dump(mode="json")
            fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:12]
            print(f"  line={line_number:02d} scenario={scenario:20s} kind={item.kind:9s} entity={item.entity or '-':20s} sha={fingerprint}")
        return 0

    counts: Counter[str] = Counter()
    log_path = Path(args.log)
    with MemoryStore(args.db) as store:
        for line_number, scenario, item in records:
            result = guarded_write(store, ctx, item)
            counts[result.status] += 1
            payload = item.model_dump_json()
            append_jsonl(log_path, {
                "timestamp": utc_now(),
                "event": "memory_ingest",
                "line": line_number,
                "scenario": scenario,
                "tenant": ctx.tenant_id,
                "project": ctx.project,
                "kind": item.kind,
                "entity": item.entity,
                "attribute": item.attribute,
                "idempotency_key": item.idempotency_key,
                "input_sha256": hashlib.sha256(payload.encode()).hexdigest(),
                "status": result.status,
                "item_id": result.item_id,
                "superseded_id": result.superseded_id,
                "redactions": result.redactions,
                "warnings": result.warnings,
            })
        totals = {
            "timestamp": utc_now(), "event": "memory_ingest_summary",
            "db": args.db, "input": str(input_path), "tenant": ctx.tenant_id,
            "project": ctx.project, "records": len(records), "statuses": dict(counts),
            "log_path": str(log_path),
        }
        append_jsonl(log_path, totals)
        print(json.dumps(totals, indent=2))
        node_count = int(store.conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE tenant = ? AND project = ?", (ctx.tenant_id, ctx.project)
        ).fetchone()[0])
        event_count = int(store.conn.execute(
            "SELECT COUNT(*) FROM events WHERE tenant = ?", (ctx.tenant_id,)
        ).fetchone()[0])
        print(f"Ingested. Scoped nodes={node_count}; tenant events={event_count}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
