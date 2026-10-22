# Phases — AGM prototype

> Work through phases in order. Mark a phase done only when its files exist,
> pass their tests, were reviewed, and are logged in `debug.md`.
> Update `status.md` after each phase. A phase brief = the phase section below
> + the contracts in `architecture.md`.

## Phase 1 — Core store and event log
**Goal:** write, supersede, delete and flat-retrieve memory; views rebuildable by replay.
**Files touched:**
- `src/agm/models.py` — frozen Pydantic contracts
- `src/agm/db.py` — schema, FTS5 check
- `src/agm/events.py` — HLC, append with idempotency, replay
- `src/agm/embed.py` — `Embedder`, `HashEmbedder`
- `src/agm/store.py` — write, supersede, delete, history, rebuild_views, flat retrieval
- `pyproject.toml`, `src/agm/__main__.py`, `src/agm/cli.py`, `scripts/pack.py`
- `tests/test_store.py`, `tests/test_replay.py`
**Done when:** pytest green; replay reconstructs node rows and embeddings; idempotency works; correction and history work; hard delete scrubs the source event and removes derived node data.
**Status:** Implemented. Ten Phase 1 tests passed on the user's Windows environment; Phase 2 regression tests retain these behaviors.

## Phase 2 — Graph layer, ranking, abstention
**Goal:** entity-aware retrieval that can be compared directly with the flat baseline.
**Files touched:**
- `src/agm/store.py` — entity identity and aliases, mentions/relates/supersedes/contests edges, CAS and contested logic
- `src/agm/retrieve.py` — bounded graph expansion (1 hop by default, max 2), validity filtering, ranking, sufficiency, abstention, route report
- `src/agm/trust.py` — D-008 provisional confidence formula and tier weights
- `tests/test_retrieve.py`, `tests/test_contested.py`, `tests/test_trust_phase2.py`, `tests/test_replay.py`
**Done when:** `expand=False` preserves the flat baseline; entity and relation queries expand to related facts; unanswerable queries abstain after one widening; stale-base writes become contested without replacing the active fact; route and conflict fields are populated; replay remains deterministic after deletion and alias resolution.
**Status:** Implementation and overlay package built. Thirty-one tests pass in the builder environment (Python 3.13.5); Windows verification and supervisor approval are pending.

## Phase 3 — Interfaces: REST, MCP, auth, redaction
**Goal:** any agent can connect, with minimum safety before exposure.
**Planned files:** `src/agm/config.py`, `guard.py`, `api.py`, `mcp_server.py`, `cli.py`, `examples/`, and interface tests.
**Done when:** REST and MCP round trips pass; invalid keys get 401; secrets are redacted before storage and embeddings; instruction-like writes are quarantined by default.
**Status:** Not started.

## Phase 4 — Trust, handoff, rollback
**Goal:** switch models mid-task and contain a bad writer.
**Planned files:** `src/agm/trust.py`, `src/agm/handoff.py`, `src/agm/store.py`, and trust/handoff tests.
**Done when:** probation and independent corroboration rules work; handoff assembly respects token budgets; readback mismatches are reported; writer revocation removes derived data.
**Status:** Not started.

## Phase 5 — Mini eval, shadow lifecycle, demo
**Goal:** an honest first look at flat vs graph, plus a runnable demo.
**Planned files:** `eval/stale_facts.py`, `src/agm/trust.py`, `src/agm/cli.py`, and the public README.
**Done when:** evaluation compares flat and graph modes and carries the D-007 caveat; demo runs end to end offline; dry-run lifecycle lists candidates without mutating state.
**Status:** Not started.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task — it routes you to the right file for what you are about to do.
