"""Memory Doctor: integrity checks and privacy-aware retrieval tracing.

This module is deliberately dependency-light and does not print. Callers decide
where diagnostic JSONL records are written and how summaries are displayed.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import statistics
import time
import uuid
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from .events import utc_now
from .guard import _redact_text
from .models import Ctx, RetrieveResult
from .store import MemoryStore, _iso_key

_SCHEMA_VERSION = 1


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _safe_text(value: str, *, limit: int = 1600) -> str:
    clean, _ = _redact_text(value)
    return clean[:limit]


def _sql_template(sql: str) -> str:
    """Return a statement shape without bound/literal values for privacy-safe logs."""
    normalized = re.sub(r"'(?:''|[^'])*'", "'?'", sql)
    normalized = re.sub(r'"(?:""|[^"])*"', '"?"', normalized)
    normalized = re.sub(r"\b\d+(?:\.\d+)?\b", "?", normalized)
    return " ".join(normalized.split())[:240]


class SQLTrace:
    """Collect SQLite statement counts and normalized templates for one operation."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.operation_counts: Counter[str] = Counter()
        self.template_counts: Counter[str] = Counter()
        self.statement_count = 0

    def _callback(self, sql: str) -> None:
        self.statement_count += 1
        template = _sql_template(sql)
        self.template_counts[template] += 1
        match = re.match(r"\s*([A-Za-z]+)", template)
        operation = match.group(1).upper() if match else "OTHER"
        self.operation_counts[operation] += 1

    def __enter__(self) -> "SQLTrace":
        self.conn.set_trace_callback(self._callback)
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.conn.set_trace_callback(None)

    def report(self) -> dict[str, Any]:
        return {
            "statement_count": self.statement_count,
            "operations": dict(sorted(self.operation_counts.items())),
            "templates": [
                {"count": count, "sql_shape": shape}
                for shape, count in self.template_counts.most_common(30)
            ],
        }


def append_jsonl(path: str | Path, record: dict[str, Any]) -> None:
    """Append one JSON event. Parent directories are created if needed."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True, default=str) + "\n")


def _scoped_counts(store: MemoryStore, ctx: Ctx) -> dict[str, Any]:
    conn = store.conn
    counts = {
        "nodes_by_status": {
            str(row["status"]): int(row["n"])
            for row in conn.execute(
                "SELECT status, COUNT(*) AS n FROM nodes WHERE tenant = ? AND project = ? GROUP BY status",
                (ctx.tenant_id, ctx.project),
            ).fetchall()
        },
        "nodes_by_kind": {
            str(row["kind"]): int(row["n"])
            for row in conn.execute(
                "SELECT kind, COUNT(*) AS n FROM nodes WHERE tenant = ? AND project = ? GROUP BY kind",
                (ctx.tenant_id, ctx.project),
            ).fetchall()
        },
        "events_by_type": {
            str(row["type"]): int(row["n"])
            for row in conn.execute(
                "SELECT type, COUNT(*) AS n FROM events WHERE tenant = ? GROUP BY type",
                (ctx.tenant_id,),
            ).fetchall()
        },
        "entities": int(conn.execute(
            "SELECT COUNT(*) FROM entities WHERE tenant = ?", (ctx.tenant_id,)
        ).fetchone()[0]),
        "aliases": int(conn.execute(
            """SELECT COUNT(*) FROM entity_aliases ea JOIN entities e ON e.id = ea.entity_id
               WHERE e.tenant = ?""", (ctx.tenant_id,)
        ).fetchone()[0]),
        "edges_touching_scope": int(conn.execute(
            """SELECT COUNT(*) FROM edges e
               WHERE EXISTS (SELECT 1 FROM nodes n WHERE n.id = e.src AND n.tenant = ? AND n.project = ?)
                  OR EXISTS (SELECT 1 FROM nodes n WHERE n.id = e.dst AND n.tenant = ? AND n.project = ?)
                  OR EXISTS (SELECT 1 FROM entities ent WHERE ent.id = e.src AND ent.tenant = ?)
                  OR EXISTS (SELECT 1 FROM entities ent WHERE ent.id = e.dst AND ent.tenant = ?)""",
            (ctx.tenant_id, ctx.project, ctx.tenant_id, ctx.project, ctx.tenant_id, ctx.tenant_id),
        ).fetchone()[0]),
    }
    return counts


def _diagnostic_findings(store: MemoryStore, ctx: Ctx) -> list[dict[str, str]]:
    conn = store.conn
    findings: list[dict[str, str]] = []

    def count(sql: str, params: tuple[Any, ...] = ()) -> int:
        return int(conn.execute(sql, params).fetchone()[0])

    node_scope = (ctx.tenant_id, ctx.project)
    integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
    if integrity.lower() != "ok":
        findings.append({"severity": "ERROR", "code": "SQLITE_INTEGRITY", "message": integrity})

    checks = [
        (
            "MISSING_EMBEDDING", "ERROR",
            "SELECT COUNT(*) FROM nodes n LEFT JOIN embeddings e ON e.node_id = n.id WHERE n.tenant = ? AND n.project = ? AND e.node_id IS NULL",
            "One or more memory nodes have no embedding; vector retrieval may silently miss them.",
        ),
        (
            "MISSING_FTS", "ERROR",
            "SELECT COUNT(*) FROM nodes n LEFT JOIN nodes_fts f ON f.node_id = n.id WHERE n.tenant = ? AND n.project = ? AND f.node_id IS NULL",
            "One or more memory nodes have no full-text index row.",
        ),
        (
            "ORPHAN_EMBEDDING", "WARNING",
            "SELECT COUNT(*) FROM embeddings e LEFT JOIN nodes n ON n.id = e.node_id WHERE n.id IS NULL",
            "Embedding rows exist without corresponding memory nodes.",
        ),
        (
            "ORPHAN_FTS", "WARNING",
            "SELECT COUNT(*) FROM nodes_fts f LEFT JOIN nodes n ON n.id = f.node_id WHERE n.id IS NULL",
            "Full-text rows exist without corresponding memory nodes.",
        ),
        (
            "ACTIVE_WITH_VALID_TO", "ERROR",
            "SELECT COUNT(*) FROM nodes WHERE tenant = ? AND project = ? AND status = 'active' AND valid_to IS NOT NULL",
            "Active nodes have a valid_to timestamp; check correction replay and temporal validity.",
        ),
        (
            "SUPERSEDED_WITHOUT_VALID_TO", "WARNING",
            "SELECT COUNT(*) FROM nodes WHERE tenant = ? AND project = ? AND status = 'superseded' AND valid_to IS NULL",
            "Superseded nodes lack a valid_to timestamp, so historical queries may have ambiguous intervals.",
        ),
        (
            "DUPLICATE_ACTIVE_FACTS", "WARNING",
            "SELECT COUNT(*) FROM (SELECT entity_id, attribute FROM nodes WHERE tenant = ? AND project = ? AND kind = 'fact' AND status = 'active' AND entity_id IS NOT NULL AND attribute IS NOT NULL GROUP BY entity_id, attribute HAVING COUNT(*) > 1)",
            "Multiple active rows share an entity/attribute key; inspect intended multi-value behavior or missed supersession.",
        ),
        (
            "AMBIGUOUS_ALIASES", "WARNING",
            "SELECT COUNT(*) FROM (SELECT ea.alias FROM entity_aliases ea JOIN entities e ON e.id = ea.entity_id WHERE e.tenant = ? GROUP BY ea.alias HAVING COUNT(DISTINCT ea.entity_id) > 1)",
            "An alias maps to more than one entity; alias lookup may need a canonical name.",
        ),
    ]
    for code, severity, sql, message in checks:
        params = node_scope if code not in {"ORPHAN_EMBEDDING", "ORPHAN_FTS", "AMBIGUOUS_ALIASES"} else ((ctx.tenant_id,) if code == "AMBIGUOUS_ALIASES" else ())
        value = count(sql, params)
        if value:
            findings.append({"severity": severity, "code": code, "message": f"{message} Count: {value}."})

    # Only flag broken edges that touch this diagnostic scope. An endpoint may be
    # another valid tenant's node/entity; it is not an orphan merely because it is
    # outside this scope. Endpoint existence is checked globally because `edges`
    # does not carry tenant/project columns of its own.
    orphan_edges = count(
        """SELECT COUNT(*) FROM edges e WHERE
           (EXISTS (SELECT 1 FROM nodes sn WHERE sn.id = e.src AND sn.tenant = ? AND sn.project = ?)
            OR EXISTS (SELECT 1 FROM nodes dn WHERE dn.id = e.dst AND dn.tenant = ? AND dn.project = ?)
            OR EXISTS (SELECT 1 FROM entities se WHERE se.id = e.src AND se.tenant = ?)
            OR EXISTS (SELECT 1 FROM entities de WHERE de.id = e.dst AND de.tenant = ?))
           AND
           ((NOT EXISTS (SELECT 1 FROM nodes n WHERE n.id = e.src)
             AND NOT EXISTS (SELECT 1 FROM entities ent WHERE ent.id = e.src))
            OR
            (NOT EXISTS (SELECT 1 FROM nodes n WHERE n.id = e.dst)
             AND NOT EXISTS (SELECT 1 FROM entities ent WHERE ent.id = e.dst)))""",
        (ctx.tenant_id, ctx.project, ctx.tenant_id, ctx.project, ctx.tenant_id, ctx.tenant_id),
    )
    if orphan_edges:
        findings.append({
            "severity": "ERROR", "code": "ORPHAN_GRAPH_EDGES",
            "message": f"Graph contains {orphan_edges} edge endpoint(s) that do not resolve to a scoped node or entity.",
        })

    # Check interval overlap across fact versions. Open-ended active rows are
    # expected; only intersecting intervals for the same entity/attribute warn.
    versions = conn.execute(
        """SELECT entity_id, attribute, id, valid_from, valid_to, status
           FROM nodes WHERE tenant = ? AND project = ? AND kind = 'fact'
             AND entity_id IS NOT NULL AND attribute IS NOT NULL
             AND status IN ('active', 'superseded')
           ORDER BY entity_id, attribute, valid_from, id""",
        node_scope,
    ).fetchall()
    grouped: dict[tuple[str, str], list[sqlite3.Row]] = {}
    for row in versions:
        grouped.setdefault((str(row["entity_id"]), str(row["attribute"])), []).append(row)
    overlap_count = 0
    for rows in grouped.values():
        intervals = []
        for row in rows:
            try:
                start = _iso_key(str(row["valid_from"]))
                end = _iso_key(str(row["valid_to"])) if row["valid_to"] else None
            except (TypeError, ValueError):
                continue
            intervals.append((start, end, str(row["id"])))
        for index, (start, end, _) in enumerate(intervals):
            for next_start, next_end, _ in intervals[index + 1:]:
                if end is not None and next_start >= end:
                    break
                if end is None or next_start < end:
                    if next_end is None or next_start < next_end:
                        overlap_count += 1
                        break
    if overlap_count:
        findings.append({
            "severity": "WARNING", "code": "OVERLAPPING_TEMPORAL_INTERVALS",
            "message": f"Found {overlap_count} entity/attribute version groups with overlapping valid-time intervals.",
        })

    quarantined = count(
        "SELECT COUNT(*) FROM nodes WHERE tenant = ? AND project = ? AND status = 'quarantined'",
        node_scope,
    )
    if quarantined:
        findings.append({
            "severity": "INFO", "code": "QUARANTINED_MEMORY_PRESENT",
            "message": f"{quarantined} quarantined item(s) are stored but excluded from ordinary retrieval.",
        })
    if not findings:
        findings.append({
            "severity": "OK", "code": "NO_STRUCTURAL_FINDINGS",
            "message": "No structural or temporal integrity findings were detected by the current checks.",
        })
    return findings


def _recent_events(store: MemoryStore, ctx: Ctx, limit: int, *, include_content: bool) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    rows = store.conn.execute(
        "SELECT id, writer_id, tier, type, payload, created_at FROM events WHERE tenant = ? ORDER BY id DESC LIMIT ?",
        (ctx.tenant_id, limit),
    ).fetchall()
    events = []
    for row in reversed(rows):
        payload = str(row["payload"])
        event = {
            "id": int(row["id"]),
            "writer_id": str(row["writer_id"]),
            "tier": str(row["tier"]),
            "type": str(row["type"]),
            "created_at": str(row["created_at"]),
            "payload_sha256": _sha256(payload),
            "payload_chars": len(payload),
        }
        if include_content:
            event["payload_redacted"] = _safe_text(payload, limit=1000)
        events.append(event)
    return events


def audit_store(
    store: MemoryStore,
    ctx: Ctx,
    *,
    tail_events: int = 20,
    include_content: bool = False,
) -> dict[str, Any]:
    """Read-only consistency audit for a tenant/project memory store."""
    audit_start = time.perf_counter()
    with SQLTrace(store.conn) as sql_trace:
        counts = _scoped_counts(store, ctx)
        findings = _diagnostic_findings(store, ctx)
        recent_events = _recent_events(store, ctx, tail_events, include_content=include_content)
    status = "ERROR" if any(row["severity"] == "ERROR" for row in findings) else (
        "WARNING" if any(row["severity"] == "WARNING" for row in findings) else "OK"
    )
    return {
        "schema_version": _SCHEMA_VERSION,
        "timestamp": utc_now(),
        "event": "memory_audit",
        "tenant": ctx.tenant_id,
        "project": ctx.project,
        "status": status,
        "elapsed_ms": round((time.perf_counter() - audit_start) * 1000.0, 3),
        "counts": counts,
        "findings": findings,
        "recent_events": recent_events,
        "sql_profile": sql_trace.report(),
    }


def run_traced_retrieval(
    store: MemoryStore,
    ctx: Ctx,
    query: str,
    *,
    mode: str,
    as_of: str | None = None,
    entity: str | None = None,
    k: int = 8,
    graph_hops: int | None = None,
    include_content: bool = False,
    log_path: str | Path | None = None,
    probe: dict[str, Any] | None = None,
) -> tuple[RetrieveResult, dict[str, Any]]:
    """Run one retrieval and emit detailed, redacted, replayable telemetry."""
    if mode not in {"flat", "graph"}:
        raise ValueError("mode must be 'flat' or 'graph'")
    trace_id = uuid.uuid4().hex
    query_start = time.perf_counter()
    profile: dict[str, Any]
    try:
        with SQLTrace(store.conn) as sql_trace:
            result = store.retrieve(
                ctx, query, entity=entity, as_of=as_of, k=k,
                expand=(mode == "graph"), graph_hops=graph_hops,
            )
        profile = sql_trace.report()
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - query_start) * 1000.0
        record: dict[str, Any] = {
            "schema_version": _SCHEMA_VERSION,
            "timestamp": utc_now(),
            "event": "retrieval_error",
            "trace_id": trace_id,
            "tenant": ctx.tenant_id,
            "project": ctx.project,
            "mode": mode,
            "query_sha256": _sha256(query),
            "query_chars": len(query),
            "elapsed_ms": round(elapsed_ms, 3),
            "error_type": type(exc).__name__,
            "error_message": _safe_text(str(exc), limit=500),
        }
        if include_content:
            record["query_redacted"] = _safe_text(query)
        if log_path:
            append_jsonl(log_path, record)
        raise

    elapsed_ms = (time.perf_counter() - query_start) * 1000.0
    items = []
    for rank, item in enumerate(result.items, 1):
        item_record: dict[str, Any] = {
            "rank": rank,
            "id": item.id,
            "kind": item.kind,
            "entity": item.entity,
            "attribute": item.attribute,
            "score": round(float(item.score), 6),
            "via": item.via,
            "valid_from": item.valid_from,
            "valid_to": item.valid_to,
            "trust_tier": item.trust_tier,
            "text_sha256": _sha256(item.text),
            "text_chars": len(item.text),
            "value_sha256": _sha256(item.value or ""),
            "value_chars": len(item.value or ""),
        }
        if include_content:
            item_record["text_redacted"] = _safe_text(item.text, limit=800)
            item_record["value_redacted"] = _safe_text(item.value or "", limit=300)
        items.append(item_record)

    top_score = round(float(result.items[0].score), 6) if result.items else None
    harness_abstain = bool(result.abstain) or not result.items or top_score < 0.25
    record = {
        "schema_version": _SCHEMA_VERSION,
        "timestamp": utc_now(),
        "event": "retrieval",
        "trace_id": trace_id,
        "tenant": ctx.tenant_id,
        "project": ctx.project,
        "writer_id": ctx.writer_id,
        "mode": mode,
        "query_sha256": _sha256(query),
        "query_chars": len(query),
        "entity_filter": entity,
        "as_of": as_of,
        "k": k,
        "graph_hops": graph_hops,
        "elapsed_ms": round(elapsed_ms, 3),
        "result_count": len(result.items),
        "items": items,
        "route": result.route.model_dump(mode="json"),
        "store_abstain": bool(result.abstain),
        "abstain_reason": result.abstain_reason,
        "top_score": top_score,
        "harness_abstain": harness_abstain,
        "sql_profile": profile,
        "probe": probe or {},
    }
    if include_content:
        record["query_redacted"] = _safe_text(query)
    if log_path:
        append_jsonl(log_path, record)
    return result, record


def _default_probes(store: MemoryStore, ctx: Ctx) -> list[dict[str, Any]]:
    probes: list[dict[str, Any]] = []
    entity_row = store.conn.execute(
        """SELECT e.canonical FROM entities e JOIN nodes n ON n.entity_id = e.id
           WHERE e.tenant = ? AND n.tenant = ? AND n.project = ? AND n.status = 'active'
           ORDER BY e.canonical LIMIT 1""",
        (ctx.tenant_id, ctx.tenant_id, ctx.project),
    ).fetchone()
    if entity_row:
        entity = str(entity_row["canonical"])
        rows = store.conn.execute(
            """SELECT n.attribute, n.value FROM nodes n JOIN entities e ON e.id = n.entity_id
               WHERE n.tenant = ? AND n.project = ? AND e.canonical = ? AND n.kind = 'fact' AND n.status = 'active'
               ORDER BY n.attribute""",
            (ctx.tenant_id, ctx.project, entity),
        ).fetchall()
        gold = [[str(row["attribute"] or ""), str(row["value"] or "")] for row in rows]
        probes.append({
            "id": "auto_entity_centric",
            "family": "entity_centric",
            "query": f"What is known about {entity}?",
            "entity": entity,
            "gold": gold,
        })
    owner_row = store.conn.execute(
        """SELECT e.canonical AS entity, n.value FROM nodes n JOIN entities e ON e.id = n.entity_id
           WHERE n.tenant = ? AND n.project = ? AND n.kind = 'fact' AND n.attribute = 'owner'
             AND n.status = 'active' ORDER BY e.canonical LIMIT 1""",
        (ctx.tenant_id, ctx.project),
    ).fetchone()
    if owner_row:
        owner_entity = str(owner_row["entity"])
        probes.append({
            "id": "auto_direct_owner",
            "family": "single_fact",
            "query": f"Who owns {owner_entity}?",
            "entity": owner_entity,
            "gold": [["owner", str(owner_row["value"] or "")]],
        })

    historical = store.conn.execute(
        """SELECT e.canonical AS entity, n.attribute, n.value, n.valid_to
           FROM nodes n JOIN entities e ON e.id = n.entity_id
           WHERE n.tenant = ? AND n.project = ? AND n.kind = 'fact'
             AND n.attribute = 'owner' AND n.status = 'superseded' AND n.valid_to IS NOT NULL
           ORDER BY n.valid_to DESC, n.id LIMIT 1""",
        (ctx.tenant_id, ctx.project),
    ).fetchone()
    if historical:
        try:
            at = _iso_key(str(historical["valid_to"])) - timedelta(seconds=1)
            as_of = at.isoformat().replace("+00:00", "Z")
            entity = str(historical["entity"])
            probes.append({
                "id": "auto_temporal_owner",
                "family": "temporal",
                "query": f"Who owned {entity} immediately before the latest correction?",
                "entity": entity,
                "as_of": as_of,
                "gold": [[str(historical["attribute"]), str(historical["value"])]],
            })
        except (TypeError, ValueError):
            pass
    catalogue_names = [str(row[0]).casefold() for row in store.conn.execute(
        """SELECT DISTINCT e.canonical FROM entities e JOIN nodes n ON n.entity_id = e.id
           WHERE e.tenant = ? AND n.tenant = ? AND n.project = ? AND n.status IN ('active', 'contested')""",
        (ctx.tenant_id, ctx.tenant_id, ctx.project),
    ).fetchall()]
    numeric_prefixes = sorted({
        match.group(1) for name in catalogue_names
        if (match := re.match(r"^([a-z][a-z0-9]*[-_])\d+", name)) is not None
    })
    unknown_ref = f"{numeric_prefixes[0]}999999" if numeric_prefixes else "memory-doctor-unknown-unregistered"
    probes.append({
        "id": "auto_unanswerable",
        "family": "unanswerable",
        "query": f"What owner and runtime are configured for {unknown_ref}?",
        "gold": [],
    })
    return probes


def run_doctor(
    store: MemoryStore,
    ctx: Ctx,
    *,
    queries: list[dict[str, Any]] | None = None,
    modes: list[str] | None = None,
    k: int = 8,
    log_path: str | Path = "logs/memory-doctor.jsonl",
    include_content: bool = False,
    tail_events: int = 20,
) -> dict[str, Any]:
    """Run store audit and flat/graph diagnostic probes, returning a concise report."""
    modes = modes or ["flat", "graph"]
    audit = audit_store(store, ctx, tail_events=tail_events, include_content=include_content)
    append_jsonl(log_path, audit)
    probes = queries if queries else _default_probes(store, ctx)
    probe_results: list[dict[str, Any]] = []
    for probe in probes:
        for mode in modes:
            result, trace = run_traced_retrieval(
                store, ctx, str(probe["query"]), mode=mode,
                as_of=probe.get("as_of"), entity=probe.get("entity"), k=k,
                include_content=include_content, log_path=log_path,
                probe={"id": probe.get("id"), "family": probe.get("family")},
            )
            expected = {tuple(pair) for pair in probe.get("gold", [])}
            returned = {(item.attribute or "", item.value or "") for item in result.items}
            family = probe.get("family", "custom")
            if family == "entity_centric":
                correctness = len(expected & returned) / len(expected) if expected else None
            elif family == "unanswerable":
                top_score = float(result.items[0].score) if result.items else 0.0
                harness_abstain = bool(result.abstain) or not result.items or top_score < 0.25
                correctness = float(harness_abstain)
            else:
                correctness = float(bool(expected & returned)) if expected else None
            diagnosis: list[str] = []
            if family == "temporal" and correctness == 0.0:
                diagnosis.append("TEMPORAL_GOLD_MISS: requested valid-time answer was not returned.")
            if family == "entity_centric" and correctness is not None and correctness < 0.75:
                diagnosis.append("ENTITY_RECALL_LOW: fewer than 75% of known current facts were returned.")
            if family == "unanswerable" and correctness == 0.0:
                diagnosis.append("UNKNOWN_NOT_ABSTAINED: result returned for a query with no gold entity.")
            if not result.items and family != "unanswerable":
                diagnosis.append("NO_RESULT: inspect eligibility filters, query terms and index coverage.")
            if trace["elapsed_ms"] > 1000.0:
                diagnosis.append("SLOW_QUERY: retrieval took over 1,000 ms; inspect SQL profile templates.")
            probe_results.append({
                "probe_id": probe.get("id"),
                "family": family,
                "mode": mode,
                "elapsed_ms": trace["elapsed_ms"],
                "result_count": trace["result_count"],
                "top_score": trace["top_score"],
                "store_abstain": trace["store_abstain"],
                "harness_abstain": trace["harness_abstain"],
                "correctness": correctness,
                "expected_count": len(expected),
                "returned_expected_count": len(expected & returned),
                "sql_statement_count": trace["sql_profile"]["statement_count"],
                "diagnosis": diagnosis,
            })
    findings = list(audit["findings"])
    for row in probe_results:
        for problem in row["diagnosis"]:
            severity = "ERROR" if any(code in problem for code in ("TEMPORAL_GOLD_MISS", "UNKNOWN_NOT_ABSTAINED")) else "WARNING"
            findings.append({
                "severity": severity,
                "code": problem.split(":", 1)[0],
                "message": f"{row['mode']} / {row['family']} / {row['probe_id']}: {problem}",
            })
    overall_status = "ERROR" if any(row["severity"] == "ERROR" for row in findings) else (
        "WARNING" if any(row["severity"] == "WARNING" for row in findings) else "OK"
    )
    summary = {
        "schema_version": _SCHEMA_VERSION,
        "timestamp": utc_now(),
        "event": "memory_doctor_summary",
        "tenant": ctx.tenant_id,
        "project": ctx.project,
        "status": overall_status,
        "audit_status": audit["status"],
        "probe_count": len(probe_results),
        "queries": probe_results,
        "findings": findings,
        "log_path": str(log_path),
    }
    append_jsonl(log_path, summary)
    return summary
