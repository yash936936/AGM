"""Official MCP SDK adapter for the AGM core store.

The stdio transport is intended for a local agent host. Streamable HTTP is
restricted to loopback and uses the single identity configured in environment
variables; do not treat it as a multi-tenant remote deployment.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Literal

from .config import database_path, ensure_loopback_host, runtime_identity_from_env
from .models import Ctx, Readback, TaskState, WriteItem
from .store import MemoryStore

_LOG = logging.getLogger(__name__)


def create_mcp_server(
    *,
    store: MemoryStore,
    ctx: Ctx,
    scopes: frozenset[str],
) -> Any:
    """Register the nine stable tool names from the architecture parity table."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # make missing extras actionable
        raise RuntimeError(
            "The MCP server requires the official SDK. Install the project with `pip install -e '.[dev]'` "
            "or install its `mcp>=1.26,<2` dependency."
        ) from exc

    server = FastMCP("Adaptive Graph Memory")

    def require(scope: str) -> None:
        if "*" not in scopes and "admin" not in scopes and scope not in scopes:
            raise PermissionError(f"MCP identity lacks required scope: {scope}")

    @server.tool()
    def memory_write(item: dict[str, Any]) -> dict[str, Any]:
        """Store a structured episode, fact, or procedure. Secrets are redacted and instruction-like content is quarantined."""
        require("memory:write")
        parsed = WriteItem.model_validate(item)
        return store.write(ctx, parsed).model_dump(mode="json")

    @server.tool()
    def memory_retrieve(
        query: str,
        entity: str | None = None,
        as_of: str | None = None,
        k: int = 8,
        expand: bool = True,
        include_superseded: bool = False,
        high_stakes: bool = False,
    ) -> dict[str, Any]:
        """Retrieve relevant current memory with provenance, graph route, and an abstention signal."""
        require("memory:read")
        result = store.retrieve(
            ctx, query, entity=entity, as_of=as_of, k=k, expand=expand,
            include_superseded=include_superseded, high_stakes=high_stakes,
        )
        return result.model_dump(mode="json")

    @server.tool()
    def memory_supersede(item_id: str, item: dict[str, Any], reason: str) -> dict[str, Any]:
        """Correct an active fact explicitly, retaining the old fact as history."""
        require("memory:write")
        parsed = WriteItem.model_validate(item)
        return store.supersede(ctx, item_id, parsed, reason).model_dump(mode="json")

    @server.tool()
    def memory_history(entity: str, attribute: str | None = None) -> list[dict[str, Any]]:
        """List all versions for an entity, oldest first, optionally limited to one attribute."""
        require("memory:read")
        visible = []
        for node in store.history(ctx, entity, attribute):
            row = store.conn.execute(
                "SELECT status FROM nodes WHERE id = ? AND tenant = ?",
                (node.id, ctx.tenant_id),
            ).fetchone()
            if row is not None and row["status"] != "quarantined":
                visible.append(node.model_dump(mode="json"))
        return visible

    @server.tool()
    def memory_delete(item_id: str) -> dict[str, Any]:
        """Hard-delete a memory item and its derived index/graph data, scrubbing its source event payload."""
        require("memory:delete")
        return store.delete(ctx, item_id).model_dump(mode="json")

    @server.tool()
    def handoff_save(session_id: str, task_state: dict[str, Any]) -> dict[str, Any]:
        """Save task state as a handoff packet. This tool is declared now but implemented in Phase 4."""
        require("memory:write")
        state = TaskState.model_validate(task_state)
        return store.handoff_save(ctx, session_id, state).model_dump(mode="json")

    @server.tool()
    def handoff_resume(packet_id: str, target_model: str, token_budget: int) -> dict[str, Any]:
        """Assemble pinned memory, task state and relevant retrieved memory under a token budget."""
        require("memory:read")
        return store.handoff_resume(ctx, packet_id, target_model, token_budget).model_dump(mode="json")

    @server.tool()
    def handoff_readback(packet_id: str, readback: dict[str, Any]) -> dict[str, Any]:
        """Compare a resumed model's goal, decisions and open items to the saved packet."""
        require("memory:write")
        state = Readback.model_validate(readback)
        return store.handoff_readback(ctx, packet_id, state).model_dump(mode="json")

    @server.tool()
    def memory_revoke_writer(writer_id: str, since: str | None = None) -> dict[str, Any]:
        """Revoke a writer in this tenant and roll back its stored items and dependent derived data."""
        require("admin")
        return store.revoke_writer(ctx, writer_id, since).model_dump(mode="json")

    return server


def serve_mcp(
    *,
    transport: Literal["stdio", "streamable-http"] = "stdio",
    host: str = "127.0.0.1",
    port: int = 8766,
    db_path: str | None = None,
) -> int:
    """Run the local MCP server and close the database handle on exit."""
    if transport not in {"stdio", "streamable-http"}:
        raise ValueError("MCP transport must be 'stdio' or 'streamable-http'.")
    if transport == "streamable-http":
        ensure_loopback_host(host)
    ctx, scopes = runtime_identity_from_env()
    store = MemoryStore(database_path(db_path))
    try:
        server = create_mcp_server(store=store, ctx=ctx, scopes=scopes)
        if transport == "stdio":
            server.run(transport="stdio")
        else:
            server.run(transport="streamable-http", host=host, port=port)
    finally:
        store.close()
    return 0
