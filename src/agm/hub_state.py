"""Tenant-scoped local session and agent connection registry.

Connection records intentionally store metadata only: no API keys, passwords, or
bearer tokens. REST health probes are restricted to loopback endpoints.
"""
from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

from .models import Ctx

_SCHEMA = """
CREATE TABLE IF NOT EXISTS agm_sessions (
    id TEXT PRIMARY KEY,
    tenant TEXT NOT NULL,
    project TEXT NOT NULL,
    writer_id TEXT NOT NULL,
    label TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('active', 'closed')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    closed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_agm_sessions_scope
    ON agm_sessions(tenant, project, writer_id, status, updated_at);
CREATE TABLE IF NOT EXISTS agm_connections (
    id TEXT PRIMARY KEY,
    tenant TEXT NOT NULL,
    project TEXT NOT NULL,
    writer_id TEXT NOT NULL,
    name TEXT NOT NULL,
    transport TEXT NOT NULL CHECK(transport IN ('rest')),
    endpoint TEXT NOT NULL,
    scopes_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(tenant, project, writer_id, name)
);
CREATE INDEX IF NOT EXISTS idx_agm_connections_scope
    ON agm_connections(tenant, project, writer_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def ensure_hub_schema(conn) -> None:
    conn.executescript(_SCHEMA)
    conn.commit()


def _scope(ctx: Ctx) -> tuple[str, str, str]:
    return ctx.tenant_id, ctx.project, ctx.writer_id


def create_session(conn, ctx: Ctx, label: str = "") -> dict[str, str]:
    ensure_hub_schema(conn)
    now = _now()
    session_id = "s_" + uuid.uuid4().hex
    safe_label = label.strip()
    if len(safe_label) > 120:
        raise ValueError("session label must be at most 120 characters")
    conn.execute(
        """INSERT INTO agm_sessions
           (id, tenant, project, writer_id, label, status, created_at, updated_at, closed_at)
           VALUES (?, ?, ?, ?, ?, 'active', ?, ?, NULL)""",
        (session_id, ctx.tenant_id, ctx.project, ctx.writer_id, safe_label, now, now),
    )
    conn.commit()
    return {"id": session_id, "label": safe_label, "status": "active", "created_at": now, "updated_at": now}


def list_sessions(conn, ctx: Ctx, *, limit: int = 50) -> list[dict[str, str | None]]:
    ensure_hub_schema(conn)
    if not 1 <= limit <= 200:
        raise ValueError("limit must be between 1 and 200")
    rows = conn.execute(
        """SELECT id, label, status, created_at, updated_at, closed_at
           FROM agm_sessions WHERE tenant = ? AND project = ? AND writer_id = ?
           ORDER BY created_at DESC, id DESC LIMIT ?""",
        (*_scope(ctx), limit),
    ).fetchall()
    return [dict(row) for row in rows]


def close_session(conn, ctx: Ctx, session_id: str) -> bool:
    ensure_hub_schema(conn)
    now = _now()
    cursor = conn.execute(
        """UPDATE agm_sessions SET status = 'closed', updated_at = ?, closed_at = ?
           WHERE id = ? AND tenant = ? AND project = ? AND writer_id = ? AND status = 'active'""",
        (now, now, session_id, *_scope(ctx)),
    )
    conn.commit()
    return cursor.rowcount == 1


def _validate_loopback_endpoint(endpoint: str) -> str:
    if not isinstance(endpoint, str) or len(endpoint) > 512:
        raise ValueError("endpoint must be a URL of at most 512 characters")
    parsed = urlsplit(endpoint)
    if parsed.scheme != "http" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("connection endpoint must be an http URL on loopback without userinfo")
    if parsed.query or parsed.fragment:
        raise ValueError("connection endpoint must not include a query or fragment")
    host = parsed.hostname.lower().rstrip(".")
    if host != "localhost":
        try:
            if not __import__("ipaddress").ip_address(host).is_loopback:
                raise ValueError("connection endpoint must resolve to a loopback IP")
        except ValueError as exc:
            if "connection endpoint must resolve" in str(exc):
                raise
            raise ValueError("connection endpoint host must be localhost or a loopback IP") from exc
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("connection endpoint has an invalid port") from exc
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("connection endpoint has an invalid port")
    path = parsed.path.rstrip("/")
    if path and path != "/":
        raise ValueError("connection endpoint must be a base URL without a path")
    return f"http://{parsed.netloc}"


def create_connection(
    conn, ctx: Ctx, *, name: str, endpoint: str, scopes: list[str] | None = None,
) -> dict[str, object]:
    ensure_hub_schema(conn)
    safe_name = name.strip()
    if not safe_name or len(safe_name) > 100:
        raise ValueError("connection name must contain 1 to 100 characters")
    safe_endpoint = _validate_loopback_endpoint(endpoint)
    requested_scopes = sorted(set(scopes or ["memory:read"]))
    allowed = {"memory:read", "memory:write", "memory:delete"}
    if not requested_scopes or any(scope not in allowed for scope in requested_scopes):
        raise ValueError("connection scopes must be a non-empty subset of memory:read/write/delete")
    now = _now()
    connection_id = "c_" + uuid.uuid4().hex
    try:
        conn.execute(
            """INSERT INTO agm_connections
               (id, tenant, project, writer_id, name, transport, endpoint, scopes_json, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 'rest', ?, ?, ?, ?)""",
            (connection_id, *_scope(ctx), safe_name, safe_endpoint,
             json.dumps(requested_scopes, separators=(",", ":")), now, now),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {
        "id": connection_id, "name": safe_name, "transport": "rest",
        "endpoint": safe_endpoint, "scopes": requested_scopes,
        "created_at": now, "updated_at": now,
    }


def list_connections(conn, ctx: Ctx) -> list[dict[str, object]]:
    ensure_hub_schema(conn)
    rows = conn.execute(
        """SELECT id, name, transport, endpoint, scopes_json, created_at, updated_at
           FROM agm_connections WHERE tenant = ? AND project = ? AND writer_id = ?
           ORDER BY name, id""",
        _scope(ctx),
    ).fetchall()
    return [{
        "id": row["id"], "name": row["name"], "transport": row["transport"],
        "endpoint": row["endpoint"], "scopes": json.loads(row["scopes_json"]),
        "created_at": row["created_at"], "updated_at": row["updated_at"],
    } for row in rows]


def test_connection(conn, ctx: Ctx, connection_id: str, *, timeout: float = 1.5) -> dict[str, object]:
    ensure_hub_schema(conn)
    row = conn.execute(
        """SELECT endpoint FROM agm_connections
           WHERE id = ? AND tenant = ? AND project = ? AND writer_id = ?""",
        (connection_id, *_scope(ctx)),
    ).fetchone()
    if row is None:
        raise KeyError("connection not found")
    endpoint = _validate_loopback_endpoint(str(row["endpoint"]))
    started = time.monotonic()
    result: dict[str, object] = {
        "connection_id": connection_id, "ok": False, "status_code": None,
        "latency_ms": None, "error": None,
    }
    request = urllib.request.Request(endpoint + "/healthz", headers={"Accept": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=timeout) as response:
            result["status_code"] = response.status
            body = response.read(4096).decode("utf-8", errors="replace")
            result["ok"] = response.status == 200 and '"status"' in body and '"ok"' in body
            if not result["ok"]:
                result["error"] = "health endpoint returned an unexpected response"
    except urllib.error.HTTPError as exc:
        result["status_code"] = exc.code
        result["error"] = "health endpoint returned an HTTP error"
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError):
        result["error"] = "could not reach loopback health endpoint"
    finally:
        result["latency_ms"] = round((time.monotonic() - started) * 1000, 2)
    return result


def delete_connection(conn, ctx: Ctx, connection_id: str) -> bool:
    ensure_hub_schema(conn)
    cursor = conn.execute(
        """DELETE FROM agm_connections
           WHERE id = ? AND tenant = ? AND project = ? AND writer_id = ?""",
        (connection_id, *_scope(ctx)),
    )
    conn.commit()
    return cursor.rowcount == 1
