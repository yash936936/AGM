"""Phase 2 trust and ranking features. The coefficients are provisional (D-008)."""
from __future__ import annotations

import json
import math
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
    """Count distinct other writers affirming the same fact or exact item text."""
    if row["entity_id"] is not None and row["value"] is not None:
        matching_rows = conn.execute(
            """SELECT DISTINCT writer_id FROM nodes
               WHERE tenant = ? AND project = ? AND entity_id = ? AND attribute IS ? AND value = ?
                 AND writer_id <> ? AND status = 'active'""",
            (
                row["tenant"], row["project"], row["entity_id"], row["attribute"],
                row["value"], row["writer_id"],
            ),
        ).fetchall()
    else:
        # Episodes and procedures may not have an entity/value pair. An independent
        # writer can corroborate such an item by recording the exact same statement.
        matching_rows = conn.execute(
            """SELECT DISTINCT writer_id FROM nodes
               WHERE tenant = ? AND project = ? AND kind = ? AND text = ?
                 AND writer_id <> ? AND status = 'active'""",
            (row["tenant"], row["project"], row["kind"], row["text"], row["writer_id"]),
        ).fetchall()
    writers = {str(result["writer_id"]) for result in matching_rows}
    # Revocation events keep event history but withdraw corroboration contributed by
    # a revoked writer. The event log remains the audit trail; this set is a view rule.
    revoked_corroboration_ids: set[int] = set()
    for revoke in conn.execute(
        "SELECT payload FROM events WHERE tenant = ? AND type = 'revoke_writer'",
        (row["tenant"],),
    ).fetchall():
        try:
            payload = json.loads(revoke["payload"])
        except (TypeError, json.JSONDecodeError):
            continue
        revoked_corroboration_ids.update(
            int(value) for value in payload.get("corroboration_event_ids", [])
            if isinstance(value, int) or (isinstance(value, str) and value.isdigit())
        )

    # A same-value no-op from another writer is a content-free event. It confirms
    # a fact without making a second memory node, unless that writer was revoked.
    for event in conn.execute(
        "SELECT id, writer_id, payload FROM events WHERE tenant = ? AND type = 'corroborate'",
        (row["tenant"],),
    ).fetchall():
        if int(event["id"]) in revoked_corroboration_ids:
            continue
        if str(event["writer_id"]) == str(row["writer_id"]):
            continue
        try:
            payload = json.loads(event["payload"])
        except (TypeError, json.JSONDecodeError):
            continue
        if payload.get("node_id") == str(row["id"]):
            writers.add(str(event["writer_id"]))
    return len(writers)


def is_probationary(conn: sqlite3.Connection, row: sqlite3.Row) -> bool:
    """Return true for low-trust items not yet corroborated by an independent writer.

    Phase 4 treats trusted-agent and untrusted items as probationary for high-stakes
    queries. One independent active duplicate or corroboration event lifts probation.
    """
    if str(row["tier"]) not in {"trusted_agent", "untrusted"}:
        return False
    return independent_corroborations(conn, row) < 1


def effective_confidence(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    now: datetime | None = None,
    corroboration_count: int | None = None,
) -> float:
    """Apply the D-008 placeholder confidence formula, clipped to [0, 1]."""
    extraction_conf = float(row["confidence"])
    # Graph retrieval can batch the same evidence lookup for all candidate rows.
    # Keep the original path as the default for all existing callers.
    raw_corroborations = (
        independent_corroborations(conn, row)
        if corroboration_count is None
        else corroboration_count
    )
    corroborations = min(raw_corroborations, 3)
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


DEFAULT_ARCHIVE_THRESHOLD = 0.30


def compute_decay_weight(
    valid_from: str,
    *,
    last_used: str | None = None,
    usage_count: int = 0,
    citation_count: int = 0,
    corroboration_count: int = 0,
    pinned: bool = False,
    now: datetime | None = None,
) -> float:
    """Compute a provisional decay weight without persisting it.

    The last activity timestamp is ``last_used`` when available, otherwise
    ``valid_from``. The idle factor halves roughly each idle year; retrievals,
    incoming derived-from citations and independent corroborations add small
    bounded bonuses, and pinned memories stay at 1.0. This is a provisional,
    uncalibrated forgetting model.
    """
    if pinned:
        return 1.0
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    activity_time = _parse_time(last_used or valid_from)
    idle_days = max(0.0, (current.astimezone(timezone.utc) - activity_time).total_seconds() / 86400.0)
    idle_factor = 1.0 / (1.0 + idle_days / 365.0)
    use_bonus = min(0.12, 0.03 * math.log1p(max(0, int(usage_count))))
    citation_bonus = min(0.08, 0.04 * math.log1p(max(0, int(citation_count))))
    corroboration_bonus = min(0.10, 0.05 * max(0, min(int(corroboration_count), 2)))
    return min(1.0, max(0.0, idle_factor + use_bonus + citation_bonus + corroboration_bonus))


def lifecycle_candidates(
    conn: sqlite3.Connection,
    *,
    threshold: float = DEFAULT_ARCHIVE_THRESHOLD,
    tenant: str | None = None,
    project: str | None = None,
    now: datetime | None = None,
) -> list[dict[str, object]]:
    """Return active, unpinned nodes below the decay threshold without mutation.

    This helper is deliberately read-only. Phase 5 only reports candidates; it
    does not archive nodes or append lifecycle events.
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0.0 and 1.0")
    where = ["n.status = 'active'", "n.pinned = 0"]
    params: list[object] = []
    if tenant is not None:
        where.append("n.tenant = ?")
        params.append(tenant)
    if project is not None:
        where.append("n.project = ?")
        params.append(project)
    rows = conn.execute(
        "SELECT n.*, e.canonical AS entity FROM nodes n "
        "LEFT JOIN entities e ON e.id = n.entity_id WHERE " + " AND ".join(where) +
        " ORDER BY n.event_id ASC, n.id ASC",
        tuple(params),
    ).fetchall()
    candidates: list[dict[str, object]] = []
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    for row in rows:
        citation_count = int(conn.execute(
            "SELECT COUNT(*) FROM edges WHERE dst = ? AND type = 'derived_from'",
            (row["id"],),
        ).fetchone()[0])
        corroboration_count = independent_corroborations(conn, row)
        weight = compute_decay_weight(
            str(row["valid_from"]),
            last_used=str(row["last_used"]) if row["last_used"] else None,
            usage_count=int(row["usage_count"]),
            citation_count=citation_count,
            corroboration_count=corroboration_count,
            pinned=bool(row["pinned"]),
            now=current,
        )
        if weight >= threshold:
            continue
        activity = _parse_time(str(row["last_used"] or row["valid_from"]))
        idle_days = max(0.0, (current.astimezone(timezone.utc) - activity).total_seconds() / 86400.0)
        candidates.append({
            "id": str(row["id"]),
            "tenant": str(row["tenant"]),
            "project": str(row["project"]),
            "kind": str(row["kind"]),
            "entity": str(row["entity"]) if row["entity"] is not None else None,
            "usage_count": int(row["usage_count"]),
            "citation_count": citation_count,
            "corroboration_count": corroboration_count,
            "idle_days": round(idle_days, 1),
            "decay_weight": round(weight, 4),
            "threshold": float(threshold),
        })
    return candidates
