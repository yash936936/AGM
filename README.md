# AGM Phase 6

Adaptive Graph Memory (AGM) is a local-first, model-agnostic memory layer for AI agents. Phase 1 added the event-sourced SQLite core; Phase 2 added aliases, bounded graph retrieval, contested writes, provisional trust ranking and abstention. Phase 3 added authenticated REST endpoints, nine MCP tools, API-key scopes, pre-storage secret redaction, and quarantine of instruction-like memory writes. Phase 4 adds probation checks for high-stakes retrieval, writer revocation and rollback, and replayable cross-model handoff with readback verification. Phase 5 adds a synthetic flat-versus-graph smoke evaluation, lazy decay scoring, and a read-only lifecycle dry run. Phase 6 adds a richer deterministic synthetic evaluation to compare flat, filtered-flat, and graph retrieval without replacing the original smoke test.

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

Secret redaction and instruction-like-text quarantine run inside `MemoryStore.write` and `MemoryStore.supersede` (D-021), so direct library calls receive the same protection as REST and MCP. `supersede` also sanitizes its reason and `handoff_save` sanitizes task-state strings and the session ID. The adapter guard remains a thin wrapper. `delete` and `revoke_writer` checkpoint the write-ahead log after commit and each SQLite connection enables `secure_delete` (D-022). Revocation retains event payloads for audit; hard delete scrubs the source event.

This prototype guard is a narrow pattern-based filter, not a complete prompt-injection detector or secret scanner. Use local loopback only and review the code before connecting real agents or sensitive data.

## Phase 5 evaluation and lifecycle

The original 4-scenario smoke test remains available:

```bash
python eval/stale_facts.py
```

Inspect items that would be archived without changing the database:

```bash
python -m agm lifecycle --db ./agm.db --dry-run
```

The dry run lists active, unpinned items below a provisional decay threshold. Phase 5 does not archive or delete those items.

## Phase 6 evaluation v2

The stronger seeded evaluation compares three modes over the same generated store: `flat` (`expand=False`, no entity filter), `flat_filter` (`expand=False`, metadata entity filter), and `graph` (`expand=True`, no entity filter). It generates six families: direct facts, corrected/stale facts, entity-centric sets, 1- and 2-hop queries, temporal queries, and unanswerable near-misses. It reports accuracy@k, stale-error rate, abstention correctness, store abstentions and harness abstentions separately, p50/p95 latency, mean result count and mean graph expansion. Seed-level means receive a deterministic 1,000-resample bootstrap 95% CI. Full results are saved under `eval/results/<timestamp>.json`.

```bash
python eval/synthetic_v2.py --entities 200 --episodes 2000 --seeds 5 --k 8 --embedder hash
```

`--seed` changes the first seed; `--seeds N` runs N consecutive seeds starting there. `--embedder st` lazily imports the optional `sentence-transformers` package and may need a model download; it is not a hard dependency. `docs/decisions.md` records the pre-declared rule before Phase 6 results. Flat wins and non-improvements must be reported; do not tune the generator after inspecting the output. The synthetic evaluation is not evidence for or against H1–H7 (D-007).

## Tests and smoke check

```bash
python -m pytest -q
python examples/mcp_smoke_client.py
python examples/rest_smoke_client.py
python eval/stale_facts.py
python eval/synthetic_v2.py --entities 200 --episodes 2000 --seeds 5
python scripts/pack.py
```

The MCP stdio integration test runs when the official `mcp` dependency is installed. Phase 4 readback similarity, Phase 2 confidence/ranking coefficients and lifecycle thresholds are provisional. `retrieve(expand=False)` retains the flat Phase 1 baseline. `high_stakes=True` gates `trusted_agent` and `untrusted` items until independently corroborated. Synthetic evaluation scores are not calibrated probabilities or evidence that graph retrieval is better.

## Connection smoke tests

```bash
python examples/mcp_smoke_client.py    # acts as an MCP host over stdio, 12 checks
python examples/rest_smoke_client.py   # real HTTP against a live loopback server, 11 checks
```

These confirm the two local integration paths. They do not replace testing with the real host (Claude Code, Claude Desktop or another agent) you intend to use.
