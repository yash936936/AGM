#!/usr/bin/env python3
"""Synthetic smoke evaluation comparing AGM's flat and graph retrieval paths.

Latency measurements are local smoke diagnostics, not production benchmarks.
The scenarios and scores are illustrative only; they are not evidence for H1-H7.
See decisions D-007 and D-020 before interpreting differences between modes.
"""
from __future__ import annotations

import argparse
import json
import platform
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from agm import Ctx, MemoryStore, Relation, WriteItem


@dataclass(frozen=True)
class Scenario:
    name: str
    query: str
    expected_value: str | None
    entity: str | None = None
    stale_value: str | None = None


SCENARIOS = (
    Scenario(
        name="corrected fact",
        query="What is the current release version for AGM?",
        expected_value="0.4.0",
        entity="AGM",
        stale_value="0.3.0",
    ),
    Scenario(
        name="entity owner",
        query="Who owns the service?",
        expected_value="platform team",
        entity="service",
    ),
    Scenario(
        name="related database",
        query="What database configuration is linked to the service dependency?",
        expected_value="SQLite",
    ),
    Scenario(
        name="unanswerable",
        query="Which planet is made entirely from blue glass?",
        expected_value=None,
    ),
)


def seed_store(store: MemoryStore) -> None:
    ctx = Ctx(tenant_id="eval-tenant", writer_id="eval-curator", tier="human_verified", project="synthetic")
    store.write(ctx, WriteItem(
        kind="fact", entity="AGM", attribute="release", value="0.3.0",
        text="AGM release version is 0.3.0.", valid_from="2025-01-01T00:00:00Z",
    ))
    store.write(ctx, WriteItem(
        kind="fact", entity="AGM", attribute="release", value="0.4.0",
        text="AGM release version is 0.4.0.", valid_from="2026-01-01T00:00:00Z",
    ))
    store.write(ctx, WriteItem(
        kind="fact", entity="service", attribute="owner", value="platform team",
        text="The service owner is the platform team.",
    ))
    store.write(ctx, WriteItem(
        kind="fact", entity="service", attribute="dependency", value="database",
        text="The service has a database dependency.",
        relations=[Relation(rel="relates", target="database")],
    ))
    store.write(ctx, WriteItem(
        kind="fact", entity="database", attribute="engine", value="SQLite",
        text="The database engine for the service dependency is SQLite.",
    ))
    for index in range(60):
        store.write(ctx, WriteItem(
            kind="episode",
            text=(f"Synthetic unrelated archive note {index}: laboratory inventory "
                  f"batch code item-{index:03d} was checked."),
        ))


def _contains_answer(result, expected: str) -> bool:
    expected_folded = expected.casefold()
    return any(
        expected_folded in " ".join(filter(None, [item.value, item.text])).casefold()
        for item in result.items
    )


def _percentile(samples: list[float], percentile: float) -> float:
    """Return a nearest-rank percentile in milliseconds."""
    if not samples:
        return 0.0
    ordered = sorted(samples)
    index = max(0, min(len(ordered) - 1, int((percentile / 100) * len(ordered) + 0.999999) - 1))
    return ordered[index] * 1000


def evaluate_mode(mode: str, *, k: int, repeats: int = 25) -> dict[str, float | int | str]:
    expand = mode == "graph"
    total_answerable = 0
    correct = 0
    stale_fact_queries = 0
    stale_errors = 0
    abstentions = 0
    expanded_items = 0
    latencies: list[float] = []
    errors = 0
    query_count = 0
    with tempfile.TemporaryDirectory(prefix=f"agm-eval-{mode}-") as temp_dir:
        db_path = str(Path(temp_dir) / "memory.db")
        ctx = Ctx(tenant_id="eval-tenant", writer_id="eval-reader", tier="human_verified", project="synthetic")
        with MemoryStore(db_path) as store:
            seed_store(store)
            # Score each authored scenario once, separate from repeated timing samples.
            for scenario in SCENARIOS:
                result = store.retrieve(
                    ctx, scenario.query, entity=scenario.entity, k=k, expand=expand,
                )
                expanded_items += result.route.expanded_n
                abstentions += int(result.abstain)
                if scenario.expected_value is not None:
                    total_answerable += 1
                    correct += int(_contains_answer(result, scenario.expected_value))
                if scenario.stale_value is not None:
                    stale_fact_queries += 1
                    surfaced_values = [str(item.value or "") for item in result.items]
                    stale_errors += int(any(scenario.stale_value.casefold() == value.casefold() for value in surfaced_values))

            # Warm each query once, then collect retrieval-only timings.
            for scenario in SCENARIOS:
                store.retrieve(ctx, scenario.query, entity=scenario.entity, k=k, expand=expand)
            for _ in range(repeats):
                for scenario in SCENARIOS:
                    started = time.perf_counter()
                    try:
                        store.retrieve(ctx, scenario.query, entity=scenario.entity, k=k, expand=expand)
                    except Exception:
                        errors += 1
                    else:
                        latencies.append(time.perf_counter() - started)
                    query_count += 1

    elapsed = sum(latencies)
    return {
        "mode": mode,
        "accuracy": correct / total_answerable if total_answerable else 0.0,
        "stale_error": stale_errors / stale_fact_queries if stale_fact_queries else 0.0,
        "abstention": abstentions / len(SCENARIOS),
        "expanded_items": expanded_items,
        "answerable": total_answerable,
        "scenarios": len(SCENARIOS),
        "queries": query_count,
        "errors": errors,
        "latency_p50_ms": _percentile(latencies, 50),
        "latency_p95_ms": _percentile(latencies, 95),
        "latency_p99_ms": _percentile(latencies, 99),
        "throughput_qps": len(latencies) / elapsed if elapsed > 0 else 0.0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, default=5, help="maximum returned memories per scenario")
    parser.add_argument("--repeats", type=int, default=25, help="timed repetitions per scenario and mode")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="output format; JSON is suitable for archiving or automation")
    args = parser.parse_args(argv)
    if args.k < 1:
        parser.error("--k must be at least 1")
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")

    results = [evaluate_mode(mode, k=args.k, repeats=args.repeats) for mode in ("flat", "graph")]
    if args.format == "json":
        print(json.dumps({
            "benchmark": "agm_synthetic_retrieval_smoke",
            "benchmark_type": "synthetic_smoke_not_production_benchmark",
            "metadata": {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "embedder": "hash-256-v1",
                "top_k": args.k,
                "timed_repeats_per_scenario": args.repeats,
                "scenario_count": len(SCENARIOS),
                "timed_queries_per_mode": len(SCENARIOS) * args.repeats,
                "timing_scope": "retrieval calls only after one warm-up per scenario; excludes setup and process startup",
            },
            "results": results,
            "caveats": [
                "Synthetic hand-authored cases are not evidence for or against hypotheses H1-H7 (D-007).",
                "Small sample size, weak hashing embedder, machine load, and hand-authored scenarios limit interpretation.",
                "Throughput is successful retrieval calls divided by the sum of measured retrieval-call durations; it is not end-to-end concurrent service throughput.",
                "No held-out consented real-history evaluation is represented by this output.",
            ],
        }, indent=2, sort_keys=True))
        return 0
    print("AGM synthetic retrieval smoke evaluation (not a production benchmark)")
    print(f"Scenarios: {len(SCENARIOS)}; top-k: {args.k}; timed repeats/scenario: {args.repeats}; embedder: hash-256-v1")
    print("Quality metrics: accuracy = expected answer present in returned items; stale error = old value returned for corrected-fact case; abstention = abstained scenarios / all scenarios.")
    print("Performance metrics time retrieval calls only after one warm-up per scenario; seed/setup and process startup are excluded.")
    print()
    print(f"{'mode':<7} {'accuracy':>9} {'stale-error':>12} {'abstention':>11} {'p50 ms':>9} {'p95 ms':>9} {'p99 ms':>9} {'q/s':>9} {'errors':>8}")
    print("-" * 96)
    for result in results:
        print(
            f"{result['mode']:<7} {result['accuracy']:>8.1%} "
            f"{result['stale_error']:>11.1%} {result['abstention']:>10.1%} "
            f"{result['latency_p50_ms']:>9.3f} {result['latency_p95_ms']:>9.3f} "
            f"{result['latency_p99_ms']:>9.3f} {result['throughput_qps']:>9.1f} "
            f"{result['errors']:>8d}"
        )
    print()
    print("Caveat (D-007): this synthetic smoke test is not evidence for or against hypotheses H1-H7.")
    print("Scores and timings are affected by hand-authored cases, the weak hashing embedder, machine load, and small sample size; do not treat them as benchmark results.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
