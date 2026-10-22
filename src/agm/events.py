"""Append-only event log and deterministic replay helpers."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any
import sqlite3


class HybridLogicalClock:
    def __init__(self, writer_id: str):
        self.writer_id = writer_id
        self._last_wall_ms = -1
        self._counter = 0

    def tick(self, wall_ms: int | None = None) -> str:
        now = int(time.time() * 1000) if wall_ms is None else int(wall_ms)
        if now > self._last_wall_ms:
            self._last_wall_ms = now
            self._counter = 0
        else:
            self._counter += 1
        return f"{self._last_wall_ms:013d}-{self._counter:05d}-{self.writer_id}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def append_event(
    conn: sqlite3.Connection,
    clock: HybridLogicalClock,
    *,
    tenant: str,
    writer_id: str,
    tier: str,
    idem_key: str | None,
    base_version: int | None,
    event_type: str,
    payload: dict[str, Any],
    created_at: str | None = None,
) -> tuple[int, bool]:
    """Append an event. Returns (event id, inserted); idem hits return the original id."""
    if idem_key is not None:
        row = conn.execute(
            "SELECT id FROM events WHERE tenant = ? AND writer_id = ? AND idem_key = ?",
            (tenant, writer_id, idem_key),
        ).fetchone()
        if row is not None:
            return int(row["id"]), False
    cur = conn.execute(
        """INSERT INTO events
           (tenant, writer_id, tier, hlc, idem_key, base_version, type, payload, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            tenant, writer_id, tier, clock.tick(), idem_key, base_version,
            event_type, json.dumps(payload, sort_keys=True, separators=(",", ":")),
            created_at or utc_now(),
        ),
    )
    return int(cur.lastrowid), True


def decode_payload(row: sqlite3.Row) -> dict[str, Any]:
    try:
        payload = json.loads(row["payload"])
    except (TypeError, json.JSONDecodeError):
        return {"scrubbed": True}
    return payload if isinstance(payload, dict) else {"scrubbed": True}
