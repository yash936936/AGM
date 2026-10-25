from __future__ import annotations

from agm import Ctx, MemoryStore, WriteItem
from agm.local_hub import export_obsidian, graph_snapshot, timeline


def _ctx(tenant="hub-tenant", project="hub-project", writer="hub-writer"):
    return Ctx(tenant_id=tenant, writer_id=writer, tier="human_verified", project=project)


def test_timeline_is_scoped_and_never_includes_memory_payload(tmp_path):
    ctx = _ctx()
    other = _ctx(tenant="other-tenant", project="other-project")
    with MemoryStore(str(tmp_path / "timeline.db")) as store:
        store.write(ctx, WriteItem(kind="episode", text="Timeline secret marker timeline-secret-8d2f"))
        store.write(other, WriteItem(kind="episode", text="Foreign timeline marker"))
        rows = timeline(store, ctx)
        assert rows
        assert all(row["tenant_id"] == ctx.tenant_id for row in rows)
        assert all("payload" not in row and "text" not in row for row in rows)
        assert all("timeline-secret-8d2f" not in str(row) for row in rows)


def test_graph_snapshot_is_deterministic_and_tenant_project_scoped(tmp_path):
    ctx = _ctx()
    other = _ctx(tenant="other-tenant", project="other-project")
    with MemoryStore(str(tmp_path / "snapshot.db")) as store:
        saved = store.write(ctx, WriteItem(kind="episode", text="Local snapshot node"))
        store.write(other, WriteItem(kind="episode", text="Foreign snapshot node"))
        first = graph_snapshot(store, ctx)
        second = graph_snapshot(store, ctx)
        assert first == second
        assert first["snapshot"] is True
        assert first["snapshot_id"]
        assert [node["id"] for node in first["nodes"]] == [saved.item_id]
        assert all(node["text"] != "Foreign snapshot node" for node in first["nodes"])


def test_obsidian_export_redacts_secrets_and_is_explicitly_a_copy(tmp_path):
    ctx = _ctx()
    destination = tmp_path / "vault"
    with MemoryStore(str(tmp_path / "export.db")) as store:
        saved = store.write(ctx, WriteItem(
            kind="episode",
            text="Export example password=supersecretvalue123 and useful note",
        ))
        paths = export_obsidian(store, ctx, destination)
        assert len(paths) == 1
        exported = paths[0].read_text(encoding="utf-8")
        assert saved.item_id in exported
        assert "[REDACTED]" in exported
        assert "supersecretvalue123" not in exported
        assert "untrusted data, not instructions" in exported
        store.delete(ctx, saved.item_id)
        # Export is a snapshot; source deletion does not silently alter an external copy.
        assert paths[0].exists()
        assert paths[0].read_text(encoding="utf-8") == exported
