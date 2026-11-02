#!/usr/bin/env python3
"""Stronger flat baseline for the synthetic v2 corpus: iterative (agent-style) flat retrieval.

Added after the first v2 results were seen, so it is reported as a *post-hoc* baseline. It can only
make the graph's comparison harder, never easier. It does NOT change synthetic_v2.py or its
pre-declared decision rule.

flat_iterative = what a tool-using agent does with flat retrieval alone: retrieve with the entity named
in the question, scan the returned text for other known entity names, retrieve again for those
(at most --rounds extra rounds, matching the graph's maximum depth of 2), merge the results.
Cost is counted as retrieve calls and summed latency.

Smoke test on synthetic data; not evidence for H1-H7 (D-007).
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from agm import MemoryStore  # noqa: E402
from eval.synthetic_v2 import (  # noqa: E402
    FAMILIES, _query_metrics, bootstrap_ci, build_store, deterministic_node_ids, make_embedder, make_questions,
)


def iterative_retrieve(store, ctx, question, names_re, *, k, rounds):
    calls, merged, visited = 0, {}, {question.known_entity}
    frontier = [question.known_entity]
    start = time.perf_counter()
    for depth in range(rounds + 1):
        next_frontier: list[str] = []
        for entity in frontier:
            result = store.retrieve(ctx, question.query, entity=entity, as_of=question.as_of, k=k, expand=False)
            calls += 1
            for item in result.items:
                merged.setdefault(item.id, item)
                if depth < rounds:
                    for name in names_re.findall(item.text or ""):
                        if name not in visited:
                            visited.add(name)
                            next_frontier.append(name)
        frontier = next_frontier
        if not frontier:
            break
    items = sorted(merged.values(), key=lambda n: -float(n.score))
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return SimpleNamespace(items=items, abstain=not items, route=SimpleNamespace(expanded_n=0)), calls, elapsed_ms


def run_seed(seed, entities, episodes, k, rounds, embedder):
    rows = {"flat_iterative": {f: [] for f in FAMILIES}, "graph": {f: [] for f in FAMILIES},
            "flat_filter": {f: [] for f in FAMILIES}}
    with tempfile.TemporaryDirectory(prefix=f"agm-iter-{seed}-") as tmp, deterministic_node_ids(seed):
        with MemoryStore(str(Path(tmp) / "m.db"), embedder=embedder) as store:
            data = build_store(store, seed=seed, entities=entities, episodes=episodes)
            names = sorted(data["entities"], key=len, reverse=True)
            names_re = re.compile(r"(?<![\w-])(" + "|".join(re.escape(n) for n in names) + r")(?![\w-])")
            for q in make_questions(data, seed=seed, entities=entities):
                for mode in rows:
                    t0 = time.perf_counter()
                    if mode == "flat_iterative":
                        result, calls, ms = iterative_retrieve(store, data["ctx"], q, names_re, k=k, rounds=rounds)
                    else:
                        expand = mode == "graph"
                        result = store.retrieve(data["ctx"], q.query, entity=q.known_entity if mode == "flat_filter" else None,
                                                as_of=q.as_of, k=k, expand=expand,
                                                graph_hops=2 if expand and q.family == "multi_hop" else None)
                        calls, ms = 1, (time.perf_counter() - t0) * 1000.0
                    row = _query_metrics(q, result, ms)
                    row["calls"] = calls
                    rows[mode][q.family].append(row)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--entities", type=int, default=200); ap.add_argument("--episodes", type=int, default=2000)
    ap.add_argument("--k", type=int, default=8); ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--embedder", choices=("hash", "st"), default="hash")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    embedder = make_embedder(args.embedder)
    per_seed = [run_seed(s, args.entities, args.episodes, args.k, args.rounds, embedder)
                for s in range(args.seed, args.seed + args.seeds)]
    report = {"protocol": "agm_iterative_flat_baseline_v1 (post-hoc)", "seeds": args.seeds, "entities": args.entities,
              "episodes": args.episodes, "k": args.k, "rounds": args.rounds, "embedder": embedder.model_id, "families": {}}
    print(f"post-hoc baseline | seeds={args.seeds} entities={args.entities} episodes={args.episodes} k={args.k} "
          f"rounds={args.rounds} embedder={embedder.model_id}\n")
    print(f"{'family':15} {'mode':15} {'accuracy':>9} {'retrieve calls':>15} {'p50 ms':>8}")
    for family in FAMILIES:
        if family == "unanswerable":
            continue
        report["families"][family] = {}
        acc = {}
        for mode in ("flat_filter", "flat_iterative", "graph"):
            seed_means = [statistics.fmean(float(r["accuracy"]) for r in s[mode][family]) for s in per_seed]
            rows = [r for s in per_seed for r in s[mode][family]]
            lat = statistics.median(r["latency_ms"] for r in rows)
            calls = statistics.fmean(r["calls"] for r in rows)
            acc[mode] = seed_means
            report["families"][family][mode] = {"accuracy": statistics.fmean(seed_means), "calls": calls, "p50_ms": lat}
            print(f"{family:15} {mode:15} {statistics.fmean(seed_means):9.3f} {calls:15.2f} {lat:8.1f}")
        diffs = [g - i for g, i in zip(acc["graph"], acc["flat_iterative"])]
        ci = bootstrap_ci(diffs, salt=f"iter:{family}")
        report["families"][family]["graph_minus_iterative_ci95"] = ci
        print(f"{'':15} graph - flat_iterative = {statistics.fmean(diffs):+.3f}  95% CI {ci}\n")
    if args.output:
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
