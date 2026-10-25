from __future__ import annotations

import json

import pytest

from agm import Ctx, ExpiryResult, MemoryStore, WriteItem


CUTOFF = "2025-01-01T00:00:00Z"
OLD_CREATED_AT = "2020-01-01T00:00:00Z"
NEW_CREATED_AT = "2026-01-01T00:00:00Z"


def _ctx(tenant="retention-tenant", project="project-a", writer="writer-a"):
    return Ctx(
        tenant_id=tenant,
        writer_id=writer,
        tier="human_verified",
        project=project,
    )


def _backdate_event(store: MemoryStore, item_id: str, created_at: str) -> None:
    row = store.conn.execute(
        "SELECT event_id FROM nodes WHERE id = ?", (item_id,)
    ).fetchone()
    assert row is not None
    store.conn.execute(
        "UPDATE events SET created_at = ? WHERE id = ?",
        (created_at, int(row["event_id"])),
    )
    store.conn.commit()


def test_expire_before_purges_old_items_skips_pinned_and_preserves_new_items(tmp_path):
    db = tmp_path / "retention.db"
    ctx = _ctx()
    with MemoryStore(str(db)) as store:
        old = store.write(ctx, WriteItem(
            kind="episode",
            text="Retention synthetic expired marker RETENTION-OLD-7E31",
        ))
        pinned = store.write(ctx, WriteItem(
            kind="episode",
            text="Retention pinned marker RETENTION-PINNED-81A2",
            pin=True,
        ))
        new = store.write(ctx, WriteItem(
            kind="episode",
            text="Retention fresh marker RETENTION-NEW-29B4",
        ))
        _backdate_event(store, old.item_id, OLD_CREATED_AT)
        _backdate_event(store, pinned.item_id, OLD_CREATED_AT)
        _backdate_event(store, new.item_id, NEW_CREATED_AT)

        result = store.expire_before(ctx, CUTOFF)
        assert isinstance(result, ExpiryResult)
        assert result.scanned_nodes == 3
        assert result.expired_ids == [old.item_id]
        assert result.skipped_pinned_ids == [pinned.item_id]
        assert result.scrubbed_orphan_events == 0

        old_payload = store.conn.execute(
            "SELECT payload FROM events WHERE id = (SELECT event_id FROM nodes WHERE id = ?)",
            (old.item_id,),
        ).fetchone()
        assert old_payload is None  # the deleted node is no longer materialized
        event_payloads = " ".join(
            str(row[0]) for row in store.conn.execute("SELECT payload FROM events")
        )
        assert "RETENTION-OLD-7E31" not in event_payloads
        assert "RETENTION-PINNED-81A2" in event_payloads
        assert "RETENTION-NEW-29B4" in event_payloads

        store.rebuild_views()
        rows = store.conn.execute("SELECT id, text FROM nodes").fetchall()
        texts = {str(row["text"]) for row in rows}
        assert not any("RETENTION-OLD-7E31" in text for text in texts)
        assert any("RETENTION-PINNED-81A2" in text for text in texts)
        assert any("RETENTION-NEW-29B4" in text for text in texts)


def test_expire_before_is_tenant_and_project_scoped(tmp_path):
    db = tmp_path / "retention-scope.db"
    local = _ctx()
    foreign_tenant = _ctx(tenant="another-tenant")
    foreign_project = _ctx(project="project-b")
    with MemoryStore(str(db)) as store:
        local_item = store.write(local, WriteItem(
            kind="episode", text="Local expired marker LOCAL-RETENTION-77"
        ))
        tenant_item = store.write(foreign_tenant, WriteItem(
            kind="episode", text="Foreign tenant marker FOREIGN-TENANT-RETENTION-22"
        ))
        project_item = store.write(foreign_project, WriteItem(
            kind="episode", text="Foreign project marker FOREIGN-PROJECT-RETENTION-33"
        ))
        _backdate_event(store, local_item.item_id, OLD_CREATED_AT)
        _backdate_event(store, tenant_item.item_id, OLD_CREATED_AT)
        _backdate_event(store, project_item.item_id, OLD_CREATED_AT)

        result = store.expire_before(local, CUTOFF)
        assert result.expired_ids == [local_item.item_id]
        assert store.conn.execute("SELECT 1 FROM nodes WHERE id = ?", (tenant_item.item_id,)).fetchone()
        assert store.conn.execute("SELECT 1 FROM nodes WHERE id = ?", (project_item.item_id,)).fetchone()


def test_expire_before_scrubs_aged_revoked_source_payload_but_keeps_revoke_audit(tmp_path):
    db = tmp_path / "retention-revoked.db"
    writer = _ctx(writer="writer-to-revoke")
    admin = _ctx(writer="retention-admin")
    with MemoryStore(str(db)) as store:
        item = store.write(writer, WriteItem(
            kind="episode",
            text="Revoked audit marker REVOKED-RETENTION-4C10",
        ))
        _backdate_event(store, item.item_id, OLD_CREATED_AT)
        revoke = store.revoke_writer(admin, writer.writer_id)
        assert revoke.revoked
        assert store.conn.execute(
            "SELECT 1 FROM nodes WHERE id = ?", (item.item_id,)
        ).fetchone() is None
        before = store.conn.execute(
            "SELECT payload FROM events WHERE type = 'add' AND writer_id = ?",
            (writer.writer_id,),
        ).fetchone()
        assert before is not None and "REVOKED-RETENTION-4C10" in before["payload"]

        result = store.expire_before(admin, CUTOFF)
        assert result.expired_ids == []
        assert result.scrubbed_orphan_events >= 1
        payloads = " ".join(str(row[0]) for row in store.conn.execute("SELECT payload FROM events"))
        assert "REVOKED-RETENTION-4C10" not in payloads
        assert store.conn.execute(
            "SELECT COUNT(*) FROM events WHERE type = 'revoke_writer'"
        ).fetchone()[0] == 1

        store.rebuild_views()
        assert store.conn.execute(
            "SELECT 1 FROM nodes WHERE id = ?", (item.item_id,)
        ).fetchone() is None
        assert "REVOKED-RETENTION-4C10" not in " ".join(
            str(row[0]) for row in store.conn.execute("SELECT payload FROM events")
        )


def test_expire_before_can_include_pinned_memories_explicitly(tmp_path):
    db = tmp_path / "retention-pinned.db"
    ctx = _ctx()
    with MemoryStore(str(db)) as store:
        item = store.write(ctx, WriteItem(
            kind="episode", text="Pinned explicit expiry marker PINNED-EXPIRY-090"
            , pin=True,
        ))
        _backdate_event(store, item.item_id, OLD_CREATED_AT)
        result = store.expire_before(ctx, CUTOFF, include_pinned=True)
        assert result.expired_ids == [item.item_id]
        assert result.skipped_pinned_ids == []


@pytest.mark.parametrize("cutoff", ["not-a-date", "", "2025-01-01T00:00:00+99:99"])
def test_expire_before_rejects_invalid_cutoff(tmp_path, cutoff):
    with MemoryStore(str(tmp_path / "invalid-cutoff.db")) as store:
        with pytest.raises(ValueError, match="cutoff"):
            store.expire_before(_ctx(), cutoff)


def test_expire_before_rejects_non_boolean_pinned_policy(tmp_path):
    with MemoryStore(str(tmp_path / "invalid-pinned.db")) as store:
        with pytest.raises(ValueError, match="include_pinned"):
            store.expire_before(_ctx(), CUTOFF, include_pinned=1)

def test_expire_before_is_idempotent(tmp_path):
    db = tmp_path / "retention-idempotent.db"
    ctx = _ctx()

    with MemoryStore(str(db)) as store:
        item = store.write(ctx, WriteItem(
            kind="episode",
            text="Idempotent expiry marker IDEMPOTENT-EXPIRY-123",
        ))
        _backdate_event(store, item.item_id, OLD_CREATED_AT)

        first = store.expire_before(ctx, CUTOFF)
        assert item.item_id in first.expired_ids

        second = store.expire_before(ctx, CUTOFF)
        assert second.expired_ids == []
        assert store.conn.execute(
            "SELECT 1 FROM nodes WHERE id = ?", (item.item_id,)
        ).fetchone() is None

        store.rebuild_views()
        assert store.conn.execute(
            "SELECT 1 FROM nodes WHERE id = ?", (item.item_id,)
        ).fetchone() is None


def test_expire_before_includes_exact_cutoff(tmp_path):
    db = tmp_path / "retention-boundary.db"
    ctx = _ctx()

    with MemoryStore(str(db)) as store:
        item = store.write(ctx, WriteItem(
            kind="episode",
            text="Exact cutoff expiry marker EXACT-CUTOFF-456",
        ))
        _backdate_event(store, item.item_id, CUTOFF)

        result = store.expire_before(ctx, CUTOFF)

        assert item.item_id in result.expired_ids
        assert store.conn.execute(
            "SELECT 1 FROM nodes WHERE id = ?", (item.item_id,)
        ).fetchone() is None

def test_expire_before_rolls_back_entire_sweep_on_failure(tmp_path, monkeypatch):
    db = tmp_path / "retention-rollback.db"
    ctx = _ctx()

    with MemoryStore(str(db)) as store:
        first = store.write(ctx, WriteItem(
            kind="episode", text="Rollback marker FIRST-RETENTION-101"
        ))
        second = store.write(ctx, WriteItem(
            kind="episode", text="Rollback marker SECOND-RETENTION-202"
        ))
        _backdate_event(store, first.item_id, OLD_CREATED_AT)
        _backdate_event(store, second.item_id, OLD_CREATED_AT)

        def snapshot():
            return {
                table: [
                    tuple(row)
                    for row in store.conn.execute(
                        f"SELECT * FROM {table} ORDER BY 1"
                    ).fetchall()
                ]
                for table in ("events", "nodes", "nodes_fts", "embeddings", "edges")
            }

        before = snapshot()
        original_delete = store.delete
        calls = 0

        def fail_on_second_delete(call_ctx, item_id):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("injected expiry failure")
            return original_delete(call_ctx, item_id)

        monkeypatch.setattr(store, "delete", fail_on_second_delete)

        with pytest.raises(RuntimeError, match="injected expiry failure"):
            store.expire_before(ctx, CUTOFF)

        assert calls == 2
        assert snapshot() == before

def test_expire_before_scrubs_orphan_events_only_in_current_tenant_and_project(tmp_path):
    db = tmp_path / "retention-orphan-scope.db"
    local = _ctx(tenant="scope-tenant", project="project-a", writer="local-writer")
    other_project = _ctx(tenant="scope-tenant", project="project-b", writer="project-writer")
    other_tenant = _ctx(tenant="other-tenant", project="project-a", writer="tenant-writer")
    local_admin = _ctx(tenant="scope-tenant", project="project-a", writer="local-admin")
    project_admin = _ctx(tenant="scope-tenant", project="project-b", writer="project-admin")
    tenant_admin = _ctx(tenant="other-tenant", project="project-a", writer="tenant-admin")

    with MemoryStore(str(db)) as store:
        local_item = store.write(local, WriteItem(
            kind="episode", text="Local orphan payload LOCAL-ORPHAN-RETENTION-711"
        ))
        project_item = store.write(other_project, WriteItem(
            kind="episode", text="Other project payload PROJECT-ORPHAN-RETENTION-822"
        ))
        tenant_item = store.write(other_tenant, WriteItem(
            kind="episode", text="Other tenant payload TENANT-ORPHAN-RETENTION-933"
        ))
        for item in (local_item, project_item, tenant_item):
            _backdate_event(store, item.item_id, OLD_CREATED_AT)

        assert store.revoke_writer(local_admin, local.writer_id).revoked
        assert store.revoke_writer(project_admin, other_project.writer_id).revoked
        assert store.revoke_writer(tenant_admin, other_tenant.writer_id).revoked

        result = store.expire_before(local_admin, CUTOFF)
        assert result.expired_ids == []
        assert result.scrubbed_orphan_events >= 1

        payloads_by_marker = {}
        for marker in (
            "LOCAL-ORPHAN-RETENTION-711",
            "PROJECT-ORPHAN-RETENTION-822",
            "TENANT-ORPHAN-RETENTION-933",
        ):
            payloads_by_marker[marker] = any(
                marker in str(row["payload"])
                for row in store.conn.execute("SELECT payload FROM events")
            )

        assert payloads_by_marker["LOCAL-ORPHAN-RETENTION-711"] is False
        assert payloads_by_marker["PROJECT-ORPHAN-RETENTION-822"] is True
        assert payloads_by_marker["TENANT-ORPHAN-RETENTION-933"] is True

        store.rebuild_views()
        assert store.conn.execute(
            "SELECT 1 FROM nodes WHERE id IN (?, ?, ?)",
            (local_item.item_id, project_item.item_id, tenant_item.item_id),
        ).fetchone() is None
        payloads_after_rebuild = " ".join(
            str(row["payload"]) for row in store.conn.execute("SELECT payload FROM events")
        )
        assert "LOCAL-ORPHAN-RETENTION-711" not in payloads_after_rebuild
        assert "PROJECT-ORPHAN-RETENTION-822" in payloads_after_rebuild
        assert "TENANT-ORPHAN-RETENTION-933" in payloads_after_rebuild

def test_expiry_preserves_revoked_pinned_source_until_explicit_opt_in(tmp_path):
    db = tmp_path / "retention-revoked-pinned.db"
    writer = _ctx(writer="pinned-writer")
    admin = _ctx(writer="retention-admin")
    marker = "REVOKED-PINNED-RETENTION-AB91"

    with MemoryStore(str(db)) as store:
        item = store.write(writer, WriteItem(
            kind="episode", text=f"Pinned source marker {marker}", pin=True,
        ))
        _backdate_event(store, item.item_id, OLD_CREATED_AT)
        assert store.revoke_writer(admin, writer.writer_id).revoked
        assert store.conn.execute(
            "SELECT 1 FROM nodes WHERE id = ?", (item.item_id,)
        ).fetchone() is None

        default_sweep = store.expire_before(admin, CUTOFF)
        assert default_sweep.scrubbed_orphan_events == 0
        payloads = " ".join(
            str(row[0]) for row in store.conn.execute("SELECT payload FROM events")
        )
        assert marker in payloads

        store.rebuild_views()
        assert store.conn.execute(
            "SELECT 1 FROM nodes WHERE id = ?", (item.item_id,)
        ).fetchone() is None
        assert marker in " ".join(
            str(row[0]) for row in store.conn.execute("SELECT payload FROM events")
        )

        opted_in_sweep = store.expire_before(admin, CUTOFF, include_pinned=True)
        assert opted_in_sweep.scrubbed_orphan_events >= 1
        assert marker not in " ".join(
            str(row[0]) for row in store.conn.execute("SELECT payload FROM events")
        )

