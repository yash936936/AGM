# Decisions — AGM prototype

> Append-only log. Newest entries at top. Never edit or delete past entries — if a decision is reversed, log a new entry that supersedes it and reference the old ID.

## D-013 — Provisional 10-year age-factor scale — 2026-10-23
**Decision:** Until calibration data exists, `age_factor = 1 / (1 + age_days / 3650)`; ranking recency uses the same scale.
**Why:** D-008 names `age_factor` but does not define its function. This transparent, monotonic scale lets the Phase 2 pipeline run without claiming calibrated confidence.
**Affects:** `src/agm/trust.py`, Phase 2 and Phase 5 evaluation.

## D-012 — Abstention uses absolute evidence similarity — 2026-10-23
**Decision:** The 0.25 sufficiency gate checks absolute evidence relevance (query-token overlap plus cosine similarity), and widens once before abstaining. The D-008 composite rank remains the ordering score.
**Why:** The composite rank includes trust, confidence, recency and decay floors. Applying 0.25 to the composite alone can allow irrelevant queries to pass simply because a memory has a strong trust tier. This operational interpretation is provisional and must be tested in Phase 5.
**Affects:** `src/agm/retrieve.py`, `tests/test_retrieve.py`.

## D-011 — Persist resolved entity identity in event payloads — 2026-10-23
**Decision:** New add, supersede and contested event payloads record the resolved canonical entity plus the resolved IDs/canonical names of relation targets.
**Why:** A source event can be scrubbed during hard deletion. A later event written through an alias still needs to replay against the same canonical entity and graph target, even after the alias-declaring event has been scrubbed.
**Affects:** `src/agm/store.py`, replay tests. Public Pydantic contracts and SQLite schema remain unchanged.

## D-010 — Hard delete scrubs the original event payload — 2026-10-22
**Decision:** `delete` removes the node and all derived data, replaces the originating event's payload with `{"scrubbed": true}`, and appends a content-free delete event. Replay skips scrubbed events.
**Why:** Draft v5 says the log is append-only but also that hard deletion removes content everywhere (P13). Content left in the log would defeat deletion. Cost: the log is no longer strictly immutable for deleted items; rollback cannot restore them.
**Affects:** `events.py`, `store.py`, replay tests.

## D-009 — Phase 1 includes packaging and a minimal CLI entry point — 2026-10-22
**Decision:** Phase 1 adds `pyproject.toml`, `__main__.py`, `cli.py` (`agm demo`, `agm rebuild`) and `scripts/pack.py`. Phase 3 extends `cli.py` with `serve-api` and `serve-mcp`.
**Why:** The builder must hand back a runnable, zippable project and the user needs a one-command smoke test. Dependencies stay pydantic and numpy only until Phase 3.
**Affects:** Phase 1, architecture file tree.

## D-008 — Confidence and ranking weights are uncalibrated placeholders — 2026-10-22
**Decision:** confidence = extraction_conf × tier_weight × (1 + 0.15 × min(independent_corroborations, 3)) × age_factor, clipped to [0,1]. Rank = 0.55 sim + 0.15 conf + 0.10 trust + 0.10 recency + 0.10 decay_weight. Abstain below 0.25 after one widening. All proposed, none calibrated.
**Why:** Draft v5 D3 and D7 are open and need labelled data. Placeholders let the pipeline run. Never report these scores as calibrated.
**Affects:** `trust.py`, `retrieve.py`, Phase 2 and Phase 5 evaluation.

## D-007 — Prototype results are not evidence for H1–H7 — 2026-10-22
**Decision:** The Phase 5 eval is a smoke test. No hypothesis is called supported or refuted from it.
**Why:** Draft v5 requires thresholds, tolerances and baselines fixed before measurement. The prototype has a weak embedder, synthetic data written by us, and no pre-registration. Speed is the priority now; rigor comes with the real step 0.
**Affects:** Phase 5, public README wording.

## D-006 — Keep the flat baseline as a runtime toggle — 2026-10-22
**Decision:** `retrieve(expand=False)` is exactly the seed step and stays in the product.
**Why:** Draft v5 says expansion must beat the flat step or be removed, and the kill criterion depends on being able to compare. Cheap to keep, costly to retrofit.
**Affects:** `retrieve.py`, evaluation.

## D-005 — Supervisor/builder protocol with frozen contracts — 2026-10-22
**Decision:** Claude writes docs, contracts and phase briefs and reviews code. A ChatGPT model writes code one phase at a time. Contracts in `architecture.md` are frozen; changes need a decision entry.
**Why:** Two different models drift apart without a shared spec. Contract-first keeps review mechanical.
**Affects:** workflow, all phases.

## D-004 — One core, two adapters (REST and MCP) — 2026-10-22
**Decision:** All logic in `MemoryStore`; `api.py` and `mcp_server.py` only authenticate and translate.
**Why:** REST covers local agents and ChatGPT Actions; MCP covers Claude Code, Codex and Desktop. One core means one set of tests.
**Affects:** architecture, Phase 3.

## D-003 — Default HashEmbedder, pluggable real embedder — 2026-10-22
**Decision:** Ship a dependency-free hashing embedder; allow sentence-transformers via an extra.
**Why:** Works offline without a model download. Cost: weak semantic matching, so keyword retrieval remains important. Evaluation must record the embedder used.
**Affects:** `embed.py`, evaluation.

## D-002 — Calling agent is the extractor — 2026-10-22
**Decision:** Clients send structured facts (entity, attribute, value, text, optional span). The server runs no LLM.
**Why:** Removes an API key and cost from the critical path. Cost: this skips Draft v5 extraction risk P2, so the prototype does not test it.
**Affects:** `WriteItem`, `appflow.md`.

## D-001 — Python and SQLite — 2026-10-22
**Decision:** Python 3.11+, single SQLite file with FTS5, brute-force cosine on numpy.
**Why:** Fastest path for the user's stack, zero services to run, enough for thousands of items. Revisit if Phase 5 shows latency trouble.
**Affects:** whole project.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task — it routes you to the right file for what you are about to do.
