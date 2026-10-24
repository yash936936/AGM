# Decisions — AGM prototype

> Append-only. Newest entries at top. Never edit or delete past entries — if a decision is reversed, log a new entry that supersedes it and reference the old ID.

## D-025 — Phase 7 evaluation-validity and retrieval diagnostics — 2026-10-23
**Pre-registered corrections and targets:** Preserve D-024's 0.25 threshold, bootstrap method, baseline modes, graph verdict rule, and generated facts/relation chains. Correct only the identified evaluation ambiguity: multi-hop questions must state the generated hop distance, and graph mode should use its supported depth of two for the `multi_hop` family while keeping the default depth of one for other families. Exact catalogue-backed numeric-ID namespaces must reject a near-miss or missing ID before fuzzy retrieval; no similarity threshold is changed. For directed downstream questions, anchor expansion to the explicitly named entity, follow only relation edges supported by eligible relation facts, and prioritize requested-attribute results reached at the requested path depth. Batch graph corroboration lookups only if equivalence tests show that their semantics match the existing row helper.
**Success criteria set before the full rerun:** (1) graph answers at least 90% of the seeded multi-hop cases, with a unit test proving exact path-depth alignment; (2) all three modes correctly abstain on every generated unknown numeric service ID; (3) graph median latency improves by at least 50% relative to the saved Phase 6 Windows result (1,370 ms) and graph p95 is below 1,000 ms on the same configuration. Report the actual outcome even if any criterion misses. These are diagnostic acceptance targets, not a replacement for D-024's `PROMISING` decision rule.
**Why:** Inspection showed that multi-hop queries did not name the one- versus two-edge gold distance, graph retrieval used one hop by default, relation seeds could be chosen from a preceding service, and the top-50 global seed pool reintroduced unrelated candidates. Unknown `svc-012`/future `svc-N` queries shared high-overlap terms (`runtime`, `owner`, `svc`) with existing records, so the rank score was not a reliable abstention signal. Profiling found repeated corroboration SQL to dominate query time.
**Affects:** `src/agm/store.py`, `src/agm/retrieve.py`, `src/agm/trust.py`, `eval/synthetic_v2.py`, retrieval/evaluation tests, Phase 7 report and results. D-021 through D-024 remain unchanged.

## D-024 — Phase 6 evaluation v2 and pre-declared decision rule — 2026-10-23
**Decision:** Add a seeded offline evaluation with six question families (`single_fact`, `stale`, `entity_centric`, `multi_hop`, `temporal`, `unanswerable`) and three modes over the same seeded store and embedder: `flat`, `flat_filter`, and `graph`. Use the same `k` and one common evaluation abstention rule for all modes: abstain in the harness if no result is returned or the top returned score is below 0.25; report the store's own abstain flag separately. Report accuracy@k (entity-centric recall of the gold set), stale-error rate, abstention correctness, p50/p95 latency, mean returned items and mean expanded count, aggregated over seeds with a deterministic 1,000-resample bootstrap 95% confidence interval.
**Pre-declared decision rule (must not change after results exist):** Smoke-test rule (not evidence for H1–H7, see D-007): on a question family, graph is `PROMISING` only if its mean accuracy exceeds BOTH `flat` and `flat_filter` by at least 5 percentage points, the bootstrap CI of each graph-minus-baseline accuracy difference excludes zero, AND its stale-error rate is not worse. Report `NOT SHOWN` otherwise and `FLAT BETTER` when either baseline has higher mean accuracy. If graph does not meet this on `multi_hop` and `stale`, record exactly: `graph not shown to help in this smoke test`. Report every outcome, including where flat wins. Never tune the generator after seeing results to make graph win.
**Why:** The 4-scenario Phase 5 smoke test saturated at 100% accuracy for flat and graph and mixed expansion with different abstention behavior. Evaluation v2 gives the baseline a metadata-filter comparison and a broader set of deterministic stress cases while preserving `eval/stale_facts.py` for compatibility.
**Affects:** `eval/synthetic_v2.py`, `tests/test_eval_v2.py`, `eval/results/`, README, Phase 6 report. `sentence-transformers` is an optional lazy import used only by eval, never a hard dependency.

## D-023 — Standing builder guidelines and an expanded review checklist — 2026-10-23
**Decision:** `AGENTS.md` (root) holds the standing rules for any builder agent (ChatGPT, Codex, Claude Code); `prompts/builder_system_prompt.md` is the general prompt to paste once into a ChatGPT project or custom GPT; `prompts/phase_brief_template.md` is the template for each phase brief. The supervisor review checklist in `docs/workflow.md` now includes direct-library parity, surface parity, on-disk delete checks and a mandatory run of both smoke clients.
**Why:** The guard drifted into the adapters unnoticed for three phases because no checklist item compared the library surface with REST/MCP. Standing rules in the repo mean each new builder session starts from the same invariants instead of relying on a pasted prompt.
**Affects:** `AGENTS.md`, `prompts/`, `docs/workflow.md`, `context.md`.

## D-022 — Flush the WAL after delete and revoke; enable secure_delete — 2026-10-23
**Decision:** `delete` and `revoke_writer` run `PRAGMA wal_checkpoint(TRUNCATE)` after committing, and every connection sets `PRAGMA secure_delete = ON`. Revocation still preserves source event payloads for audit (README, D-017); only `delete` purges content.
**Why:** A mutation test showed deleted text stayed readable in the `-wal` file until a checkpoint, so a long-running server could keep it on disk indefinitely. `secure_delete` is defence in depth: the test suite does not prove it is required, the checkpoint is what the tests depend on.
**Affects:** `db.py`, `store.py`, `tests/test_delete_ondisk.py`.

## D-021 — The guard runs inside MemoryStore, not only at the adapters — 2026-10-23
**Decision:** `MemoryStore.write` and `MemoryStore.supersede` always call `inspect_write_item` (redact, then quarantine if instruction-like) before any event is appended or text embedded. `supersede` also redacts its `reason`, and `handoff_save` redacts every string in `TaskState` and the `session_id`. `guarded_write` remains as a thin wrapper that calls `store.write`. `write_quarantined` re-sanitizes its input. REST and MCP no longer contain safety logic. This supersedes the placement chosen in D-014 (boundary guard); the behaviour of D-014 is unchanged for REST and MCP callers.
**Why:** Direct library calls bypassed the guard. A key-shaped string written through the library was stored unredacted in `events` and `nodes`. The architecture's write path places redaction in the core. The supersede `reason` and handoff task state were unguarded on every surface.
**Affects:** `guard.py`, `store.py`, `api.py`, `mcp_server.py`, `tests/test_guard_core.py`.

## D-020 — Phase 5 evaluation is a synthetic smoke test — 2026-10-23
**Decision:** `eval/stale_facts.py` runs hand-authored corrected-fact, entity-owner, related-database, and unanswerable scenarios against `retrieve(expand=False)` and `retrieve(expand=True)`. Accuracy means an expected answer appears in returned items; stale-fact error means the old value appears for the corrected-fact scenario; abstention rate is abstained scenarios divided by all scenarios.
**Why:** A small offline evaluation makes the main paths and reporting executable before a labelled, preregistered benchmark exists. D-007 remains in force: these results are not evidence for or against H1–H7.
**Affects:** `eval/stale_facts.py`, Phase 5, README.

## D-019 — Lazy decay weight and dry-run lifecycle threshold — 2026-10-23
**Decision:** Compute graph-rank decay lazily from idle time, retrieval count, incoming `derived_from` citations and independent corroborations. Idle weight is `1 / (1 + idle_days / 365)`; bounded bonuses are added for usage, citations and up to two independent corroborations, and the result is clipped to `[0,1]`. Pinned items receive `1.0`. `agm lifecycle --dry-run` lists active, unpinned items below default threshold `0.30` but never changes state.
**Why:** This introduces an inspectable lifecycle signal without silently archiving user memory. All coefficients and the threshold are provisional and must not be treated as calibrated.
**Affects:** `src/agm/trust.py`, `src/agm/retrieve.py`, `src/agm/cli.py`, lifecycle tests.


## D-018 — Corroborate non-fact items by exact independent text — 2026-10-23
**Decision:** For items without an entity/attribute/value fact key (episodes and some procedures), high-stakes probation can be lifted when a different writer independently stores the exact same text in the same tenant and project. Fact items continue to corroborate by the canonical entity/attribute/value tuple or a matching corroboration event.
**Why:** Episodes and procedures do not always have a fact tuple, so otherwise low-trust entries could never leave probation. Exact text is intentionally conservative and does not try to infer semantic equivalence.
**Affects:** `trust.py`, Phase 4 probation tests, contract addendum.

## D-017 — Make handoff and revocation replayable — 2026-10-23
**Decision:** `handoff_save` appends a `handoff_save` event before materializing the packet. `revoke_writer` appends a rollback marker containing the affected node IDs and corroboration event IDs, then removes those items and dependent `derived_from` descendants from views. Original write payloads remain in the event log for audit; unlike `delete`, revocation is not a content-scrubbing operation.
**Why:** replay must reconstruct packet state and keep revoked content out of searchable views. Retaining source events preserves the audit trail, but means a revoke is not equivalent to hard deletion.
**Affects:** `events.py`, `store.py`, `trust.py`, `handoff.py`, replay and trust tests.

## D-016 — Add an explicit high-stakes gate and usable handoff result — 2026-10-23
**Decision:** Add the optional `high_stakes=False` argument to `MemoryStore.retrieve`, and pass it through REST and MCP. In high-stakes mode, `trusted_agent` and `untrusted` memories are probationary until at least one different writer independently confirms the same active fact. Extend `ResumeResult` with `context`, `readback_prompt`, `target_model`, `token_budget`, and `estimated_tokens`. Estimate context tokens as `ceil(characters / 4)` and cap the returned context at four characters per budget token.
**Why:** the previous retrieval contract had no way to request the Phase 4 probation rule, and `ResumeResult(goal, packet_id)` could not return the assembled context needed to continue work. Existing default retrieval and the flat-baseline toggle remain unchanged.
**Affects:** the frozen contract addendum, `models.py`, `store.py`, `retrieve.py`, `trust.py`, `api.py`, `mcp_server.py`, handoff tests.

## D-015 — Pin Phase 3 to the official FastMCP 1.x API — 2026-10-23
**Decision:** Phase 3 declares `mcp>=1.26,<2` and uses `mcp.server.fastmcp.FastMCP` for the nine contract-defined tools.
**Why:** The frozen Phase 3 brief explicitly names FastMCP. The official SDK's 2.x line renamed that server API, so pinning the maintained 1.x line avoids an unreviewed breaking API shift while preserving a standards-based MCP server/client interface.
**Affects:** `pyproject.toml`, `src/agm/mcp_server.py`, MCP integration tests.

## D-014 — Guard inputs at the REST/MCP boundary — 2026-10-23
**Decision:** REST and MCP writes pass through the same guard before the event append. Recognized secret patterns are replaced with `[REDACTED]`; instruction-like writes are recorded with `status="quarantined"` and are excluded from default retrieval and history responses. Services bind to loopback only.
**Why:** Redaction after persistence is too late because the raw value would remain in the event log or embedding input. Local-only exposure is the safe prototype default until a separate review approves remote deployment.
**Affects:** `config.py`, `guard.py`, `api.py`, `mcp_server.py`, `store.py`, interface tests.

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
