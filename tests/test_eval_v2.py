from __future__ import annotations

import json
from difflib import SequenceMatcher
from pathlib import Path

from agm import Ctx, MemoryStore
from agm.embed import HashEmbedder
from eval.synthetic_v2 import FAMILIES, aggregate_seed_metrics, build_store, decision_verdicts, evaluate_seed, make_questions


def _stable_metrics(result):
    """Latency is a wall-clock measurement; compare deterministic outcome metrics only."""
    def strip_latency(value):
        if isinstance(value, dict):
            return {
                key: strip_latency(item) for key, item in value.items()
                if key not in {"p50_latency_ms", "p95_latency_ms"}
            }
        if isinstance(value, list):
            return [strip_latency(item) for item in value]
        return value
    return strip_latency(result)


def test_tiny_config_runs_all_modes_and_writes_json(tmp_path, capsys):
    output_dir = tmp_path / "results"
    from eval.synthetic_v2 import main

    code = main([
        "--entities", "20", "--episodes", "100", "--seeds", "2", "--k", "8",
        "--results-dir", str(output_dir),
    ])
    output = capsys.readouterr().out
    assert code == 0
    assert "flat" in output and "flat_filter" in output and "graph" in output
    assert "Caveat (D-007)" in output
    assert "DECISION multi_hop:" in output
    assert "DECISION stale:" in output
    assert "graph vs flat_filter:" in output
    assert "PROMISING" in output or "NOT SHOWN" in output or "FLAT BETTER" in output
    files = list(output_dir.glob("*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert data["configuration"]["seeds"] == [0, 1]
    assert set(data["aggregate"]["families"]) == set(FAMILIES)
    assert set(data["aggregate"]["overall"]) == {"flat", "flat_filter", "graph"}
    assert data["caveat"].startswith("D-007")
    assert all(len(data["per_seed"][0]["families"][family]) == 3 for family in FAMILIES)


def test_same_seed_has_identical_gold_and_outcome_metrics():
    embedder = HashEmbedder()
    kwargs = dict(seed=42, entities=20, episodes=100, k=8, embedder=embedder)
    first = evaluate_seed(**kwargs)
    second = evaluate_seed(**kwargs)
    assert first["gold_manifest"] == second["gold_manifest"]
    assert _stable_metrics(aggregate_seed_metrics([first])) == _stable_metrics(aggregate_seed_metrics([second]))
    first_trace = [{k: v for k, v in row.items() if k not in {"latency_ms", "top_score"}} for row in first["query_trace"]]
    second_trace = [{k: v for k, v in row.items() if k not in {"latency_ms", "top_score"}} for row in second["query_trace"]]
    assert first_trace == second_trace


def test_every_question_family_has_at_least_one_question():
    ctx = Ctx(tenant_id="test", writer_id="seed", tier="human_verified", project="synthetic")
    with MemoryStore(":memory:", embedder=HashEmbedder()) as store:
        data = build_store(store, seed=7, entities=20, episodes=100)
        questions = make_questions(data, seed=7, entities=20)
    assert set(question.family for question in questions) == set(FAMILIES)
    assert all(any(q.family == family for q in questions) for family in FAMILIES)


def test_stale_owner_text_is_near_identical_to_current_text():
    ctx = Ctx(tenant_id="test", writer_id="seed", tier="human_verified", project="synthetic")
    with MemoryStore(":memory:", embedder=HashEmbedder()) as store:
        data = build_store(store, seed=11, entities=20, episodes=0)
    corrected = data["corrected_owner_entities"]
    assert corrected
    entity = corrected[0]
    history = data["histories"][(entity, "owner")]
    stale_text, current_text = history[-2].text, history[-1].text
    assert SequenceMatcher(None, stale_text, current_text).ratio() >= 0.70



def test_graph_is_not_labelled_promising_if_flat_filter_wins():
    def metric(mean, seed_values):
        return {"mean": mean, "ci95": [mean, mean], "seed_values": seed_values}

    modes = {
        "flat": {"accuracy": metric(0.38, [0.38, 0.38]), "stale_error_rate": metric(0.0, [0.0, 0.0])},
        "flat_filter": {"accuracy": metric(1.0, [1.0, 1.0]), "stale_error_rate": metric(0.0, [0.0, 0.0])},
        "graph": {"accuracy": metric(0.90, [0.90, 0.90]), "stale_error_rate": metric(0.0, [0.0, 0.0])},
    }
    aggregated = {
        "overall": modes,
        "families": {
            family: {
                mode: {
                    "accuracy": metric(
                        modes[mode]["accuracy"]["mean"] if family == "entity_centric" else 0.5,
                        modes[mode]["accuracy"]["seed_values"] if family == "entity_centric" else [0.5, 0.5],
                    ),
                    "stale_error_rate": metric(0.0, [0.0, 0.0]),
                }
                for mode in ("flat", "flat_filter", "graph")
            }
            for family in FAMILIES
        },
    }
    verdicts = decision_verdicts(aggregated)
    assert verdicts["family_verdicts"]["entity_centric"] == "FLAT BETTER"
    assert verdicts["pairwise"]["entity_centric"]["flat_filter"]["verdict"] == "FLAT BETTER"
    assert verdicts["pairwise"]["entity_centric"]["flat"]["verdict"] == "NOT SHOWN"
