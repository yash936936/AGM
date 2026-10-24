"""Durable-memory acceptance tests using synthetic, non-sensitive histories.

These validate cross-session storage behavior. They do not substitute for a
consented, de-identified real-history evaluation before production launch.
"""
from __future__ import annotations

from agm import Ctx, MemoryStore, WriteItem


def context(tenant: str = "acceptance-tenant", writer: str = "acceptance-writer") -> Ctx:
    return Ctx(tenant_id=tenant, writer_id=writer, tier="human_verified", project="acceptance")


def test_cross_session_recall_survives_store_close_and_reopen(tmp_path):
    db = tmp_path / "persistent-memory.db"
    ctx = context()
    first = MemoryStore(str(db))
    saved = first.write(ctx, WriteItem(
        kind="fact", entity="Project Orion", attribute="preferred_format", value="weekly summary",
        text="Project Orion updates should be delivered as a weekly summary.",
    ))
    assert saved.item_id
    first.close()

    # A newly constructed store represents a separate session/process boundary.
    second = MemoryStore(str(db))
    try:
        result = second.retrieve(ctx, "Project Orion preferred format weekly summary", entity="Project Orion")
        assert any(n.id == saved.item_id and n.value == "weekly summary" for n in result.items)
    finally:
        second.close()


def test_tenant_boundary_prevents_cross_tenant_recall(tmp_path):
    db = tmp_path / "tenant-boundary.db"
    writer_ctx = context("tenant-A", "writer-A")
    other_ctx = context("tenant-B", "writer-B")
    store = MemoryStore(str(db))
    try:
        store.write(writer_ctx, WriteItem(
            kind="fact", entity="Project Cedar", attribute="access_code_hint", value="blue lantern",
            text="Synthetic test memory: Project Cedar access-code hint is blue lantern.",
        ))
        result = store.retrieve(other_ctx, "Project Cedar access code hint blue lantern", entity="Project Cedar")
        assert all(n.tenant != "tenant-A" for n in result.items)
        assert not any(n.value == "blue lantern" for n in result.items)
    finally:
        store.close()


def test_correction_is_recalled_as_current_after_reopen_and_history_is_preserved(tmp_path):
    db = tmp_path / "correction-history.db"
    ctx = context()
    store = MemoryStore(str(db))
    old = store.write(ctx, WriteItem(
        kind="fact", entity="Project Juniper", attribute="meeting_day", value="Tuesday",
        text="Project Juniper's meeting day is Tuesday.", valid_from="2024-01-01T00:00:00Z",
    ))
    new = store.write(ctx, WriteItem(
        kind="fact", entity="Project Juniper", attribute="meeting_day", value="Thursday",
        text="Correction: Project Juniper's meeting day is Thursday.", valid_from="2025-01-01T00:00:00Z",
    ))
    store.close()

    reopened = MemoryStore(str(db))
    try:
        current = reopened.retrieve(ctx, "Project Juniper meeting day", entity="Project Juniper")
        assert any(n.id == new.item_id and n.value == "Thursday" for n in current.items)
        history = reopened.history(ctx, "Project Juniper", "meeting_day")
        assert {n.id for n in history} >= {old.item_id, new.item_id}
    finally:
        reopened.close()


def test_deleted_memory_stays_unavailable_after_reopen_and_view_rebuild(tmp_path):
    db = tmp_path / "deleted-memory.db"
    ctx = context()
    store = MemoryStore(str(db))
    saved = store.write(ctx, WriteItem(
        kind="fact", entity="Project Maple", attribute="private_marker", value="synthetic-delete-marker-7f31",
        text="Synthetic test memory marker synthetic-delete-marker-7f31 for Project Maple.",
    ))
    assert saved.item_id
    result = store.delete(ctx, saved.item_id)
    assert result.deleted
    store.close()

    reopened = MemoryStore(str(db))
    try:
        reopened.rebuild_views()
        result = reopened.retrieve(ctx, "synthetic-delete-marker-7f31 Project Maple", entity="Project Maple")
        assert all(n.id != saved.item_id for n in result.items)
        payloads = " ".join(row[0] for row in reopened.conn.execute("SELECT payload FROM events"))
        assert "synthetic-delete-marker-7f31" not in payloads
    finally:
        reopened.close()
