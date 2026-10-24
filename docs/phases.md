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
**Status:** Implemented. The user reported ten Phase 1 tests passing on Windows; the Phase 2 suite retains these behaviors. Review/log closure is tracked in status.md.

## Phase 2 — Graph layer, ranking, abstention
**Goal:** entity-aware retrieval that can be compared directly with the flat baseline.
**Files touched:**
- `src/agm/store.py` — entity identity and aliases, mentions/relates/supersedes/contests edges, CAS and contested logic
- `src/agm/retrieve.py` — bounded graph expansion (1 hop by default, max 2), validity filtering, ranking, sufficiency, abstention, route report
- `src/agm/trust.py` — D-008 provisional confidence formula and tier weights
- `tests/test_retrieve.py`, `tests/test_contested.py`, `tests/test_trust_phase2.py`, `tests/test_replay.py`
**Done when:** `expand=False` preserves the flat baseline; entity and relation queries expand to related facts; unanswerable queries abstain after one widening; stale-base writes become contested without replacing the active fact; route and conflict fields are populated; replay remains deterministic after deletion and alias resolution.
**Status:** The user reported 31 tests passing on Windows Python 3.14.7, plus successful demo, rebuild, and packaging. Supervisor review and archive verification remain separate closure checks.

## Phase 3 — Interfaces: REST, MCP, auth, redaction
**Goal:** any agent can connect, with minimum safety before exposure.
**Files implemented:** `src/agm/config.py`, `guard.py`, `api.py`, `mcp_server.py`, CLI commands `serve-api`/`serve-mcp`, `examples/`, `tests/test_guard.py`, `tests/test_e2e_rest.py`, and `tests/test_mcp_stdio.py`.
**Done when:** REST and MCP round trips pass; invalid keys get 401; secrets are redacted before storage and embeddings; instruction-like writes are quarantined by default.
**Status:** Windows-verified by the user on 2026-10-23: `43 passed` in 15.15 seconds; REST health, authenticated write/retrieve, and invalid-key HTTP 401 smoke checks succeeded. The test run emitted one Starlette/httpx deprecation warning. Keep remote exposure disabled pending security review.

## Phase 4 — Trust, handoff, rollback
**Goal:** switch models mid-task and contain a bad writer.
**Files touched:** `src/agm/trust.py`, new `src/agm/handoff.py`, `src/agm/store.py`, `src/agm/retrieve.py`, `src/agm/models.py`, REST/MCP retrieval options, and trust/handoff tests.
**Done when:** high-stakes retrieval excludes low-trust items until independently corroborated; handoff assembly respects the rough token budget; readback mismatches identify missing goals, decisions and open items; writer revocation removes its items and `derived_from` descendants; replay restores packets and keeps revoked views removed.
**Status:** Windows-verified on 2026-10-23 by the user: `56 passed` in 11.93s. The full test count includes the MCP stdio integration test; only a Starlette/httpx deprecation warning was reported.

## Phase 5 — Mini eval, shadow lifecycle, demo
**Goal:** an honest first look at flat vs graph, plus a runnable demo.
**Files implemented:** `eval/stale_facts.py`, lazy decay in `src/agm/trust.py` and graph ranking, `src/agm/cli.py` lifecycle command and handoff demo, `tests/test_eval.py`, `tests/test_lifecycle.py`, and updated README/docs.
**Done when:** evaluation compares flat and graph modes and carries the D-007 caveat; demo runs end to end offline through handoff/readback; dry-run lifecycle lists candidates without mutating events or memory views.
**Status:** Windows-verified by the user on 2026-10-23: `61 passed` in 20.24 seconds. Evaluation reported flat/graph accuracy 100%, stale-fact error 0%, abstention 0% flat / 25% graph, and 3 expanded items. Demo handoff readback passed; lifecycle dry run reported zero candidates and no mutations; packaging created the workspace and overlay ZIPs. Evaluation is a smoke test only; no H1–H7 conclusions are supported. The demo label was corrected to Phase 5 in a final polish patch; the updated builder suite reports 61 passed, 1 skipped in 2.71s. Rerun the final patch on Windows to include the new demo-label regression test alongside MCP.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task — it routes you to the right file for what you are about to do.


## Active Memory Loop v1 — in progress
**Goal:** make persistent memory useful across turns by providing a bounded context pack before generation and a conservative, evidence-aware policy after generation.
**Files added/changed:** `src/agm/active_memory.py`, `src/agm/models.py`, `src/agm/store.py`, `src/agm/api.py`, `src/agm/mcp_server.py`, `src/agm/__init__.py`, `examples/active_memory_loop.py`, `prompts/active_memory_system_prompt.md`, active-memory unit/API/MCP checks, REST and MCP integration guides, and the architecture/decision/status logs.
**Done when:** `memory_context` returns query-specific evidence, convention-tagged profile/goals/decisions, conflicts, provenance and abstention within the configured context-string budget; remember requires matching source evidence and uses stable idempotency only when a caller-supplied operation ID is present; correct requires explicit correction language and preserves history; forget requires an explicit non-negated request matching every selected target, supports up to 100 targets, and atomically deletes their full supersede chains or does nothing; health checks are read-only and scoped; the provider-neutral controller orders retrieve → generate → post-turn policy; REST/MCP tool parity is preserved without removing legacy names; tenant isolation and replay/delete behavior are verified.
**Implementation status:** Written on feature branch `feature/active-memory-loop-v1`. Tests have deliberately **not been run yet**, following the integrator's instruction to finish implementation before testing. Do not mark this work complete until the subsequent full test/smoke run and review pass.
**Known limits:** token count uses characters/4; category retrieval relies on existing attributes/text conventions; native MCP invocation is model-controlled and not guaranteed on every consumer-chat turn; current-message quote verification is strongest in a host-controlled loop. Remote exposure remains disabled pending security review.

