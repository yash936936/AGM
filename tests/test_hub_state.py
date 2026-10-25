from __future__ import annotations

import json

import pytest

from agm import Ctx, MemoryStore
from agm.hub_state import (
    close_session, create_connection, create_session, delete_connection,
    list_connections, list_sessions, test_connection as probe_connection,
)


def _ctx(tenant="tenant-a", project="project-a", writer="writer-a"):
    return Ctx(tenant_id=tenant, writer_id=writer, tier="human_verified", project=project)


def test_session_lifecycle_is_persistent_and_scoped(tmp_path):
    path = str(tmp_path / "hub-sessions.db")
    owner = _ctx()
    foreign = _ctx(tenant="tenant-b")
    with MemoryStore(path) as store:
        created = create_session(store.conn, owner, "work session")
        assert created["status"] == "active"
        assert len(list_sessions(store.conn, owner)) == 1
        assert list_sessions(store.conn, foreign) == []
        assert close_session(store.conn, foreign, created["id"]) is False
        assert close_session(store.conn, owner, created["id"]) is True
        assert close_session(store.conn, owner, created["id"]) is False
        row = list_sessions(store.conn, owner)[0]
        assert row["status"] == "closed"
        assert row["closed_at"] is not None
    with MemoryStore(path) as reopened:
        assert list_sessions(reopened.conn, owner)[0]["id"] == created["id"]


def test_session_limit_and_label_are_validated(tmp_path):
    with MemoryStore(str(tmp_path / "hub-session-validation.db")) as store:
        with pytest.raises(ValueError, match="label"):
            create_session(store.conn, _ctx(), "x" * 121)
        with pytest.raises(ValueError, match="limit"):
            list_sessions(store.conn, _ctx(), limit=0)


def test_connection_registry_is_scoped_and_stores_metadata_only(tmp_path):
    with MemoryStore(str(tmp_path / "hub-connections.db")) as store:
        ctx = _ctx()
        foreign = _ctx(tenant="tenant-b")
        created = create_connection(
            store.conn, ctx, name="local-agent", endpoint="http://127.0.0.1:8765",
            scopes=["memory:read", "memory:write"],
        )
        assert created["transport"] == "rest"
        assert created["scopes"] == ["memory:read", "memory:write"]
        assert list_connections(store.conn, ctx)[0]["id"] == created["id"]
        assert list_connections(store.conn, foreign) == []
        serialized = json.dumps(list_connections(store.conn, ctx))
        assert "token" not in serialized.lower()
        assert "password" not in serialized.lower()
        assert delete_connection(store.conn, foreign, created["id"]) is False
        assert delete_connection(store.conn, ctx, created["id"]) is True


@pytest.mark.parametrize("endpoint", [
    "https://127.0.0.1:8765",
    "http://example.com",
    "http://127.0.0.1:8765/admin",
    "http://user:password@127.0.0.1:8765",
    "http://127.0.0.1:8765?token=secret",
])
def test_connection_endpoint_rejects_non_loopback_or_ambiguous_urls(tmp_path, endpoint):
    with MemoryStore(str(tmp_path / "hub-connection-invalid.db")) as store:
        with pytest.raises(ValueError):
            create_connection(store.conn, _ctx(), name="unsafe", endpoint=endpoint)


def test_connection_scopes_are_least_privilege_and_validated(tmp_path):
    with MemoryStore(str(tmp_path / "hub-connection-scopes.db")) as store:
        with pytest.raises(ValueError, match="scopes"):
            create_connection(
                store.conn, _ctx(), name="too-powerful",
                endpoint="http://localhost:8765", scopes=["admin"],
            )


def test_connection_diagnostics_fail_closed_for_unreachable_loopback(tmp_path):
    with MemoryStore(str(tmp_path / "hub-connection-test.db")) as store:
        created = create_connection(
            store.conn, _ctx(), name="offline", endpoint="http://127.0.0.1:1",
        )
        result = probe_connection(store.conn, _ctx(), str(created["id"]), timeout=0.1)
        assert result["ok"] is False
        assert result["error"] == "could not reach loopback health endpoint"
        assert isinstance(result["latency_ms"], float)
        with pytest.raises(KeyError, match="connection not found"):
            probe_connection(store.conn, _ctx(tenant="foreign"), str(created["id"]))
