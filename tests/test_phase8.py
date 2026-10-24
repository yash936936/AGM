from __future__ import annotations

import json
from pathlib import Path

from agm import Ctx, MemoryStore, Relation, WriteItem
from agm.diagnostics import audit_store, run_doctor, run_traced_retrieval
from eval.phase8_benchmark import CONTEXT_EPISODES_PER_ENTITY, run_cell
from scripts.ingest_phase8_sample import main as ingest_sample


def _ctx() -> Ctx:
    return Ctx(tenant_id="phase8-test", project="phase8", writer_id="phase8-test-writer", tier="human_verified")


def _write_fact(store: MemoryStore, ctx: Ctx, entity: str, attribute: str, value: str, stamp: str, *, relation: str | None = None) -> None:
    store.write(ctx, WriteItem(
        kind="fact", entity=entity, attribute=attribute, value=value,
        text=f"{entity} {attribute} is {value}.", valid_from=stamp, confidence=0.95,
        relations=[Relation(rel="relates", target=relation)] if relation else [],
    ))


def test_graph_temporal_query_prioritizes_entity_attribute_version(tmp_path: Path) -> None:
    with MemoryStore(str(tmp_path / "temporal.db")) as store:
        ctx = _ctx()
        _write_fact(store, ctx, "billing-api", "owner", "team-old", "2024-01-01T00:00:00Z")
        _write_fact(store, ctx, "billing-api", "owner", "team-current", "2025-01-01T00:00:00Z")
        for index in range(12):
            _write_fact(store, ctx, f"svc-{index:02d}", "owner", f"team-{index:02d}", "2024-01-01T00:00:00Z")
        _write_fact(store, ctx, "billing-api", "runtime", "python", "2024-01-01T00:00:00Z")
        _write_fact(store, ctx, "billing-api", "region", "us-east-1", "2024-01-01T00:00:00Z")
        as_of = "2024-12-31T23:59:59Z"
        result = store.retrieve(
            ctx, "Who owned billing-api immediately before the latest correction?",
            as_of=as_of, k=3, expand=True,
        )
        assert any(item.attribute == "owner" and item.value == "team-old" for item in result.items)
        assert all(item.valid_from <= as_of for item in result.items)


def test_graph_entity_summary_prioritizes_direct_facts(tmp_path: Path) -> None:
    with MemoryStore(str(tmp_path / "entity.db")) as store:
        ctx = _ctx()
        expected = {("owner", "team-target"), ("region", "eu-west-1"), ("runtime", "python"), ("environment", "production")}
        for attribute, value in expected:
            _write_fact(store, ctx, "billing-api", attribute, value, "2025-01-01T00:00:00Z")
        for index in range(20):
            _write_fact(store, ctx, f"billing-copy-{index:02d}", "owner", f"team-target-{index}", "2025-01-01T00:00:00Z")
            store.write(ctx, WriteItem(kind="episode", text=f"billing-api and billing copy {index} rollout and service status reviewed."))
        result = store.retrieve(ctx, "What is known about billing-api?", k=4, expand=True)
        actual = {(item.attribute or "", item.value or "") for item in result.items}
        assert expected <= actual




def test_graph_explicit_attribute_query_ranks_matching_fact_first(tmp_path: Path) -> None:
    with MemoryStore(str(tmp_path / "attribute.db")) as store:
        ctx = _ctx()
        _write_fact(store, ctx, "billing-api", "runtime", "python", "2025-01-01T00:00:00Z")
        _write_fact(store, ctx, "billing-api", "region", "us-east-1", "2025-01-01T00:00:00Z")
        _write_fact(store, ctx, "billing-api", "owner", "team-platform", "2025-01-01T00:00:00Z")
        for index in range(12):
            _write_fact(store, ctx, f"copy-api-{index:02d}", "owner", f"team-copy-{index}", "2025-01-01T00:00:00Z")
        result = store.retrieve(ctx, "Who owns billing-api?", k=8, expand=True)
        assert result.items
        assert result.items[0].entity == "billing-api"
        assert result.items[0].attribute == "owner"
        assert result.items[0].value == "team-platform"

def test_entity_summary_uses_exact_entity_anchor_when_lexical_score_is_low(tmp_path: Path) -> None:
    with MemoryStore(str(tmp_path / "entity-anchor.db")) as store:
        ctx = _ctx()
        _write_fact(store, ctx, "AGM", "storage", "SQLite event log", "2025-01-01T00:00:00Z")
        _write_fact(store, ctx, "AGM", "retrieval_modes", "flat and graph", "2025-01-01T00:00:00Z")
        result = store.retrieve(ctx, "What is known about AGM?", k=4, expand=True)
        assert not result.abstain
        assert {item.attribute for item in result.items} >= {"storage", "retrieval_modes"}

def test_memory_doctor_records_audit_retrieval_sql_and_redacted_content(tmp_path: Path) -> None:
    db = tmp_path / "doctor.db"
    log = tmp_path / "memory-doctor.jsonl"
    with MemoryStore(str(db)) as store:
        ctx = _ctx()
        _write_fact(store, ctx, "billing-api", "owner", "team-old", "2024-01-01T00:00:00Z")
        _write_fact(store, ctx, "billing-api", "owner", "team-current", "2025-01-01T00:00:00Z")
        result = run_doctor(
            store, ctx, modes=["flat", "graph"], log_path=log,
            include_content=True, tail_events=3,
        )
        assert result["probe_count"] >= 4
    events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    kinds = {event["event"] for event in events}
    assert {"memory_audit", "retrieval", "memory_doctor_summary"} <= kinds
    retrieval = next(event for event in events if event["event"] == "retrieval")
    assert retrieval["sql_profile"]["statement_count"] > 0
    assert "query_redacted" in retrieval
    assert retrieval["trace_id"]


def test_sample_ingest_is_idempotent_and_quarantines_injection_example(tmp_path: Path) -> None:
    db = tmp_path / "sample.db"
    log = tmp_path / "ingest.jsonl"
    args = ["--db", str(db), "--log", str(log)]
    assert ingest_sample(args) == 0
    with MemoryStore(str(db)) as store:
        first_events = int(store.conn.execute("SELECT COUNT(*) FROM events WHERE tenant = 'phase8-demo'").fetchone()[0])
        quarantined = int(store.conn.execute("SELECT COUNT(*) FROM nodes WHERE tenant = 'phase8-demo' AND project = 'phase8' AND status = 'quarantined'").fetchone()[0])
    assert ingest_sample(args) == 0
    with MemoryStore(str(db)) as store:
        second_events = int(store.conn.execute("SELECT COUNT(*) FROM events WHERE tenant = 'phase8-demo'").fetchone()[0])
    assert second_events == first_events
    assert quarantined == 1


def test_benchmark_smoke_reports_both_modes_and_all_context_families() -> None:
    cell = run_cell(size=8, context="sparse", seed=0, k=4)
    assert cell["nodes_seeded"] > 0
    assert set(cell["overall"]) == {"flat", "graph"}
    assert set(cell["families"]) == {"single_fact", "stale", "entity_centric", "multi_hop", "temporal", "unanswerable"}
    assert CONTEXT_EPISODES_PER_ENTITY == {"sparse": 0, "balanced": 1, "dense": 4}
    assert cell["overall"]["graph"]["questions"] > 0


def test_memory_doctor_does_not_flag_valid_other_tenant_edges_as_orphans(tmp_path: Path) -> None:
    with MemoryStore(str(tmp_path / "shared-tenants.db")) as store:
        tenant_a = _ctx()
        tenant_b = Ctx(tenant_id="other-tenant", project="phase8", writer_id="other-writer", tier="human_verified")
        _write_fact(store, tenant_a, "billing-api", "owner", "team-a", "2025-01-01T00:00:00Z")
        _write_fact(store, tenant_b, "identity-api", "owner", "team-b", "2025-01-01T00:00:00Z")
        report = audit_store(store, tenant_a, tail_events=0)
        assert not any(finding["code"] == "ORPHAN_GRAPH_EDGES" for finding in report["findings"])
