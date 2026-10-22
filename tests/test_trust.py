from __future__ import annotations

from agm import Ctx, MemoryStore, SourceSpan, WriteItem


def test_probationary_low_trust_memory_is_hidden_from_high_stakes_until_independently_corroborated(tmp_path):
    with MemoryStore(str(tmp_path / "probation.db")) as store:
        untrusted = Ctx(tenant_id="tenant-p", writer_id="external-tool", tier="untrusted", project="ops")
        verifier = Ctx(tenant_id="tenant-p", writer_id="human-check", tier="human_verified", project="ops")
        candidate = WriteItem(
            kind="fact", entity="release", attribute="region", value="eu-west",
            text="The release region is eu-west.",
        )
        added = store.write(untrusted, candidate)
        assert added.item_id

        ordinary = store.retrieve(untrusted, "release region eu-west", entity="release", high_stakes=False)
        assert any(item.id == added.item_id for item in ordinary.items)
        for expand in (False, True):
            high_stakes_before = store.retrieve(
                untrusted, "release region eu-west", entity="release", high_stakes=True, expand=expand
            )
            assert all(item.id != added.item_id for item in high_stakes_before.items)

        confirmation = store.write(verifier, candidate.model_copy())
        assert confirmation.status == "noop"
        for expand in (False, True):
            high_stakes_after = store.retrieve(
                verifier, "release region eu-west", entity="release", high_stakes=True, expand=expand
            )
            assert any(item.id == added.item_id for item in high_stakes_after.items)


def test_revoking_corroborating_writer_withdraws_its_evidence(tmp_path):
    with MemoryStore(str(tmp_path / "revoke-corroboration.db")) as store:
        untrusted = Ctx(tenant_id="tenant-p2", writer_id="external-tool", tier="untrusted", project="ops")
        verifier = Ctx(tenant_id="tenant-p2", writer_id="human-check", tier="human_verified", project="ops")
        candidate = WriteItem(
            kind="fact", entity="database", attribute="engine", value="SQLite",
            text="Database engine is SQLite.",
        )
        added = store.write(untrusted, candidate)
        store.write(verifier, candidate.model_copy())
        assert any(
            item.id == added.item_id
            for item in store.retrieve(verifier, "database engine SQLite", high_stakes=True).items
        )

        result = store.revoke_writer(Ctx(tenant_id="tenant-p2", writer_id="admin", tier="human_verified", project="ops"), "human-check")
        assert result.revoked is True
        assert result.removed == 0
        filtered = store.retrieve(verifier, "database engine SQLite", high_stakes=True)
        assert all(item.id != added.item_id for item in filtered.items)


def test_revoke_writer_rolls_back_written_nodes_and_derived_dependents_deterministically(tmp_path):
    with MemoryStore(str(tmp_path / "revoke.db")) as store:
        bad_writer = Ctx(tenant_id="tenant-r", writer_id="bad-writer", tier="trusted_agent", project="app")
        other_writer = Ctx(tenant_id="tenant-r", writer_id="other-writer", tier="human_verified", project="app")
        admin = Ctx(tenant_id="tenant-r", writer_id="admin", tier="human_verified", project="app")
        source = store.write(bad_writer, WriteItem(kind="episode", text="Unverified deployment result."))
        assert source.item_id
        derived = store.write(other_writer, WriteItem(
            kind="procedure", entity="deploy", attribute=None, value=None,
            text="Procedure distilled from the unverified deployment result.",
            source_span=SourceSpan(episode_id=source.item_id, start=0, end=34),
        ))
        assert derived.item_id
        assert store.conn.execute(
            "SELECT 1 FROM edges WHERE src = ? AND dst = ? AND type = 'derived_from'",
            (derived.item_id, source.item_id),
        ).fetchone() is not None

        result = store.revoke_writer(admin, "bad-writer")
        assert result.revoked is True
        assert result.removed == 2
        for node_id in (source.item_id, derived.item_id):
            assert store.conn.execute("SELECT 1 FROM nodes WHERE id = ?", (node_id,)).fetchone() is None
            assert store.conn.execute("SELECT 1 FROM nodes_fts WHERE node_id = ?", (node_id,)).fetchone() is None
            assert store.conn.execute("SELECT 1 FROM embeddings WHERE node_id = ?", (node_id,)).fetchone() is None

        before_nodes = [tuple(row) for row in store.conn.execute("SELECT * FROM nodes ORDER BY id")]
        before_edges = [tuple(row) for row in store.conn.execute("SELECT * FROM edges ORDER BY src, dst, type, event_id")]
        store.rebuild_views()
        assert before_nodes == [tuple(row) for row in store.conn.execute("SELECT * FROM nodes ORDER BY id")]
        assert before_edges == [tuple(row) for row in store.conn.execute("SELECT * FROM edges ORDER BY src, dst, type, event_id")]


def test_revoke_writer_since_only_removes_writes_created_after_timestamp(tmp_path):
    with MemoryStore(str(tmp_path / "revoke-since.db")) as store:
        writer = Ctx(tenant_id="tenant-s", writer_id="writer", tier="tool_verified", project="ops")
        admin = Ctx(tenant_id="tenant-s", writer_id="admin", tier="human_verified", project="ops")
        old = store.write(writer, WriteItem(
            kind="episode", text="Keep this older event", valid_from="2020-01-01T00:00:00Z"
        ))
        new = store.write(writer, WriteItem(
            kind="episode", text="Remove this newer event", valid_from="2025-01-01T00:00:00Z"
        ))
        timestamps = {
            row["id"]: row["created_at"] for row in store.conn.execute(
                "SELECT id, created_at FROM events WHERE type = 'add'"
            )
        }
        threshold = timestamps[max(timestamps)]
        result = store.revoke_writer(admin, "writer", since=threshold)
        assert result.revoked
        assert result.removed == 1
        assert store.conn.execute("SELECT 1 FROM nodes WHERE id = ?", (old.item_id,)).fetchone() is not None
        assert store.conn.execute("SELECT 1 FROM nodes WHERE id = ?", (new.item_id,)).fetchone() is None


def test_probationary_episode_can_be_corroborated_by_same_text_from_another_writer(tmp_path):
    with MemoryStore(str(tmp_path / "probation-episode.db")) as store:
        low = Ctx(tenant_id="tenant-ep", writer_id="external", tier="untrusted", project="ops")
        reviewer = Ctx(tenant_id="tenant-ep", writer_id="reviewer", tier="human_verified", project="ops")
        text = "Deployment completed after the cache was cleared."
        added = store.write(low, WriteItem(kind="episode", text=text))
        assert added.item_id
        before = store.retrieve(low, "deployment cache cleared", high_stakes=True)
        assert all(item.id != added.item_id for item in before.items)
        store.write(reviewer, WriteItem(kind="episode", text=text))
        after = store.retrieve(reviewer, "deployment cache cleared", high_stakes=True)
        assert any(item.id == added.item_id for item in after.items)
