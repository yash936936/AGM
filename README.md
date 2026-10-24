# AGM Phase 8

Adaptive Graph Memory (AGM) is a local-first, model-agnostic memory layer for AI agents. Phase 1 added the event-sourced SQLite core; Phase 2 added aliases, bounded graph retrieval, contested writes, provisional trust ranking and abstention. Phase 3 added authenticated REST endpoints, nine MCP tools, API-key scopes, pre-storage secret redaction, and quarantine of instruction-like memory writes. Phase 4 adds probation checks for high-stakes retrieval, writer revocation and rollback, and replayable cross-model handoff with readback verification. Phase 5 adds a synthetic flat-versus-graph smoke evaluation, lazy decay scoring, and a read-only lifecycle dry run. Phase 6 adds a richer deterministic synthetic evaluation to compare flat, filtered-flat, and graph retrieval without replacing the original smoke test. Phase 7 diagnosed multi-hop query/evaluator alignment, catalogue-backed unknown-entity abstention, and graph traversal latency. Phase 8 investigates temporal retrieval and entity-centric ranking, adds a mixed-context sample corpus, runs a flat-versus-graph size/context matrix, and introduces a privacy-aware Memory Doctor plus an agent demo. Neither phase changes D-024 thresholds or tunes the Phase 6 generator to force a positive result.

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

## Phase 7 retrieval diagnostics

Phase 7 makes three targeted corrections identified by the Phase 6 run:

- **Multi-hop alignment:** questions say exactly how many dependency edges away the target is. The graph evaluator requests depth two for the `multi_hop` family while production/default graph depth remains one. For directed downstream questions, traversal begins at the entity named in the query and follows relation edges supported by eligible current facts; it does not seed from unrelated global top-ranked nodes.
- **Unknown service IDs:** when the catalogue already contains a numeric-ID namespace such as `svc-…`, an exact unknown/near-miss ID in that namespace is rejected before fuzzy retrieval. This does not change the shared evaluation threshold (0.25).
- **Graph latency:** corroboration counts are batched instead of running the same corroboration query once per candidate. The graph fan-out limit is applied after eligibility filtering so superseded rows cannot crowd a current row out of the result set.

D-025 logs diagnostic targets and leaves D-024's decision rule, baseline modes, generated facts/relation chain, bootstrap method, and abstention threshold intact. The saved Phase 7 result and detailed analysis are in `eval/results/20261023T184404.879694Z.json` and `PHASE7_REPORT.md`. These synthetic results remain subject to D-007 and are not evidence for or against hypotheses H1–H7.

Run the same five-seed diagnostic configuration:

```bash
python -m pytest -q
python eval/synthetic_v2.py --entities 200 --episodes 2000 --seeds 5 --k 8 --embedder hash
python scripts/pack.py
```

The results currently available were produced in the builder environment. The final performance targets must be confirmed by running the same configuration on the actual Windows v0.5.1 checkout; do not treat cross-machine latency as a comparable benchmark.

## Phase 6 evaluation v2

The stronger seeded evaluation compares three modes over the same generated store: `flat` (`expand=False`, no entity filter), `flat_filter` (`expand=False`, metadata entity filter), and `graph` (`expand=True`, no entity filter). It generates six families: direct facts, corrected/stale facts, entity-centric sets, 1- and 2-hop queries, temporal queries, and unanswerable near-misses. It reports accuracy@k, stale-error rate, abstention correctness, store abstentions and harness abstentions separately, p50/p95 latency, mean result count and mean graph expansion. Seed-level means receive a deterministic 1,000-resample bootstrap 95% CI. Full results are saved under `eval/results/<timestamp>.json`.

```bash
python eval/synthetic_v2.py --entities 200 --episodes 2000 --seeds 5 --k 8 --embedder hash
```

`--seed` changes the first seed; `--seeds N` runs N consecutive seeds starting there. `--embedder st` lazily imports the optional `sentence-transformers` package and may need a model download; it is not a hard dependency. `docs/decisions.md` records the pre-declared rule before Phase 6 results. Flat wins and non-improvements must be reported; do not tune the generator after inspecting the output. The synthetic evaluation is not evidence for or against H1–H7 (D-007).


## Phase 8 — temporal and entity-centric retrieval, benchmark matrix, Memory Doctor

Phase 8 adds a 44-record sample memory corpus spanning current and corrected facts, dependencies, procedures, incident notes, and one instruction-like item that should be quarantined by the existing core guard.

Create an isolated sample database and inspect the import decisions:

```bash
python scripts/ingest_phase8_sample.py --db ./phase8-memory.db --log logs/phase8-ingest.jsonl
```

Run the read-only structural audit and flat/graph diagnostic probes. The log is append-only JSONL; by default it records identifiers, hashes, metadata, score/valid-time/route/abstention details, SQL statement counts and normalized SQL shapes, plus a bounded event-payload hash tail. Add `--include-content` only when you intentionally want guard-redacted snippets in local logs.

```bash
python -m agm doctor --db ./phase8-memory.db --tenant phase8-demo --project phase8 --log logs/memory-doctor.jsonl
```

To run a retrieval-augmented agent loop without an LLM first:

```bash
python examples/phase8_agent_demo.py --db ./phase8-memory.db --tenant phase8-demo --project phase8 --mode graph --query 'Who owns billing-api?' --provider offline --log logs/phase8-agent.jsonl
```

The offline provider validates retrieval and instrumentation only; it does not simulate or claim model reasoning. For an optional real OpenAI Responses API call, install the optional SDK (`python -m pip install openai`), set `OPENAI_API_KEY` and `OPENAI_MODEL` in the local environment, then select `--provider openai`. Do not place credentials in command arguments or logs. Review the prompt and use synthetic/sample data before any real sensitive memory is sent to a model.

Run the flat-versus-graph matrix over memory sizes and context densities:

```bash
python eval/phase8_benchmark.py --sizes 25 60 --contexts sparse balanced dense --seeds 0 1 --k 8
```

The committed diagnostic matrix uses sizes 12, 25, and 50 entities; sparse/balanced/dense context means 0/1/4 free-form episodes per entity; seeds 0, 1, and 2; `k=8`; the hash embedder; and the original 0.25 abstention rule. It reports family and overall accuracy, stale error, abstention correctness, p50/p95, returned items, graph expansion, ingest time, and per-query evidence/scores. This smaller matrix is exploratory and is not a replacement for D-024's five-seed three-mode decision protocol.

The sample benchmark and full-scale five-seed result are saved in `eval/results/phase8-benchmark-20261024T110135.355459Z.json` and `eval/results/phase8-synthetic-200x2000-5seeds-20261024T110557.327133Z.json`. The corpus and all figures are synthetic; D-007 remains in force.

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
