# Decisions — AGM prototype

> Append-only log. Newest entries at top. Never edit or delete past entries —
> if a decision is reversed, log a new entry that supersedes it and reference
> the old ID.

## D-010 — Hard delete scrubs the original event payload — 2026-10-22
**Decision:** `delete` removes the node and all derived data, replaces the originating event's payload with `{"scrubbed": true}`, and appends a content-free delete event. Replay skips scrubbed events.
**Why:** v5 says the log is append-only but also that hard deletion removes content everywhere (P13). Content left in the log would defeat deletion. Cost: the log is no longer strictly immutable for deleted items; rollback cannot restore them.
**Affects:** events.py, store.py, tests/test_replay.py.

## D-009 — Phase 1 includes packaging and a minimal CLI entry point — 2026-10-22
**Decision:** Phase 1 adds `pyproject.toml`, `__main__.py`, `cli.py` (`agm demo`, `agm rebuild`) and `scripts/pack.py`. Phase 3 extends `cli.py` with `serve-api` and `serve-mcp`.
**Why:** The builder must hand back a runnable, zippable project and the user needs a one-command smoke test. Dependencies stay pydantic and numpy only until Phase 3.
**Affects:** phases.md Phase 1, architecture.md file tree.

## D-008 — Confidence and ranking weights are uncalibrated placeholders — 2026-10-22
**Decision:** confidence = extraction_conf × tier_weight × (1 + 0.15 × min(independent_corroborations, 3)) × age_factor, clipped to [0,1]. Rank = 0.55 sim + 0.15 conf + 0.10 trust + 0.10 recency + 0.10 decay_weight. Abstain below score 0.25 after one widening. All proposed, none calibrated.
**Why:** v5 D3 and D7 are open and need labelled data. Placeholders let the pipeline run. Never report these scores as calibrated.
**Affects:** trust.py, retrieve.py, Phase 2, Phase 5 eval.

## D-007 — Prototype results are not evidence for H1–H7 — 2026-10-22
**Decision:** The Phase 5 eval is a smoke test. No hypothesis is called supported or refuted from it.
**Why:** v5 requires thresholds, tolerances and baselines fixed before measurement (D2). The prototype has a weak embedder, synthetic data written by us, and no pre-registration. Speed is the priority now; rigor comes with the real step 0.
**Affects:** phases.md Phase 5, readme.md wording.

## D-006 — Keep the flat baseline as a runtime toggle — 2026-10-22
**Decision:** `retrieve(expand=False)` is exactly the seed step and stays in the product.
**Why:** v5 says expansion must beat the flat step or be removed, and the kill criterion depends on being able to compare. Cheap to keep, costly to retrofit.
**Affects:** retrieve.py, eval.

## D-005 — Supervisor/builder protocol with frozen contracts — 2026-10-22
**Decision:** Claude writes docs, contracts and phase briefs and reviews code. A ChatGPT model writes code one phase at a time. Contracts in architecture.md are frozen; changes need a decision entry.
**Why:** Two different models drift apart without a shared spec. Contract-first keeps review mechanical.
**Affects:** workflow.md, all phases.

## D-004 — One core, two adapters (REST and MCP) — 2026-10-22
**Decision:** All logic in `MemoryStore`; `api.py` and `mcp_server.py` only authenticate and translate.
**Why:** Requirement is "connect to any agent". REST covers local agents and ChatGPT Actions; MCP covers Claude Code, Codex, Claude Desktop. One core means one set of tests.
**Affects:** architecture.md, Phase 3.

## D-003 — Default HashEmbedder, pluggable real embedder — 2026-10-22
**Decision:** Ship a dependency-free hashing embedder; allow sentence-transformers via an extra.
**Why:** Works offline in seconds, no model download blocking the first demo. Cost: weak semantic matching, so keyword (FTS5) carries more weight in seed. Eval results must note which embedder ran.
**Affects:** embed.py, eval.

## D-002 — Calling agent is the extractor — 2026-10-22
**Decision:** Clients send structured facts (entity, attribute, value, text, optional span). The server runs no LLM.
**Why:** Removes an API key and cost from the critical path and speeds the prototype. Cost: this skips v5's extraction risk (P2), so the prototype does not test it.
**Affects:** WriteItem contract, appflow.md.

## D-001 — Python and SQLite — 2026-10-22
**Decision:** Python 3.11+, single SQLite file with FTS5, brute-force cosine on numpy.
**Why:** Fastest path for the user's stack, zero services to run, enough for thousands of items. Revisit if Phase 5 shows latency trouble.
**Affects:** whole project.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
