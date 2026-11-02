from __future__ import annotations

from eval.iterative_baseline import run_seed
from eval.synthetic_v2 import FAMILIES, make_embedder


def test_iterative_baseline_runs_and_never_does_worse_than_single_round_filter():
    rows = run_seed(seed=0, entities=20, episodes=20, k=8, rounds=2, embedder=make_embedder("hash"))
    assert set(rows) == {"flat_iterative", "graph", "flat_filter"}
    for family in FAMILIES:
        if family == "unanswerable":
            continue
        for mode in rows:
            assert rows[mode][family], (mode, family)
        assert all(r["calls"] >= 1 for r in rows["flat_iterative"][family])
    mean = lambda mode, fam: sum(r["accuracy"] for r in rows[mode][fam]) / len(rows[mode][fam])  # noqa: E731
    for family in FAMILIES:
        if family != "unanswerable":
            assert mean("flat_iterative", family) >= mean("flat_filter", family)
