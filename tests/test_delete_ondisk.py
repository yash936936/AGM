"""Deleted or revoked content must not remain readable in the database or WAL files (D-022)."""
from __future__ import annotations

from pathlib import Path

from agm.models import Ctx, WriteItem
from agm.store import MemoryStore


def _disk_bytes(db: Path) -> bytes:
    data = b""
    for suffix in ("", "-wal"):
        path = Path(str(db) + suffix)
        if path.exists():
            data += path.read_bytes()
    return data


def test_deleted_marker_is_gone_from_disk_while_store_is_open(tmp_path):
    db = tmp_path / "d.db"
    ctx = Ctx(tenant_id="t", writer_id="w1", tier="trusted_agent")
    marker = "ZEBRAQUARTZ-MARKER-7731"
    with MemoryStore(str(db)) as store:
        item = store.write(ctx, WriteItem(
            kind="fact", entity="proj", attribute="codename", value=marker, text=f"codename {marker}",
        ))
        store.delete(ctx, item.item_id)
        assert marker.encode() not in _disk_bytes(db)
    assert marker.encode() not in _disk_bytes(db)


def test_revoke_clears_views_but_keeps_events_for_audit(tmp_path):
    """Revocation is rollback, not purge: derived views are cleared, the event log is kept for audit.

    Use delete() for a hard purge of specific content (see test above).
    """
    db = tmp_path / "r.db"
    good = Ctx(tenant_id="t", writer_id="good", tier="trusted_agent")
    bad = Ctx(tenant_id="t", writer_id="bad", tier="untrusted")
    admin = Ctx(tenant_id="t", writer_id="admin", tier="human_verified")
    marker = "OCELOTBASALT-MARKER-5520"
    with MemoryStore(str(db)) as store:
        store.write(good, WriteItem(kind="episode", text="harmless note"))
        store.write(bad, WriteItem(kind="episode", text=f"poisoned {marker}"))
        result = store.revoke_writer(admin, "bad")
        assert result.revoked and result.removed == 1
        for table in ("nodes", "nodes_fts"):
            rows = store.conn.execute(f"SELECT * FROM {table}").fetchall()  # constant table names
            assert marker not in " ".join(str(v) for row in rows for v in row)
        events = " ".join(str(r[0]) for r in store.conn.execute("SELECT payload FROM events"))
        assert marker in events  # intentional: audit trail survives revocation
        hits = store.retrieve(good, "poisoned marker note")
        assert all(marker not in (i.text or "") for i in hits.items)
