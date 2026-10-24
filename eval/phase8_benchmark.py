#!/usr/bin/env python3
"""Phase 8 flat-vs-graph benchmark across memory sizes and context densities.

This is a synthetic diagnostic harness. It preserves the Phase 6/7 generator and
threshold, changes only the corpus-size/context-density sweep, and does not edit
or overwrite any earlier result JSON.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agm import MemoryStore  # noqa: E402
from agm.embed import HashEmbedder  # noqa: E402
from eval.synthetic_v2 import (  # noqa: E402
    ABSTAIN_THRESHOLD,
    FAMILIES,
    _query_metrics,
    _summarize_query_rows,
    bootstrap_ci,
    build_store,
    deterministic_node_ids,
    make_questions,
)

CONTEXT_EPISODES_PER_ENTITY = {"sparse": 0, "balanced": 1, "dense": 4}
METRICS = (
    "accuracy", "stale_error_rate", "abstention_correctness",
    "store_abstention_rate", "eval_abstention_rate", "p50_latency_ms",
    "p95_latency_ms", "mean_items_returned", "mean_expanded_n",
)


def aggregate_metric(values: list[float], salt: str) -> dict[str, Any]:
    return {
        "mean": statistics.fmean(values) if values else None,
        "ci95": bootstrap_ci(values, salt=salt) if values else None,
        "seed_values": values,
    }


def summarise_cell(seed_stats: list[dict[str, Any]], salt: str) -> dict[str, Any]:
    output: dict[str, Any] = {
        "seeds": len(seed_stats),
        "questions_per_seed_mean": statistics.fmean(s["questions"] for s in seed_stats) if seed_stats else 0,
    }
    for metric in METRICS:
        values = [float(item[metric]) for item in seed_stats if item.get(metric) is not None]
        output[metric] = aggregate_metric(values, f"{salt}:{metric}")
    return output


def run_cell(*, size: int, context: str, seed: int, k: int) -> dict[str, Any]:
    episodes = size * CONTEXT_EPISODES_PER_ENTITY[context]
    start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix=f"agm-phase8-{size}-{context}-{seed}-") as temp_dir, deterministic_node_ids(seed * 100000 + size):
        db_path = Path(temp_dir) / "memory.db"
        with MemoryStore(str(db_path), embedder=HashEmbedder()) as store:
            corpus = build_store(store, seed=seed, entities=size, episodes=episodes)
            ingest_elapsed_ms = (time.perf_counter() - start) * 1000.0
            questions = make_questions(corpus, seed=seed, entities=size)
            initial_usage_rows = store.conn.execute("SELECT id, usage_count, last_used FROM nodes").fetchall()
            initial_usage = [(str(row["id"]), int(row["usage_count"]), row["last_used"]) for row in initial_usage_rows]
            query_rows: list[dict[str, Any]] = []
            family_rows: dict[str, dict[str, list[dict[str, Any]]]] = {
                family: {mode: [] for mode in ("flat", "graph")} for family in FAMILIES
            }
            for mode in ("flat", "graph"):
                store.conn.executemany(
                    "UPDATE nodes SET usage_count = ?, last_used = ? WHERE id = ?",
                    [(count, last_used, node_id) for node_id, count, last_used in initial_usage],
                )
                store.conn.commit()
                for question in questions:
                    query_start = time.perf_counter()
                    result = store.retrieve(
                        corpus["ctx"], question.query, as_of=question.as_of,
                        k=k, expand=(mode == "graph"),
                        graph_hops=2 if mode == "graph" and question.family == "multi_hop" else None,
                    )
                    latency_ms = (time.perf_counter() - query_start) * 1000.0
                    metrics = _query_metrics(question, result, latency_ms)
                    metrics.update({
                        "mode": mode,
                        "size_entities": size,
                        "context_density": context,
                        "episodes_per_entity": CONTEXT_EPISODES_PER_ENTITY[context],
                        "seed": seed,
                        "query": question.query,
                        "known_entity": question.known_entity,
                        "as_of": question.as_of,
                        "gold": [list(value) for value in question.gold],
                        "returned": [
                            {
                                "id": item.id, "entity": item.entity,
                                "attribute": item.attribute, "value": item.value,
                                "score": float(item.score), "via": item.via,
                                "valid_from": item.valid_from, "valid_to": item.valid_to,
                            }
                            for item in result.items
                        ],
                        "store_abstain_reason": result.abstain_reason,
                    })
                    family_rows[question.family][mode].append(metrics)
                    query_rows.append(metrics)
            family_stats = {
                family: {
                    mode: _summarize_query_rows(family_rows[family][mode])
                    for mode in ("flat", "graph")
                }
                for family in FAMILIES
            }
            overall = {
                mode: _summarize_query_rows([row for row in query_rows if row["mode"] == mode])
                for mode in ("flat", "graph")
            }
            node_count = int(store.conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0])
            edge_count = int(store.conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0])
            return {
                "size_entities": size,
                "context_density": context,
                "episodes_per_entity": CONTEXT_EPISODES_PER_ENTITY[context],
                "seed": seed,
                "episodes_requested": episodes,
                "nodes_seeded": node_count,
                "edges_seeded": edge_count,
                "ingest_elapsed_ms": round(ingest_elapsed_ms, 3),
                "elapsed_ms_total": round((time.perf_counter() - start) * 1000.0, 3),
                "families": family_stats,
                "overall": overall,
                "query_trace": query_rows,
            }


def build_aggregate(cells: list[dict[str, Any]], sizes: list[int], contexts: list[str]) -> dict[str, Any]:
    aggregate: dict[str, Any] = {}
    for size in sizes:
        aggregate[str(size)] = {}
        for context in contexts:
            selected = [cell for cell in cells if cell["size_entities"] == size and cell["context_density"] == context]
            if not selected:
                continue
            cell_aggregate: dict[str, Any] = {
                "configuration": {
                    "size_entities": size,
                    "context_density": context,
                    "episodes_per_entity": CONTEXT_EPISODES_PER_ENTITY[context],
                    "seeds": [cell["seed"] for cell in selected],
                    "mean_nodes_seeded": statistics.fmean(cell["nodes_seeded"] for cell in selected),
                    "mean_edges_seeded": statistics.fmean(cell["edges_seeded"] for cell in selected),
                    "mean_ingest_elapsed_ms": statistics.fmean(cell["ingest_elapsed_ms"] for cell in selected),
                },
                "overall": {},
                "families": {},
            }
            for mode in ("flat", "graph"):
                cell_aggregate["overall"][mode] = summarise_cell(
                    [cell["overall"][mode] for cell in selected], f"size={size}:context={context}:overall:{mode}"
                )
            for family in FAMILIES:
                cell_aggregate["families"][family] = {}
                for mode in ("flat", "graph"):
                    cell_aggregate["families"][family][mode] = summarise_cell(
                        [cell["families"][family][mode] for cell in selected],
                        f"size={size}:context={context}:family={family}:{mode}",
                    )
            cell_aggregate["pairwise_deltas"] = {
                "overall_accuracy_graph_minus_flat": {
                    "mean": (
                        cell_aggregate["overall"]["graph"]["accuracy"]["mean"]
                        - cell_aggregate["overall"]["flat"]["accuracy"]["mean"]
                    ) if cell_aggregate["overall"]["graph"]["accuracy"]["mean"] is not None
                    and cell_aggregate["overall"]["flat"]["accuracy"]["mean"] is not None else None,
                    "note": "Phase 8 pairwise diagnostic only; D-024 still requires comparison with flat_filter as well.",
                }
            }
            aggregate[str(size)][context] = cell_aggregate
    return aggregate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[25, 60], help="entity counts to test")
    parser.add_argument("--contexts", nargs="+", choices=tuple(CONTEXT_EPISODES_PER_ENTITY), default=["sparse", "balanced", "dense"], help="episodic context density")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1], help="deterministic seeds")
    parser.add_argument("--k", type=int, default=8)
    parser.add_argument("--results-dir", default="eval/results")
    parser.add_argument("--output", default=None, help="optional explicit JSON path (must not overwrite a Phase 6/7 result)")
    args = parser.parse_args(argv)
    if any(size < 5 for size in args.sizes):
        parser.error("every --sizes value must be >= 5 to generate dependency chains")
    if args.k < 1:
        parser.error("--k must be >= 1")
    if not args.seeds:
        parser.error("provide at least one --seeds value")

    cells: list[dict[str, Any]] = []
    total = len(args.sizes) * len(args.contexts) * len(args.seeds)
    for size in args.sizes:
        for context in args.contexts:
            for seed in args.seeds:
                index = len(cells) + 1
                print(f"[{index}/{total}] size={size}, context={context}, seed={seed}", flush=True)
                cell = run_cell(size=size, context=context, seed=seed, k=args.k)
                print(
                    f"  nodes={cell['nodes_seeded']} edges={cell['edges_seeded']} "
                    f"ingest={cell['ingest_elapsed_ms']:.0f}ms "
                    f"flat acc={cell['overall']['flat']['accuracy']:.3f} "
                    f"graph acc={cell['overall']['graph']['accuracy']:.3f} "
                    f"graph p50/p95={cell['overall']['graph']['p50_latency_ms']:.1f}/{cell['overall']['graph']['p95_latency_ms']:.1f}ms",
                    flush=True,
                )
                cells.append(cell)

    aggregate = build_aggregate(cells, args.sizes, args.contexts)
    created_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "schema_version": 1,
        "created_at": created_at,
        "phase": 8,
        "benchmark": "flat-vs-graph size/context sweep",
        "configuration": {
            "sizes_entities": args.sizes,
            "contexts": {key: CONTEXT_EPISODES_PER_ENTITY[key] for key in args.contexts},
            "seeds": args.seeds,
            "k": args.k,
            "embedder": "hash-256-v1",
            "modes": ["flat", "graph"],
            "abstain_threshold": ABSTAIN_THRESHOLD,
            "question_families": list(FAMILIES),
        },
        "aggregate": aggregate,
        "per_cell": [{key: value for key, value in cell.items() if key != "query_trace"} for cell in cells],
        "query_trace": [row for cell in cells for row in cell["query_trace"]],
        "interpretation_note": "Synthetic diagnostic only (D-007). Graph-vs-flat deltas do not replace the D-024 rule, which requires graph to beat both flat and flat_filter.",
    }
    result_dir = Path(args.results_dir)
    result_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    output = Path(args.output) if args.output else result_dir / f"phase8-benchmark-{timestamp}.json"
    if output.exists() and "20261023T155826.716282Z" in output.name or output.exists() and "20261023T184404.879694Z" in output.name:
        parser.error("refusing to overwrite the preserved Phase 6/7 baseline result")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Saved results: {output}")
    print("D-007 caveat: synthetic benchmark results are not evidence for or against H1-H7.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
