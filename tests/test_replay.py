import uuid
import numpy as np

from agm import Ctx, MemoryStore, Relation, WriteItem


def _snapshot(store):
    node_rows = [tuple(row) for row in store.conn.execute("SELECT * FROM nodes ORDER BY id").fetchall()]
    embedding_rows = [
        (row["node_id"], row["model_id"], row["dim"], bytes(row["vector"]))
        for row in store.conn.execute("SELECT * FROM embeddings ORDER BY node_id").fetchall()
    ]
    # Usage counters are view fields, not event source data, and must reset to replay defaults.
    return node_rows, embedding_rows


def test_replay_rebuild_is_deterministic_after_writes_supersede_delete(tmp_path):
    path = str(tmp_path / "replay.db")
    ctx = Ctx(tenant_id="t", writer_id="w", tier="tool_verified", project="p")
    with MemoryStore(path) as store:
        a = store.write(ctx, WriteItem(
            kind="fact", entity="Kite", attribute="color", value="blue",
            text="Kite is blue.", valid_from="2020-01-01T00:00:00Z",
        ))
        store.write(ctx, WriteItem(
            kind="fact", entity="Kite", attribute="color", value="red",
            text="Kite is red.", valid_from="2021-01-01T00:00:00Z",
        ))
        store.write(ctx, WriteItem(kind="episode", text="Kite flew over a field."))
        store.delete(ctx, str(a.item_id))
        before = _snapshot(store)
        store.rebuild_views()
        after = _snapshot(store)
        assert before == after


def test_replay_preserves_edges_and_alias_view_after_deleting_superseded_aliased_fact(tmp_path):
    path = str(tmp_path / "graph-replay.db")
    ctx = Ctx(tenant_id="graph-replay", writer_id="writer", tier="tool_verified", project="p")
    with MemoryStore(path) as store:
        old = store.write(ctx, WriteItem(
            kind="fact", entity="Ada Lovelace", attribute="location", value="London",
            text="Ada Lovelace lived in London.", valid_from="2020-01-01T00:00:00Z",
            relations=[Relation(rel="alias", target="Lady Lovelace")],
        ))
        new = store.write(ctx, WriteItem(
            kind="fact", entity="Ada Lovelace", attribute="location", value="Paris",
            text="Ada Lovelace lived in Paris.", valid_from="2022-01-01T00:00:00Z",
        ))
        store.delete(ctx, str(old.item_id))

        def graph_snapshot():
            return {
                "nodes": [tuple(row) for row in store.conn.execute("SELECT * FROM nodes ORDER BY id")],
                "edges": [tuple(row) for row in store.conn.execute("SELECT * FROM edges ORDER BY src, dst, type, event_id")],
                "entities": [tuple(row) for row in store.conn.execute("SELECT * FROM entities ORDER BY id")],
                "aliases": [tuple(row) for row in store.conn.execute("SELECT * FROM entity_aliases ORDER BY alias, entity_id")],
                "fts": [tuple(row) for row in store.conn.execute("SELECT node_id, text, entity, attribute, value FROM nodes_fts ORDER BY node_id")],
                "embeddings": [(row["node_id"], row["model_id"], row["dim"], bytes(row["vector"])) for row in store.conn.execute("SELECT * FROM embeddings ORDER BY node_id")],
            }

        before = graph_snapshot()
        store.rebuild_views()
        after = graph_snapshot()
        assert before == after
        assert store.conn.execute(
            "SELECT COUNT(*) FROM edges WHERE type = 'supersedes' AND dst = ?", (old.item_id,)
        ).fetchone()[0] == 0
        assert store.conn.execute("SELECT COUNT(*) FROM entity_aliases WHERE alias = ?", ("lady lovelace",)).fetchone()[0] == 0
        assert store.conn.execute("SELECT 1 FROM nodes WHERE id = ?", (new.item_id,)).fetchone() is not None


def test_replay_keeps_canonical_identity_when_alias_declaration_is_hard_deleted(tmp_path):
    path = str(tmp_path / "alias-replay.db")
    first_writer = Ctx(tenant_id="alias-replay", writer_id="first", tier="human_verified", project="p")
    second_writer = Ctx(tenant_id="alias-replay", writer_id="second", tier="tool_verified", project="p")
    with MemoryStore(path) as store:
        old = store.write(first_writer, WriteItem(
            kind="fact", entity="Ada Lovelace", attribute="location", value="London",
            text="Ada Lovelace lived in London.", valid_from="2020-01-01T00:00:00Z",
            relations=[Relation(rel="alias", target="Lady Lovelace")],
        ))
        correction = store.write(second_writer, WriteItem(
            kind="fact", entity="Lady Lovelace", attribute="location", value="Paris",
            text="Lady Lovelace lived in Paris.", valid_from="2022-01-01T00:00:00Z",
        ))
        assert correction.status == "superseded"
        assert store.delete(first_writer, str(old.item_id)).deleted

        def snapshot():
            return {
                "nodes": [tuple(row) for row in store.conn.execute("SELECT * FROM nodes ORDER BY id")],
                "edges": [tuple(row) for row in store.conn.execute("SELECT * FROM edges ORDER BY src, dst, type, event_id")],
                "entities": [tuple(row) for row in store.conn.execute("SELECT * FROM entities ORDER BY id")],
                "aliases": [tuple(row) for row in store.conn.execute("SELECT * FROM entity_aliases ORDER BY alias, entity_id")],
                "fts": [tuple(row) for row in store.conn.execute("SELECT node_id, text, entity, attribute, value FROM nodes_fts ORDER BY node_id")],
                "embeddings": [(row["node_id"], row["model_id"], row["dim"], bytes(row["vector"])) for row in store.conn.execute("SELECT * FROM embeddings ORDER BY node_id")],
            }

        before = snapshot()
        store.rebuild_views()
        after = snapshot()
        assert before == after
        node = store.conn.execute("SELECT entity_id FROM nodes WHERE id = ?", (correction.item_id,)).fetchone()
        entity = store.conn.execute("SELECT canonical FROM entities WHERE id = ?", (node["entity_id"],)).fetchone()
        assert entity["canonical"] == "ada lovelace"
        assert store.conn.execute("SELECT COUNT(*) FROM entity_aliases WHERE alias = 'lady lovelace'").fetchone()[0] == 0


def test_relation_to_alias_keeps_resolved_entity_after_alias_event_is_scrubbed(tmp_path):
    path = str(tmp_path / "relation-alias-replay.db")
    ctx = Ctx(tenant_id="relation-alias", writer_id="writer", tier="tool_verified", project="p")
    with MemoryStore(path) as store:
        alias_source = store.write(ctx, WriteItem(
            kind="fact", entity="Ada Lovelace", attribute="field", value="math",
            text="Ada Lovelace worked in mathematics.", multi_valued=True,
            relations=[Relation(rel="alias", target="Lady Lovelace")],
        ))
        linked = store.write(ctx, WriteItem(
            kind="fact", entity="Analytical Engine", attribute="designer", value="Charles Babbage",
            text="The Analytical Engine was designed by Charles Babbage.",
            relations=[Relation(rel="relates", target="Lady Lovelace")],
        ))
        assert store.delete(ctx, str(alias_source.item_id)).deleted

        def snapshot():
            return {
                "nodes": [tuple(row) for row in store.conn.execute("SELECT * FROM nodes ORDER BY id")],
                "edges": [tuple(row) for row in store.conn.execute("SELECT * FROM edges ORDER BY src, dst, type, event_id")],
                "entities": [tuple(row) for row in store.conn.execute("SELECT * FROM entities ORDER BY id")],
                "aliases": [tuple(row) for row in store.conn.execute("SELECT * FROM entity_aliases ORDER BY alias, entity_id")],
                "fts": [tuple(row) for row in store.conn.execute("SELECT node_id, text, entity, attribute, value FROM nodes_fts ORDER BY node_id")],
                "embeddings": [(row["node_id"], row["model_id"], row["dim"], bytes(row["vector"])) for row in store.conn.execute("SELECT * FROM embeddings ORDER BY node_id")],
            }

        before = snapshot()
        store.rebuild_views()
        after = snapshot()
        assert before == after
        linked_entity = store.conn.execute(
            "SELECT entity_id FROM nodes WHERE id = ?", (linked.item_id,)
        ).fetchone()["entity_id"]
        canonical = store.conn.execute(
            "SELECT canonical FROM entities WHERE id = ?", (linked_entity,)
        ).fetchone()["canonical"]
        assert canonical == "analytical engine"
        ada_id = "e_" + uuid.uuid5(uuid.NAMESPACE_URL, "relation-alias:ada lovelace").hex
        assert store.conn.execute(
            "SELECT COUNT(*) FROM edges WHERE src = ? AND dst = ? AND type = 'relates'",
            (linked_entity, ada_id),
        ).fetchone()[0] == 1
