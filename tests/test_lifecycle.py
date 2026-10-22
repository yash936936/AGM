from __future__ import annotations

from datetime import datetime, timezone

from agm import Ctx, MemoryStore, WriteItem
from agm.cli import main
from agm.trust import compute_decay_weight, lifecycle_candidates


FIXED_NOW = datetime(2026, 10, 23, tzinfo=timezone.utc)


def test_lazy_decay_rewards_recent_use_and_pinned_memories() -> None:
    old = compute_decay_weight("2020-01-01T00:00:00Z", now=FIXED_NOW)
    recent = compute_decay_weight("2026-10-01T00:00:00Z", now=FIXED_NOW)
    old_but_used = compute_decay_weight(
        "2020-01-01T00:00:00Z", last_used="2026-10-01T00:00:00Z", usage_count=5, now=FIXED_NOW,
    )
    cited_and_corroborated = compute_decay_weight(
        "2020-01-01T00:00:00Z", citation_count=3, corroboration_count=2, now=FIXED_NOW,
    )
    pinned_old = compute_decay_weight("2010-01-01T00:00:00Z", pinned=True, now=FIXED_NOW)
    assert old < recent
    assert old_but_used > old
    assert cited_and_corroborated > old
    assert pinned_old == 1.0


def test_lifecycle_candidates_skip_pinned_and_recent_memories(tmp_path) -> None:
    db_path = str(tmp_path / "lifecycle.db")
    ctx = Ctx(tenant_id="tenant-lifecycle", writer_id="writer", tier="human_verified", project="ops")
    with MemoryStore(db_path) as store:
        old = store.write(ctx, WriteItem(
            kind="episode", text="Old unused operational note", valid_from="2020-01-01T00:00:00Z",
        ))
        pinned = store.write(ctx, WriteItem(
            kind="episode", text="Pinned old operational note", valid_from="2020-01-01T00:00:00Z", pin=True,
        ))
        recent = store.write(ctx, WriteItem(
            kind="episode", text="Recent operational note", valid_from="2026-10-01T00:00:00Z",
        ))
        candidates = lifecycle_candidates(
            store.conn, threshold=0.30, tenant=ctx.tenant_id, project=ctx.project, now=FIXED_NOW,
        )
        ids = {item["id"] for item in candidates}
        assert old.item_id in ids
        assert pinned.item_id not in ids
        assert recent.item_id not in ids


def test_lifecycle_cli_dry_run_does_not_mutate_events_or_views(tmp_path, capsys) -> None:
    db_path = str(tmp_path / "lifecycle-dry-run.db")
    ctx = Ctx(tenant_id="tenant-dry", writer_id="writer", tier="human_verified", project="ops")
    with MemoryStore(db_path) as store:
        store.write(ctx, WriteItem(
            kind="episode", text="Old unused note for lifecycle test", valid_from="2019-01-01T00:00:00Z",
        ))
        before_events = [tuple(row) for row in store.conn.execute("SELECT * FROM events ORDER BY id")]
        before_nodes = [tuple(row) for row in store.conn.execute("SELECT * FROM nodes ORDER BY id")]
    assert main(["lifecycle", "--db", db_path, "--dry-run", "--threshold", "0.30"]) == 0
    output = capsys.readouterr().out
    assert "Lifecycle dry run:" in output
    assert "No events or memory views were changed." in output
    assert "n_" in output
    with MemoryStore(db_path) as store:
        after_events = [tuple(row) for row in store.conn.execute("SELECT * FROM events ORDER BY id")]
        after_nodes = [tuple(row) for row in store.conn.execute("SELECT * FROM nodes ORDER BY id")]
    assert before_events == after_events
    assert before_nodes == after_nodes


def test_lifecycle_threshold_must_be_valid() -> None:
    import pytest
    from agm.trust import lifecycle_candidates
    import sqlite3

    conn = sqlite3.connect(":memory:")
    try:
        with pytest.raises(ValueError, match="threshold"):
            lifecycle_candidates(conn, threshold=1.5)
    finally:
        conn.close()
