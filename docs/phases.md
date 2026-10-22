# Phases — AGM prototype

> Work through phases in order. Mark a phase done only when its files exist,
> pass their tests, were reviewed by Claude, and are logged in `debug.md`.
> Update `status.md` after each phase. A phase brief = the phase section below
> + the contracts in `architecture.md`.

## Phase 1 — Core store and event log
**Goal:** write, supersede, delete and flat-retrieve memory; views rebuildable by replay.
**Files touched:**
- `src/agm/models.py` — contracts from architecture.md, exactly
- `src/agm/db.py` — schema, FTS5 check
- `src/agm/events.py` — HLC, append with idempotency, replay
- `src/agm/embed.py` — `Embedder`, `HashEmbedder`
- `src/agm/store.py` — write, supersede, delete, history, rebuild_views, retrieve with `expand=False` only
- `tests/test_store.py`, `tests/test_replay.py`
**Done when:** pytest green; replay test drops all views, replays events and gets identical
nodes; same idempotency key twice yields one item; supersede hides the old value from
current retrieve and shows it with `include_superseded=True`; delete removes node, FTS row,
embedding and edges and the item never surfaces again.
**Status:** Not started

## Phase 2 — Graph layer, ranking, abstention
**Goal:** entity-aware retrieval that can be compared directly with the flat baseline.
**Files touched:**
- `src/agm/store.py` — entities and aliases, mentions/relates/supersedes/contests edges, CAS and contested logic
- `src/agm/retrieve.py` — expansion (1 hop default, max 2, fan-out 10, hub cap 50), validity filter, ranking, sufficiency, abstain, route report
- `src/agm/trust.py` — confidence formula and tier weights (placeholders per D-008)
- `tests/test_retrieve.py`, `tests/test_contested.py`
**Done when:** `expand=False` output is identical to Phase 1 flat retrieve; an entity query
pulls related current facts via expansion; unanswerable query abstains; stale-base write
becomes `contested` and both facts return with a warning; route fields are populated.
**Status:** Not started

## Phase 3 — Interfaces: REST, MCP, auth, redaction  (first point where real agents connect)
**Goal:** any agent can connect. Minimum safety before exposure.
**Files touched:**
- `src/agm/config.py`, `src/agm/guard.py` (redaction + instruction-like screen)
- `src/agm/api.py` — endpoints per parity table, API-key auth, OpenAPI
- `src/agm/mcp_server.py` — 9 tools, stdio and streamable HTTP, identity from env
- `src/agm/cli.py` — `serve-api`, `serve-mcp`, `demo`, `rebuild`
- `examples/` — python_client.py, curl.md, claude_code_mcp.md, chatgpt_actions.md
- `tests/test_guard.py`, `tests/test_e2e_rest.py`
**Done when:** a Python script writes and retrieves over REST; an MCP client (Claude Code or
Desktop) lists the tools and round-trips a write and a retrieve over stdio; a fake API key
gets 401; a string shaped like an API key is stored redacted and never embedded; an
"ignore previous instructions" style write is quarantined and not returned by default.
**Status:** Not started

## Phase 4 — Trust, handoff, rollback
**Goal:** switch models mid-task and contain a bad writer.
**Files touched:**
- `src/agm/trust.py` — probation, corroboration by independent writer, revoke and rollback
- `src/agm/handoff.py` — TaskState, packet, context assembly (pinned → task state → retrieved → model formatting), readback compare
- `src/agm/store.py` — wire handoff and revoke methods
- `tests/test_trust.py`, `tests/test_handoff.py`
**Done when:** probationary writes are excluded from high-stakes retrieval until corroborated
by a different writer; `handoff_resume` respects the token budget; a readback missing a
packet decision is reported as a mismatch; `revoke_writer` removes that writer's items and
anything derived, verified by test.
**Status:** Not started

## Phase 5 — Mini eval, shadow lifecycle, demo
**Goal:** an honest first look at flat vs graph, plus a runnable demo.
**Files touched:**
- `eval/stale_facts.py` — synthetic scenarios (changed facts, entity questions, unanswerable); reports stale-fact error, accuracy, abstention for `expand=False` vs `True`
- `src/agm/trust.py` — decay weight computed lazily; `agm lifecycle --dry-run` reports what would be archived, changes nothing
- `src/agm/cli.py` — `demo` runs write → correct → retrieve → handoff
- `docs/readme.md` updated to real state
**Done when:** eval prints a table with the D-007 caveat; demo runs end to end offline; dry-run
lifecycle lists candidates without mutating state (checked by test).
**Status:** Not started

---
**Next:** Return to [`context.md`](../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
