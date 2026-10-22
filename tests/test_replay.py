import numpy as np

from agm import Ctx, MemoryStore, WriteItem


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
