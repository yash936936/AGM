# AGM Phase 5

Adaptive Graph Memory (AGM) is a local-first, model-agnostic memory layer for AI agents. Phase 1 added the event-sourced SQLite core; Phase 2 added aliases, bounded graph retrieval, contested writes, provisional trust ranking and abstention. Phase 3 added authenticated REST endpoints, nine MCP tools, API-key scopes, pre-storage secret redaction, and quarantine of instruction-like memory writes. Phase 4 adds probation checks for high-stakes retrieval, writer revocation and rollback, and replayable cross-model handoff with readback verification. Phase 5 adds a synthetic flat-versus-graph smoke evaluation, lazy decay scoring, and a read-only lifecycle dry run.

**Prototype warning:** confidence and ranking values are not calibrated. Services bind to loopback only. Do not expose the API or streamable MCP endpoint to another machine or the public internet without a separate security review.

## Requirements and installation

Python 3.11+, SQLite with FTS5, and pip. The official MCP SDK is pinned to its maintained 1.x API because this Phase 3 adapter uses `FastMCP`.

```bash
python -m venv .venv
source .venv/bin/activate              # Windows Git Bash: source .venv/Scripts/activate
python -m pip install -e ".[dev]"
```

## Configure REST keys

Copy `examples/agm.keys.example.json` to `agm.keys.json`. Replace both example API key strings with long random values. Never commit `agm.keys.json`; it is ignored by Git and excluded from packages.

Each key maps to a tenant, writer, trust tier, optional project/agent and scopes. Supported scopes are `memory:read`, `memory:write`, `memory:delete`, and `admin` (`admin` grants all of them). The API accepts `X-API-Key` or `Authorization: Bearer ...`.

Start the local REST API:

```bash
python -m agm serve-api --db ./agm.db --keys ./agm.keys.json
```

REST is available at `http://127.0.0.1:8765`; OpenAPI is at `/openapi.json`. Useful routes (handoff and admin routes are implemented in Phase 4):

- `POST /v1/memory`
- `POST /v1/memory/retrieve`
- `POST /v1/memory/{item_id}/supersede`
- `GET /v1/memory/history?entity=...`
- `DELETE /v1/memory/{item_id}`
- `POST /v1/handoff`
- `POST /v1/handoff/{packet_id}/resume`
- `POST /v1/handoff/{packet_id}/readback`
- `POST /v1/admin/revoke` (requires `admin` scope)

See `examples/curl.md` and `examples/python_client.py`.

## Start the MCP server

For stdio, configure identity and permissions in the client process environment. Example values:

```bash
export AGM_TENANT=local-dev
export AGM_WRITER=local-agent
export AGM_TIER=trusted_agent
export AGM_PROJECT=default
export AGM_DB_PATH=./agm.db
export AGM_SCOPES=memory:read,memory:write,memory:delete
python -m agm serve-mcp --transport stdio
```

`serve-mcp --transport streamable-http` listens on `127.0.0.1:8766/mcp` and uses one environment-configured identity. It is a local integration surface, not a multi-tenant remote server. All nine tool names are registered, including handoff save/resume/readback and admin-only writer revocation. `memory_retrieve` accepts `high_stakes=true` to exclude low-trust items until independent corroboration. See `examples/claude_code_mcp.md`.

## Guardrails

REST and MCP writes pass through the same guard. Recognized API-key, token, password and credential patterns are redacted before the event is persisted or text is embedded. Instruction-like text such as “ignore all previous instructions” is stored with `status="quarantined"` and is omitted from default retrieval and history responses. Retrieval responses preserve the notice that memory is untrusted data, not instructions.

This prototype guard is a narrow pattern-based filter, not a complete prompt-injection detector or secret scanner. Use local loopback only and review the code before connecting real agents or sensitive data.

## Phase 5 evaluation and lifecycle

Run the synthetic flat-vs-graph comparison:

```bash
python eval/stale_facts.py
```

Inspect items that would be archived without changing the database:

```bash
python -m agm lifecycle --db ./agm.db --dry-run
```

The dry run lists active, unpinned items below a provisional decay threshold. Phase 5 does not archive or delete those items.

## Tests and smoke check

```bash
python -m pytest -q
python -m agm demo
python -m agm rebuild --db ./demo.db
python -m agm lifecycle --db ./agm.db --dry-run
python scripts/pack.py
```

The MCP stdio integration test runs when the official `mcp` dependency is installed. Phase 4 readback similarity and the Phase 2 confidence/ranking coefficients are provisional and are not calibrated. The Phase 5 synthetic evaluation is not evidence for or against H1–H7 (D-007).

`retrieve(expand=False)` retains the flat Phase 1 baseline. `high_stakes=True` gates `trusted_agent` and `untrusted` items until independently corroborated. Revocation removes searchable views and derived descendants, but preserves source event payloads for audit; it is not a hard-delete operation. Confidence, trust and rank coefficients from D-008 are placeholders, not calibrated probabilities or evidence that graph retrieval is better.

## Connection smoke tests

```bash
python examples/mcp_smoke_client.py    # acts as an MCP host over stdio, 12 checks
python examples/rest_smoke_client.py   # real HTTP against a live loopback server, 11 checks
```

These were written by the supervisor to confirm the two integration paths work end to end. They do not replace testing with the real host (Claude Code, Claude Desktop, ChatGPT) you intend to use.

Safety guard: secret redaction and instruction-like-text quarantine run inside `MemoryStore.write` and `MemoryStore.supersede` (D-021), so direct library calls get the same protection as REST and MCP. `delete` flushes the write-ahead log (D-022) so deleted content does not linger on disk.
