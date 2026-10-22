from __future__ import annotations

import asyncio
import importlib.util
import json
import os
from pathlib import Path
import sys
import uuid

import pytest

pytestmark = pytest.mark.skipif(importlib.util.find_spec("mcp") is None, reason="official MCP SDK is not installed in this environment")


def _content_json(result):
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return structured
    content = getattr(result, "content", None) or []
    for block in content:
        text = getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                continue
    raise AssertionError("MCP tool result did not contain a JSON payload")


def test_stdio_lists_tools_and_roundtrips_write_retrieve(tmp_path: Path) -> None:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def run() -> None:
        db_path = tmp_path / "stdio.db"
        env = os.environ.copy()
        env.update({
            "AGM_DB_PATH": str(db_path),
            "AGM_TENANT": "mcp-test-tenant",
            "AGM_WRITER": "mcp-test-writer",
            "AGM_TIER": "trusted_agent",
            "AGM_PROJECT": "default",
            "AGM_SCOPES": "memory:read,memory:write,memory:delete",
            "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")
            + os.pathsep + env.get("PYTHONPATH", ""),
        })
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "agm", "serve-mcp", "--transport", "stdio"],
            env=env,
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                listing = await session.list_tools()
                names = {tool.name for tool in listing.tools}
                expected = {
                    "memory_write", "memory_retrieve", "memory_supersede", "memory_history",
                    "memory_delete", "handoff_save", "handoff_resume", "handoff_readback",
                    "memory_revoke_writer",
                }
                assert expected.issubset(names)
                item = {
                    "kind": "fact", "text": "MCP stdio round trip is connected",
                    "entity": "MCP transport test", "attribute": "status", "value": "connected",
                    "idempotency_key": "stdio-" + uuid.uuid4().hex,
                }
                write_result = _content_json(await session.call_tool("memory_write", arguments={"item": item}))
                assert write_result["status"] == "added"
                retrieve_result = _content_json(await session.call_tool("memory_retrieve", arguments={
                    "query": "MCP stdio round trip connected", "entity": "MCP transport test", "k": 5,
                }))
                assert any(node["value"] == "connected" for node in retrieve_result["items"])

    asyncio.run(run())
