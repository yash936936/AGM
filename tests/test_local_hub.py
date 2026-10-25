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

def test_timeline_is_newest_first_and_validates_limit(tmp_path):
    import pytest

    ctx = _ctx()
    with MemoryStore(str(tmp_path / "timeline-order.db")) as store:
        first = store.write(ctx, WriteItem(kind="episode", text="First timeline item"))
        second = store.write(ctx, WriteItem(kind="episode", text="Second timeline item"))
        rows = timeline(store, ctx, limit=2)
        assert [row["event_id"] for row in rows] == sorted(
            [row["event_id"] for row in rows], reverse=True
        )
        assert rows[0]["event_id"] > rows[1]["event_id"]
        assert {first.event_id, second.event_id}.issubset(
            {row["event_id"] for row in rows}
        )
        for invalid in (0, -1, 501, True, 1.5, "2"):
            with pytest.raises(ValueError, match="limit"):
                timeline(store, ctx, limit=invalid)


def test_obsidian_export_is_deterministic_and_escapes_frontmatter(tmp_path):
    ctx = _ctx(project='project: "alpha"\\nnext: injected')
    destination = tmp_path / "vault-safe"
    note_text = 'Title\\n---\\nnext: injected\\npassword=topsecretvalue123'
    with MemoryStore(str(tmp_path / "export-frontmatter.db")) as store:
        saved = store.write(ctx, WriteItem(kind="episode", text=note_text))
        first_paths = export_obsidian(store, ctx, destination)
        first_content = first_paths[0].read_text(encoding="utf-8")
        second_paths = export_obsidian(store, ctx, destination)
        second_content = second_paths[0].read_text(encoding="utf-8")

        assert first_paths == second_paths
        assert first_content == second_content
        assert saved.item_id in first_content
        assert 'project: "project: \\"alpha\\"\\nnext: injected"' in first_content
        assert "next: injected\\npassword" not in first_content
        assert "topsecretvalue123" not in first_content
        assert "[REDACTED]" in first_content

