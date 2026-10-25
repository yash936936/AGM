from __future__ import annotations

from agm import Ctx, MemoryStore, WriteItem


def _ctx() -> Ctx:
    return Ctx(
        tenant_id="m1-acceptance-tenant",
        writer_id="m1-acceptance-writer",
        tier="human_verified",
        project="m1-acceptance-project",
    )


def test_cross_session_recall_correction_delete_and_rebuild(tmp_path):
    """Core M1 lifecycle facts survive reopen, while deleted facts stay deleted."""
    db = tmp_path / "m1-cross-session.db"
    ctx = _ctx()
    old_marker = "M1-OLD-EMPLOYER-81"
    current_marker = "M1-CURRENT-EMPLOYER-92"

    with MemoryStore(str(db)) as store:
        old = store.write(ctx, WriteItem(
            kind="fact",
            entity="M1 Acceptance Person",
            attribute="employer",
            value=old_marker,
            text=f"M1 Acceptance Person worked at {old_marker}.",
            valid_from="2020-01-01T00:00:00Z",
        ))
        current = store.write(ctx, WriteItem(
            kind="fact",
            entity="M1 Acceptance Person",
            attribute="employer",
            value=current_marker,
            text=f"M1 Acceptance Person now works at {current_marker}.",
            valid_from="2021-01-01T00:00:00Z",
        ))

    # A new MemoryStore instance represents a fresh process/session.
    with MemoryStore(str(db)) as fresh_session:
        fresh_session.rebuild_views()
        current_result = fresh_session.retrieve(
            ctx, "M1 Acceptance Person employer", entity="M1 Acceptance Person",
        )
        history_result = fresh_session.retrieve(
            ctx, "M1 Acceptance Person employer",
            entity="M1 Acceptance Person", include_superseded=True,
        )
        assert [node.id for node in current_result.items] == [current.item_id]
        assert {node.id for node in history_result.items} == {old.item_id, current.item_id}

        # Delete both versions so the previous value cannot be restored as current.
        assert fresh_session.delete(ctx, old.item_id).deleted
        assert fresh_session.delete(ctx, current.item_id).deleted
        fresh_session.rebuild_views()

    with MemoryStore(str(db)) as reopened:
        reopened.rebuild_views()
        for include_superseded in (False, True):
            result = reopened.retrieve(
                ctx, "M1 Acceptance Person employer",
                entity="M1 Acceptance Person",
                include_superseded=include_superseded,
            )
            assert not result.items
        event_payloads = " ".join(
            str(row[0]) for row in reopened.conn.execute("SELECT payload FROM events")
        )
        assert old_marker not in event_payloads
        assert current_marker not in event_payloads
