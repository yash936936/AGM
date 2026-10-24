#!/usr/bin/env python3
"""Compare Phase 8 flat/graph agent JSONL traces without exposing raw memory content."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Log file not found: {path}")

    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSONL at {path}:{line_no}: {exc}"
            ) from exc
        if isinstance(value, dict):
            rows.append(value)
    return rows


def latest(
    rows: list[dict[str, Any]],
    event: str,
    query_hash: str,
    mode: str,
) -> dict[str, Any] | None:
    matches = [
        row for row in rows
        if row.get("event") == event
        and row.get("query_sha256") == query_hash
        and row.get("mode") == mode
    ]
    return matches[-1] if matches else None


def summarize(
    label: str,
    path: Path,
    rows: list[dict[str, Any]],
    query_hash: str,
    show_content: bool,
) -> dict[str, Any]:
    retrieval = latest(rows, "retrieval", query_hash, label)
    answer = latest(rows, "agent_answer_completed", query_hash, label)

    if retrieval is None:
        raise ValueError(
            f"No matching retrieval event for mode={label}, "
            f"query hash={query_hash[:12]} in {path}"
        )

    sql = retrieval.get("sql_profile") or {}
    items = retrieval.get("items") or []

    owner_hits = [
        item for item in items
        if str(item.get("entity") or "").casefold() == "billing-api"
        and str(item.get("attribute") or "").casefold() == "owner"
    ]

    print(f"\n[{label.upper()}] {path}")
    print(f"  trace_id: {retrieval.get('trace_id', '<missing>')}")
    print(
        f"  elapsed_ms: {retrieval.get('elapsed_ms')} | "
        f"results: {retrieval.get('result_count')} | "
        f"k: {retrieval.get('k')}"
    )
    print(
        f"  store_abstain: {retrieval.get('store_abstain')} | "
        f"harness_abstain: {retrieval.get('harness_abstain')} | "
        f"top_score: {retrieval.get('top_score')}"
    )
    print(
        f"  SQL statements: {sql.get('statement_count')} | "
        f"operations: {sql.get('operations', {})}"
    )
    print(
        "  billing-api owner rank: "
        f"{owner_hits[0].get('rank') if owner_hits else 'NOT IN TOP-K'}"
    )

    print("  top retrieved items (metadata only):")
    for item in items[:8]:
        print(
            "    #{rank} id={id} entity={entity} attribute={attribute} "
            "score={score} via={via} valid_from={valid_from} "
            "valid_to={valid_to}".format(
                rank=item.get("rank"),
                id=item.get("id"),
                entity=item.get("entity") or "-",
                attribute=item.get("attribute") or "-",
                score=item.get("score"),
                via=item.get("via"),
                valid_from=item.get("valid_from"),
                valid_to=item.get("valid_to") or "open",
            )
        )

    print("  most frequent SQL shapes:")
    for shape in (sql.get("templates") or [])[:5]:
        print(
            f"    x{shape.get('count')}: {shape.get('sql_shape')}"
        )

    result = {
        "mode": label,
        "path": str(path),
        "query_sha256": retrieval.get("query_sha256"),
        "trace_id": retrieval.get("trace_id"),
        "elapsed_ms": retrieval.get("elapsed_ms"),
        "result_count": retrieval.get("result_count"),
        "store_abstain": retrieval.get("store_abstain"),
        "harness_abstain": retrieval.get("harness_abstain"),
        "top_score": retrieval.get("top_score"),
        "sql_statement_count": sql.get("statement_count"),
        "owner_rank": owner_hits[0].get("rank") if owner_hits else None,
        "owner_item_id": owner_hits[0].get("id") if owner_hits else None,
        "retrieved_ids": [item.get("id") for item in items],
        "answer_model": answer.get("model") if answer else None,
        "provider": answer.get("provider") if answer else None,
        "model_latency_ms": (
            answer.get("model_latency_ms") if answer else None
        ),
        "generation_elapsed_ms": (
            answer.get("generation_elapsed_ms") if answer else None
        ),
        "agent_total_elapsed_ms": (
            answer.get("agent_total_elapsed_ms") if answer else None
        ),
        "answer_sha256": (
            answer.get("answer_sha256") if answer else None
        ),
        "answer_chars": answer.get("answer_chars") if answer else None,
    }

    if show_content and answer and answer.get("answer_redacted"):
        print("  redacted answer:")
        print(
            "    "
            + str(answer["answer_redacted"]).replace("\n", "\n    ")
        )
    elif answer and answer.get("content_logging_enabled"):
        print(
            "  answer text omitted (pass --show-content to display "
            "the already-redacted answer)."
        )
    elif answer:
        print("  answer text not stored in log (content logging was disabled).")
    else:
        print("  matching agent_answer_completed event not found.")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--query",
        default="Who owns billing-api?",
        help="exact query used by both agent runs",
    )
    parser.add_argument(
        "--flat-log",
        type=Path,
        default=Path("logs/phase8-agent-flat.jsonl"),
    )
    parser.add_argument(
        "--graph-log",
        type=Path,
        default=Path("logs/phase8-agent.jsonl"),
    )
    parser.add_argument(
        "--show-content",
        action="store_true",
        help="show an answer only if a redacted answer is present in the log",
    )
    args = parser.parse_args()

    query_hash = hashlib.sha256(
        args.query.encode("utf-8", errors="replace")
    ).hexdigest()

    flat = summarize(
        "flat",
        args.flat_log,
        load_jsonl(args.flat_log),
        query_hash,
        args.show_content,
    )
    graph = summarize(
        "graph",
        args.graph_log,
        load_jsonl(args.graph_log),
        query_hash,
        args.show_content,
    )

    print("\n[PAIRED COMPARISON]")
    print(
        f"  same query hash: "
        f"{flat['query_sha256'] == graph['query_sha256']}"
    )

    for key, title in (
        ("owner_rank", "owner rank"),
        ("elapsed_ms", "retrieval latency ms"),
        ("sql_statement_count", "SQL statements"),
        ("result_count", "result count"),
    ):
        print(
            f"  {title}: flat={flat.get(key)} | "
            f"graph={graph.get(key)}"
        )

    flat_ms = flat.get("elapsed_ms")
    graph_ms = graph.get("elapsed_ms")

    if (
        isinstance(flat_ms, (int, float))
        and not isinstance(flat_ms, bool)
        and flat_ms > 0
        and isinstance(graph_ms, (int, float))
        and not isinstance(graph_ms, bool)
    ):
        change = (flat_ms - graph_ms) / flat_ms * 100.0
        if change > 0:
            print(f"  graph latency: {change:.1f}% faster than flat")
        elif change < 0:
            print(f"  graph latency: {abs(change):.1f}% slower than flat")
        else:
            print("  graph latency: equal to flat")

    flat_ids = flat.get("retrieved_ids") or []
    graph_ids = graph.get("retrieved_ids") or []

    if flat_ids == graph_ids:
        print("  retrieved IDs: identical and in the same order")
    else:
        flat_set = set(flat_ids)
        graph_set = set(graph_ids)
        print(
            f"  shared retrieved IDs: {len(flat_set & graph_set)}; "
            f"flat-only: {len(flat_set - graph_set)}; "
            f"graph-only: {len(graph_set - flat_set)}"
        )

    print(
        "\nNote: scores are not assumed to be calibrated across modes; "
        "this script compares ranks, correctness signals, latency, "
        "SQL work, and evidence IDs."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
