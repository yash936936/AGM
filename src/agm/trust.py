"""Phase 2 trust and ranking features. The coefficients are provisional (D-008)."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

TIER_WEIGHTS: dict[str, float] = {
    "human_verified": 1.0,
    "tool_verified": 0.85,
    "trusted_agent": 0.6,
    "untrusted": 0.3,
}


def tier_weight(tier: str) -> float:
    """Return the fixed D-008 weight for a writer trust tier."""
    return TIER_WEIGHTS.get(tier, TIER_WEIGHTS["untrusted"])


def _parse_time(value: str) -> datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def age_factor(valid_from: str, *, now: datetime | None = None) -> float:
    """Uncalibrated age factor: 1 / (1 + age-in-days / 3650)."""
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    age_days = max(0.0, (current.astimezone(timezone.utc) - _parse_time(valid_from)).total_seconds() / 86400.0)
    return 1.0 / (1.0 + age_days / 3650.0)


def recency_score(valid_from: str, *, now: datetime | None = None) -> float:
    """Use the same transparent provisional decay as the confidence age factor."""
    return age_factor(valid_from, now=now)


def independent_corroborations(conn: sqlite3.Connection, row: sqlite3.Row) -> int:
    """Count distinct other writers affirming this entity/attribute/value or node."""
    if row["entity_id"] is None or row["value"] is None:
        return 0
    writers = {
        str(result["writer_id"])
        for result in conn.execute(
            """SELECT DISTINCT writer_id FROM nodes
               WHERE tenant = ? AND project = ? AND entity_id = ? AND attribute IS ? AND value = ?
                 AND writer_id <> ? AND status = 'active'""",
            (
                row["tenant"], row["project"], row["entity_id"], row["attribute"],
                row["value"], row["writer_id"],
            ),
        ).fetchall()
    }
    # A same-value no-op from another writer is represented as a content-free event,
    # so the confirmation increases confidence without creating a duplicate memory node.
    for event in conn.execute(
        "SELECT writer_id, payload FROM events WHERE tenant = ? AND type = 'corroborate'",
        (row["tenant"],),
    ).fetchall():
        if str(event["writer_id"]) == str(row["writer_id"]):
            continue
        try:
            payload = json.loads(event["payload"])
        except (TypeError, json.JSONDecodeError):
            continue
        if payload.get("node_id") == str(row["id"]):
            writers.add(str(event["writer_id"]))
    return len(writers)


def effective_confidence(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    now: datetime | None = None,
) -> float:
    """Apply the D-008 placeholder confidence formula, clipped to [0, 1]."""
    extraction_conf = float(row["confidence"])
    corroborations = min(independent_corroborations(conn, row), 3)
    result = (
        extraction_conf
        * tier_weight(str(row["tier"]))
        * (1.0 + 0.15 * corroborations)
        * age_factor(str(row["valid_from"]), now=now)
    )
    return min(1.0, max(0.0, result))


def rank_score(
    *,
    similarity: float,
    confidence: float,
    trust: float,
    recency: float,
    decay_weight: float,
) -> float:
    """Return the provisional D-008 weighted rank, normalized to [0, 1]."""
    score = (
        0.55 * similarity
        + 0.15 * confidence
        + 0.10 * trust
        + 0.10 * recency
        + 0.10 * decay_weight
    )
    return min(1.0, max(0.0, score))
