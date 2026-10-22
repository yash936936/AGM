#!/usr/bin/env python3
"""Synthetic smoke evaluation comparing AGM's flat and graph retrieval paths.

The scenarios and scores are illustrative only. They are not evidence for H1-H7;
see decisions D-007 and D-020 before interpreting any difference between modes.
"""
from __future__ import annotations

import argparse
import tempfile
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


def evaluate_mode(mode: str, *, k: int) -> dict[str, float | int | str]:
    expand = mode == "graph"
    total_answerable = 0
    correct = 0
    stale_fact_queries = 0
    stale_errors = 0
    abstentions = 0
    expanded_items = 0
    with tempfile.TemporaryDirectory(prefix=f"agm-eval-{mode}-") as temp_dir:
        db_path = str(Path(temp_dir) / "memory.db")
        ctx = Ctx(tenant_id="eval-tenant", writer_id="eval-reader", tier="human_verified", project="synthetic")
        with MemoryStore(db_path) as store:
            seed_store(store)
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
    return {
        "mode": mode,
        "accuracy": correct / total_answerable if total_answerable else 0.0,
        "stale_error": stale_errors / stale_fact_queries if stale_fact_queries else 0.0,
        "abstention": abstentions / len(SCENARIOS),
        "expanded_items": expanded_items,
        "answerable": total_answerable,
        "scenarios": len(SCENARIOS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, default=5, help="maximum returned memories per scenario")
    args = parser.parse_args(argv)
    if args.k < 1:
        parser.error("--k must be at least 1")

    results = [evaluate_mode(mode, k=args.k) for mode in ("flat", "graph")]
    print("AGM synthetic retrieval smoke evaluation")
    print(f"Scenarios: {len(SCENARIOS)}; top-k: {args.k}; embedder: hash-256-v1")
    print("Metrics: accuracy = expected answer present in returned items; stale error = old value returned for corrected-fact case; abstention = abstained scenarios / all scenarios.")
    print()
    print(f"{'mode':<9} {'accuracy':>10} {'stale-error':>13} {'abstention':>12} {'expanded':>10}")
    print("-" * 58)
    for result in results:
        print(
            f"{result['mode']:<9} {result['accuracy']:>9.1%} "
            f"{result['stale_error']:>12.1%} {result['abstention']:>11.1%} "
            f"{result['expanded_items']:>10d}"
        )
    print()
    print("Caveat (D-007): this synthetic smoke test is not evidence for or against hypotheses H1-H7.")
    print("Scores are affected by hand-authored cases and the weak hashing embedder; do not treat them as benchmark results.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
