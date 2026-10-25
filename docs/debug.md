## DBG-054 — Fix lifecycle context compatibility and trust-boundary regressions — 2026-10-26

**Finding:** Review of merged PR #32 found three regressions: `token_budget` was inserted before existing dataclass fields and broke positional callers; shared bounded rendering omitted stored provenance; and memory text with newlines / a forged closing record tag could break record framing.

**Change:** Append the new field after all prior fields, include provenance in `_render_item`, normalize untrusted field values to one line, escape angle-bracket delimiters, and test positional compatibility, provenance retention and boundary escaping.

**Validation:** Prior PR #32 exact-head CI run [40221564276](https://github.com/yash936936/AGM/actions/runs/40221564276) passed all six matrix jobs. Initial follow-up CI run [40222469817](https://github.com/yash936936/AGM/actions/runs/40222469817) exposed two fixture failures: a 180-token budget was insufficient after provenance was added, and the boundary fixture used literal backslash-n characters. Fixtures corrected (budget 240; actual newline input). Latest-head run [40222677766](https://github.com/yash936936/AGM/actions/runs/40222677766) queued. Local tests NOT RUN. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY.

---

## DBG-054 — Fix lifecycle context compatibility and trust-boundary regressions — 2026-10-26

**Finding:** Review of merged PR #32 found three regressions: `token_budget` was inserted before existing dataclass fields and broke positional callers; shared bounded rendering omitted stored provenance; and memory text with newlines / `</memory_records>` could break the record framing.

**Change:** Append the new field after all prior fields, include provenance in `_render_item`, normalize untrusted field values to one line, escape angle-bracket delimiters, and test positional compatibility, provenance retention and boundary escaping.

**Validation:** Prior PR #32 exact-head CI run [40221564276](https://github.com/yash936936/AGM/actions/runs/40221564276) passed all six matrix jobs. New follow-up tests NOT RUN locally; follow-up exact-head CI pending. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY.
## DBG-054 — Repair M1 lifecycle review findings — 2026-10-26

**Finding:** Review of merged PR #32 surfaced a positional API compatibility break, dropped `Node.provenance` in shared context rendering, and a record-boundary injection risk when memory text contains embedded line breaks.

**Change candidate:** Append `token_budget` after all existing `BeforeTurnRequest` fields; include stable JSON-serialized provenance in each rendered record; flatten carriage returns/newlines in untrusted record text; add regression tests for the three behaviors.

**Baseline evidence:** PR #32 merged at `63826e826a2de02ec83fb284acae687f17293025`; exact-head CI run [40221564276](https://github.com/yash936936/AGM/actions/runs/40221564276) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. That run predates this fix and is not evidence for it.

**Validation:** Exact-head CI run [40222174178](https://github.com/yash936936/AGM/actions/runs/40222174178) failed on Ubuntu Python 3.11 and 3.13: the budget test's short record no longer fit after provenance metadata was added, and the injection fixture encoded literal `\
` text rather than actual line breaks. The budget was increased while retaining oversized-record exclusion; the fixture now uses real line breaks, and a focused renderer test verifies provenance serialization. This correction is committed after the failed run; a fresh exact-head CI run is required. Local tests NOT RUN in this remote editing environment. M0 IN PROGRESS; M1 PARTIAL / VERIFY.

---

## DBG-053 — Bound the lifecycle before-turn memory context — 2026-10-25

**Finding:** `MemoryLifecycle.before_turn()` previously formatted all retrieved nodes into `context_text` without a character/token budget, despite the M1 context contract requiring bounded evidence. Its `top_k` validation also accepted booleans and non-integer values until deeper layers handled them.

**Change:** Reuse `active_memory.prepare_turn_context()` as the single budgeted renderer; add `token_budget` to `BeforeTurnRequest`; strictly validate positive integer limits; and add tests for budget enforcement, omission of an oversized record, and exact correspondence between returned IDs and context contents.

**Validation:** Branch `fix/m1-bounded-before-turn-context`; exact-head CI pending. Local tests NOT RUN in this remote editing environment. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY.

---

## DBG-052 — Quarantined content must not appear in graph snapshots — 2026-10-25

**Finding:** `graph_snapshot()` scoped nodes by tenant/project but did not filter `status='quarantined'`. This could expose instruction-like content that ordinary retrieval and Obsidian export intentionally suppress.

**Change:** Exclude quarantined nodes from snapshot node selection and from both edge-endpoint subqueries. Added `test_graph_snapshot_omits_quarantined_instruction_like_memory`, which verifies the write is quarantined and the node ID/content marker are absent from the snapshot.

**Validation:** Branch `fix/m1-snapshot-quarantine-filter`; exact-head CI pending. Local tests NOT RUN in this remote editing environment. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY.

---

## DBG-051 — Expiry rollback when final orphan scrub fails — 2026-10-25

**Task:** Exercise the other late-failure boundary of `expire_before`: the sweep has already deleted an eligible live item, then fails while scrubbing a revoked-writer orphan event.

**Test added:** `test_expiry_rolls_back_deletes_when_orphan_scrub_fails` uses an SQLite trigger to abort the source-payload scrub. It verifies the earlier live-item deletion is rolled back, the orphan remains absent due to the prior revocation, both source payloads and event count remain unchanged, the transaction closes, and reopen/rebuild preserves the expected state.

**Merged baseline:** PR [#29](https://github.com/yash936936/AGM/pull/29), merge commit `85b8c55555866fa67ad1008b073b28429e73a798`; exact-head CI run [40219869374](https://github.com/yash936936/AGM/actions/runs/40219869374) passed all six Linux/Windows Python 3.11–3.13 jobs.

**Validation:** Candidate branch `test/m0-orphan-scrub-rollback`; exact-head CI pending. Local tests NOT RUN in this remote editing environment. M0 remains IN PROGRESS; real-history evaluation and independent security/privacy review remain open.

---

## DBG-050 — Multi-item expiry sweep rollback regression — 2026-10-25

**Task:** Extend atomicity coverage beyond a single expired item. A one-item test can prove rollback of that item's nested mutation but cannot prove that earlier deletes in the same sweep are restored if a later delete fails.

**Test added:** `test_expiry_rolls_back_prior_items_when_later_nested_delete_fails` creates two aged items in one tenant/project, snapshots source payloads and event count, calls the real delete handler for each nested delete, and injects failure after the second handler has mutated views. It asserts both source payloads, event count, and both active nodes are restored, no transaction remains open, and both markers remain retrievable after reopen/rebuild.

**Validation:** Candidate branch `test/m0-multi-item-expiry-rollback`; exact-head CI pending. Local tests NOT RUN in this remote editing environment. M0 remains IN PROGRESS; held-out real-history evaluation and independent security/privacy review remain open.

---

## DBG-049 — Post-mutation expiry rollback regression merged — 2026-10-25

**Merged:** PR [#28](https://github.com/yash936936/AGM/pull/28), merge commit `9db3fbaf9dc3a039f2198b6c61e9340619df7f9b).

**Finding addressed:** The previous regression injected failure before the real delete handler mutated views. The updated test invokes the original `_apply_delete_payload`, records that it ran, and then raises an injected exception from within the expiry sweep.

**Evidence:** Exact-head CI run [40219212770](https://github.com/yash936936/AGM/actions/runs/40219212770) passed all six Linux/Windows Python 3.11–3.13 jobs, including tests, repository hygiene, whitespace checks, and wheel/package inspection. Assertions cover restored source payload, unchanged event count, active node, closed transaction, and retrieval after database reopen and view rebuild.

**Limits:** Local tests NOT RUN in this remote editing environment. Synthetic rollback evidence does not establish real-history quality or independent security/privacy review. M0 remains IN PROGRESS; held-out real-history evaluation and independent security/privacy review remain open.

---

## DBG-048 — Strengthen expiry rollback injection after view mutation — 2026-10-25

**Review finding:** PR [#27](https://github.com/yash936936/AGM/pull/27) passed exact-head CI run [40218590007](https://github.com/yash936936/AGM/actions/runs/40218590007), all six Linux/Windows Python 3.11–3.13 jobs. Post-merge review correctly noted that its failure hook raised before the real nested delete handler changed derived views.

**Follow-up change:** The revised test calls the original `_apply_delete_payload` first, records that the handler ran, and then raises an injected exception. It verifies the expiry operation restores the source payload, event count and active node, closes the transaction, and leaves the marker retrievable after reopen/rebuild. This exercises rollback after the real nested handler has performed its view mutation, rather than only failure before mutation.

**Validation:** Candidate branch `test/m0-expiry-post-mutation-rollback`; exact-head CI pending. Local tests NOT RUN in this remote editing environment. Synthetic failure injection is not independent security/privacy review. M0 remains IN PROGRESS; held-out real-history evaluation and independent security/privacy review remain open.

---

## DBG-047 — M0 expiry sweep atomic rollback regression — 2026-10-25

**Task:** Verify that retention expiry is atomic across its nested delete operations.

**Test added:** `test_expiry_rolls_back_entire_sweep_when_nested_delete_fails` injects a failure while applying the nested delete event, then asserts the original source payload and event count are unchanged, the node remains active, no transaction is left open, and reopen/rebuild still retrieves the marker.

**Validation:** NOT RUN locally in this remote editing environment. Exact-head CI is required. This is synthetic failure-injection evidence, not independent security/privacy review. M0 remains IN PROGRESS; held-out real-history evaluation and independent security/privacy review remain open.

---

## DBG-046 — M0 retention orphan-scrub isolation merged — 2026-10-25

**Merged:** PR [#26](https://github.com/yash936936/AGM/pull/26), merge commit `f68aa2878e662ee7cb46099612aef27d60cfb4d1`.

**Evidence:** Exact-head CI run [40217991980](https://github.com/yash936936/AGM/actions/runs/40217991980) passed all six Linux/Windows Python 3.11–3.13 jobs, including tests, repository hygiene, whitespace, and wheel/package inspection.

**Regression:** Aged source events in the target tenant/project, a sibling project, and a sibling tenant are created. After target-writer revocation, expiry scrubs only the target orphan, a second expiry scrubs zero additional events, and reopen/rebuild preserves the expected retrieval visibility boundary.

**Limits:** Synthetic test evidence only. Local tests were not run in this remote editing environment; the test does not establish real-history quality, compliance, or external backup/WAL erasure. M0 remains IN PROGRESS; held-out real-history evaluation and independent security/privacy review remain open.

---

## DBG-045 — M0 retention orphan-scrub tenant/project isolation — 2026-10-25

**Task:** Strengthen M0 acceptance coverage for aged content-bearing source events that become orphans after writer revocation.

**Test added:** `test_expiry_scrubs_revoked_orphans_only_in_requested_tenant_project_after_replay` creates synthetic aged writes in the requested tenant/project, a sibling project, and a sibling tenant. It revokes the target writer, runs expiry twice to check idempotency, verifies only the target project's orphan payload is scrubbed, then rebuilds views after reopening and checks that the revoked marker stays absent while both out-of-scope markers remain retrievable.

**Validation:** NOT RUN locally in this remote editing environment. Exact-head CI is required. The regression uses synthetic data and does not establish compliance or prove external backup/WAL erasure. M0 remains IN PROGRESS; held-out real-history evaluation and independent security/privacy review remain open.

---

## DBG-044 — Post-merge audit: connection validation CI and duplicate test cleanup — 2026-10-25

**Merged change:** PR [#24](https://github.com/yash936936/AGM/pull/24), merge commit `571edd5082b10bfcce169d4e3fddddedee1e8aeb`, rejects explicit empty/malformed connection scopes and non-finite/non-positive diagnostic timeouts. Exact-head GitHub Actions run [40216605734](https://github.com/yash936936/AGM/actions/runs/40216605734) passed all six Ubuntu/Windows Python 3.11–3.13 jobs, including tests, repository hygiene, whitespace and wheel/package inspection.

**Post-merge audit finding:** The validation test block was accidentally appended twice, defining duplicate test names. Removed the duplicate block in branch `chore/post-merge-audit-cleanup`; the original parameterized coverage remains once. This cleanup itself is unverified until exact-head CI passes. Local tests were NOT RUN in this environment.

---

## DBG-043 — Validate connection scopes and diagnostic timeouts — 2026-10-25

**Finding:** `create_connection()` used a truthiness fallback for scopes, so an explicitly empty scope list silently became `memory:read` instead of failing closed. Non-list/unhashable scope values could leak `TypeError`. `test_connection()` accepted invalid timeout values, which could escape as inconsistent runtime exceptions.

**Change:** Apply the least-privilege default only when scopes are omitted (`None`); require explicit scopes to be a non-empty list of strings in the allowlist. Require diagnostic timeout to be a finite positive number and reject booleans.

**Tests added:** malformed/empty scope values and timeout type/boundary cases. Local tests were NOT RUN in this environment; exact-head CI is required.

---

## DBG-023 — RSS API fix, repeatable load runs, synthetic acceptance suite, and keyword baseline — 2026-10-25
**CI follow-up:** Initial run [40211567298](https://github.com/yash936936/AGM/actions/runs/40211567298) found a lexical-baseline test failure: the tokenization regex matched a literal backslash sequence, yielding zero recall. Corrected the regex on the latest branch head. The follow-up exact-head matrix is [run 40211660005](https://github.com/yash936936/AGM/actions/runs/40211660005), currently queued; do not consider this increment verified until it completes.


**Task:** Continue benchmark hardening after the first successful Windows synthetic smoke run reported `process_peak_rss_bytes: null`.

**Changed:** The Windows RSS query now loads Kernel32/PSAPI explicitly and declares ctypes argument/return types for the process handle and memory-counter structure. Added `--repetitions` (1–50) to rerun the complete benchmark and retain each run's concurrent latency percentiles, throughput and errors alongside across-run percentile summaries. Added a 10-case labelled synthetic suite for recall/relevance, abstention, correction, deletion, revocation, expiry and tenant isolation. Added a transparent token-overlap lexical baseline to paired reports and as `python -m eval.keyword_baseline`.

**Tests added:** Windows CI requires a non-null positive RSS result; tests cover keyword lifecycle handling, repeated-run aggregation and suite scenario coverage.

**Validation:** Exact-head CI is pending. No local test results are claimed from this remote editing step. Run the synthetic suite on the target Windows checkout and inspect the RSS field. If it remains null, preserve that as an unavailable metric and investigate the platform API separately. Held-out real-history evaluation and independent security/privacy review remain NOT RUN / NOT ESTABLISHED.

## DBG-022 — Peak RSS and concurrent retrieval load measurements — 2026-10-25

**Task:** Continue performance instrumentation after PR #14.

**Changed:** Added best-effort peak resident/working-set memory capture for Windows and Unix-like systems without adding a dependency. Added opt-in concurrent retrieval load execution against each evaluated case database, reporting worker count, requests, errors, p50/p95/p99, throughput, and elapsed time. Protocol version advanced to `paired_flat_vs_graph_v3`.

**Tests added:** Peak RSS is checked for a valid positive value when available; concurrent retrieval tests assert request counts, no errors, latency, throughput, and that dataset filenames remain absent.

**Validation:** NOT RUN yet for this branch. CI and full suite must pass before merge. Concurrent results are synthetic fixture diagnostics, not production capacity claims. Real-history evaluation and independent security/privacy review remain NOT RUN / NOT ESTABLISHED.

## DBG-021 — Benchmark privacy and operation timing follow-up — 2026-10-25

**Task:** Address review follow-ups from merged PR #13.

**Changed:** Aggregate paired benchmark output no longer emits the input dataset filename. The real-history evaluator records per-write, lifecycle mutation, and rebuild/replay durations; the paired runner aggregates p50/p95/p99 and sample counts by operation. Protocol version advanced to `paired_flat_vs_graph_v2`.

**Tests added/updated:** Paired runner asserts protocol version, omission of dataset filename, and operation timing summaries for write and rebuild/replay.

**Validation:** NOT RUN in this remote editing step. Exact-head CI and the full suite must pass before merge. Peak RSS, concurrent-load throughput, and a standalone keyword baseline remain open. Real-history evaluation and independent security/privacy review remain NOT RUN / NOT ESTABLISHED.

## DBG-020 — Paired flat-vs-graph benchmark harness — 2026-10-25

**Change:** Added `eval/benchmark_runner.py` to evaluate each labelled case in both flat and graph modes using isolated temporary SQLite databases. It reports retrieval and end-to-end p50/p95/p99, expected-value recall, case pass rate, abstention accuracy, forbidden-value leakage, cases/second and maximum SQLite file size. Default reports omit case IDs and memory content. The real-history evaluator records retrieval-call duration and database file size.

**Test added:** `tests/test_benchmark_runner.py` covers both modes, metric output, gate status and omission of case identifiers.

**Verification:** Base commit `f7def22501b12693488354ea8e37a1476e6f67a7` passed six Ubuntu/Windows Python 3.11–3.13 jobs in [run 40202107198](https://github.com/yash936936/AGM/actions/runs/40202107198). New code has NOT RUN locally because GitHub DNS resolution failed during clone. Candidate exact-head CI remains pending.

**Not closed:** Held-out real-history evaluation and independent security/privacy review remain NOT RUN / NOT ESTABLISHED. RSS, concurrent-load throughput and a separate keyword baseline remain unimplemented or unmeasured.
## DBG-019 — Owner bootstrap, session lifecycle, and connection registry — 2026-10-25

**Change under review:** PR [#11](https://github.com/yash936936/AGM/pull/11) adds a local bootstrap CLI, scoped persistent session routes, loopback-only REST connection registry/health probes, focused tests, a Windows/Linux Python 3.11–3.13 CI matrix, and wheel content inspection.

**Security boundaries:** bootstrap refuses to overwrite an existing key file and does not print the generated key to stdout; the generated key remains in a local file and must be protected. Connection records store endpoint metadata and memory scopes only, not connection secrets. Diagnostic probes disable proxy use and accept only loopback HTTP endpoints.

**Validation:** Exact-head CI is pending. Local execution is unavailable because GitHub DNS resolution failed when attempting to clone the repo. External held-out real-history evaluation and independent security/privacy review are NOT RUN / NOT ESTABLISHED.

**Revocation update:** main commit `bffa7ff652df55308004a867ab2a6dec9f1c24cb` passed all 193 tests on Python 3.11, 3.12 and 3.13 in run 40193212194, including the cutoff-revocation regression. This is exact-head evidence for that main commit, not for the new PR branch.

## DBG-018 — Local hub views and export increment — 2026-10-25
**Branch:** `feat/m0-m1-completion`; PR #10.
**Changed:** Added `src/agm/local_hub.py` for project-scoped timeline metadata, deterministic graph snapshots, and guarded Obsidian Markdown export; added `tests/test_local_hub.py` for scope, payload minimization, deterministic snapshots, secret redaction and copy semantics. Added D-030 and `M0_M1_IMPLEMENTATION_REVIEW.md`.
**Review limits:** This is not full M1. Owner authentication/bootstrap, session lifecycle, connection registry and actual connection diagnostics are not implemented by this increment. M0 exact-head acceptance and real-history/security review remain open.
**Tests:** Local pytest NOT RUN: this execution environment could not resolve GitHub for cloning. GitHub Actions run 40192632664 was triggered by PR #10; result must be checked before reporting CI status. Do not report tests as passing until that run completes.
**Next:** Inspect exact-head CI output; fix any regression; continue remaining owner/session/connection M1 work and M0 acceptance gates.

## DBG-017 — Fast-track plan reconciled with current repository — 2026-10-25
**Task:** Inspect the supplied fasttrack.zip against context.md, AGENTS.md, current roadmap/status/decisions, and GitHub CI; revise the plan before code changes.

**ZIP inspection:** The archive contains three files only: prompts/m0_m1_fast_track.md, scripts/verify_all.py, and tests/test_m0_open_gaps.py. It is a plan/test overlay, not a complete repository snapshot. Its premise of “187 tests pass” and missing M0/M1 features conflicts with the current checkout and the documented October 25 status. The current main tree does not contain tests/test_m0_open_gaps.py. Do not apply it wholesale or add these tests without validating each gap against current contracts.

**Current main head:** fb732d2e49bc99205cd14964a9d0ba01163bfbb0 (merge of fix/revocation-replay-corrective). Added a revised plan at prompts/fasttrack_debug_plan_revised.md on branch debug/revocation-replay-fasttrack-review, commit e8356e7bd5fd19472a23fbb850e345b8f1116711. No runtime code changed in this review.

**Critical current failure:** GitHub Actions run 40189884890, exact main head fb732d2e49bc99205cd14964a9d0ba01163bfbb0, failed on Python 3.11, 3.12 and 3.13. Each reports 1 failed, 189 passed, 1 warning. The failed test is tests/test_privacy_edge_acceptance.py::test_revocation_since_cutoff_preserves_older_memory_after_rebuild_and_reopen. The later item is absent immediately after revoke_writer, but returns after reopening and rebuild_views. Repository hygiene and git diff --check passed in those jobs. This is NOT fixed.

**Plan change:** Make the revocation replay regression the first code task. Investigate the event metadata/payload and final replay enforcement before changing M0 or adding M1. After repair, validate retention/expiry against D-028/D-029, then inventory genuine M0 gaps using docs/M0_ACCEPTANCE_MATRIX.md and only then do an evidence-based M1 feature gap analysis. The ZIP's broad owner auth, connection/session tables, UI, export implementation, version bump and temporal validation list are not pre-approved implementation work.

**Validation:** Repository files and the current main Actions run/logs were inspected remotely. Local test execution, Windows execution, smoke clients, pack inspection and the candidate branch runtime fix are NOT RUN. Do not claim otherwise.

**Next:** Fix replay so cutoff revocation is durable across close/open/rebuild, older items remain and tenant isolation is preserved. Run focused test, full test suite and hygiene/whitespace checks, then exact-head CI on all supported Python versions. Do not merge until those gates pass.

## DBG-015 — Require mutation operations for mutation scenario labels — 2026-10-25
**Task:** Prevent benchmark cases from claiming correction, deletion, or revocation coverage through a scenario label without running the matching store operation.

**Changes:** `load_cases` now requires `correction` for `current_vs_stale`, `delete` for `deletion`, and `revoke_writer` for `revocation`. Added parameterized negative tests for all three mislabeled cases. This supplements DBG-014's end-to-end synthetic operation cases and prevents false acceptance coverage.

**Validation:** CI run [40124931082](https://github.com/yash936936/AGM/actions/runs/40124931082), commit `5122f24f1bcc7bd40ec7607f6d28bdeb28e2bffa`: 174 passed, 1 warning on Python 3.11 (12.12s), Python 3.12 (13.19s), and Python 3.13 (14.96s). Repository hygiene and `git diff --check` passed. The completion report refresh after this run triggers a new final-head CI run.

**Still open:** Local Windows regression and smoke clients, simulation and packaging remain NOT RUN here. Retention/expiry mutation policy remains unimplemented. Real-history evaluation is NOT RUN; security/privacy review is NOT ESTABLISHED.


## DBG-014 — M1 evaluator exercises mutation operations through replay — 2026-10-25
**Task:** Close a release-gate gap where deletion/revocation scenario tags were only labels, not actual tested operations.

**Changes:** Extended the benchmark schema with explicit `operations` supporting correction via `MemoryStore.supersede`, hard delete via `MemoryStore.delete`, and writer rollback via `MemoryStore.revoke_writer`. The evaluator closes/reopens between each operation, rebuilds views from the event log, then retrieves and scores expected/forbidden values and abstention. Missing expected values no longer fail the recall threshold when the benchmark contains no expected-value assertions; the case-pass and zero-tolerance criteria still apply.

**Tests added:** An end-to-end correction test verifies the new current value is found and the old value is forbidden after replay; a hard-delete test verifies the forbidden marker remains absent after rebuild and expects abstention; a writer-revocation test verifies the revoked writer's marker remains absent after replay and expects abstention. Each test uses synthetic markers only.

**Validation:** Branch CI run [40124787565](https://github.com/yash936936/AGM/actions/runs/40124787565), commit `20ea048a887ad9b31a36a7615ac12f841cdfea01`, reports `171 passed, 1 warning` on Python 3.11 (9.46s), 3.12 (13.68s), and 3.13 (15.78s). These are actual GitHub Actions test outputs, not local Windows output. The subsequent documentation update is a new tree and must receive its own CI run.

**Not run:** local Windows full test suite, MCP and REST smoke clients, active-memory simulation, `eval/stale_facts.py`, package inspection and Windows working-tree hygiene. Consented real-history benchmark and security/privacy review remain not run/not established.

**Contract concerns:** no frozen public API or required dependency was changed. Default evaluator thresholds remain provisional and must be preregistered for a held-out benchmark.

**Task:** Reconcile the M0 matrix with actual public CI evidence and harden the M1 evaluation harness so benchmark schema, scenario coverage, threshold failures, and zero-tolerance leak cases are explicit.

**Changes:** Updated `docs/M0_ACCEPTANCE_MATRIX_ADDENDUM.md` to record successful public CI jobs tied to baseline commit `f150a1996bda6292fae295c65ce14d9faf17a06b`, while preserving later-code rerun, real-history, and security/privacy review as separate gates. Hardened `scripts/evaluate_real_history.py` with named scenario validation, zero-tolerance scenarios (`tenant_isolation`, `deletion`, `revocation`), benchmark input validation, default minimum case pass rate and expected recall of 0.95, configurable thresholds, threshold failure reporting, scenario coverage, and a separate release-gate result. Expanded evaluator regression tests for missing expected values, forbidden leaks, wrong abstention, malformed fixtures, duplicate IDs, zero-tolerance sentinel requirements, and a correct tenant-isolation case. No new dependency and no frozen API/REST/MCP contract changes.

**Evidence found before this task:** Public CI run [40118798582](https://github.com/yash936936/AGM/actions/runs/40118798582), baseline commit `f150a1996bda6292fae295c65ce14d9faf17a06b), had successful Python 3.11, 3.12, and 3.13 jobs: `153 passed, 1 warning` in each job (10.99s, 14.02s, and 11.89s respectively). The warning is Starlette/httpx deprecation. This predates the current M1 hardening commits.

**Validation during this task:** GitHub Actions workflow runs for documentation and evaluator edits were triggered on branch `work/m0-m1-completion`. Earlier targeted test runs after the first test-file update reported successful CI; final runs for evaluator changes are pending at time of entry. No claim is made that the newest evaluator changes pass until the newest run completes and is inspected. No local Python runtime is available through this GitHub-only execution path, so local tests, both host smoke clients, simulation, packaging, and Windows-specific verification are NOT RUN here.

**Not finished:** The synthetic benchmark still does not exercise actual store-level delete/revoke operations by scenario; its contract currently evaluates seeded retrieval cases and treats scenario tags as acceptance classification. Dedicated store tests in M0 cover deletion/replay/revocation separately. Real consented held-out evaluation and production privacy/security sign-off are NOT RUN/NOT ESTABLISHED. A Windows run of the full `debug.md` checklist is still required.

**Contract concerns / assumptions:** Defaults of 0.95 for case pass rate, expected-value recall, and abstention accuracy are provisional operational defaults for the evaluator CLI, not established real-user quality targets. They must be preregistered/reviewed before any held-out run; command-line overrides are available. Zero-leak rules apply to the named scenario classes. No raw benchmark cases are written to aggregate reports.


> Append-only. Every completed coding task gets an entry here, even "no
> issues found." Newest entries at top.

## DBG-012 — Optional Gemini provider for Phase 8 live-agent testing — 2026-10-24
**Task:** Add a second real-model provider to the Phase 8 RAG demo so paired flat/graph retrieval can be evaluated with Gemini without adding a mandatory dependency.
**Changes:** Adds `--provider gemini`, lazily imports the official `google-genai` package, reads `GEMINI_API_KEY` and optional `GEMINI_MODEL` (default `gemini-3.8-flash`), passes system instructions to the model, and logs response ID/model version/token counts/block/finish status when present. Missing SDK/key and empty/safety-blocked response paths return explicit errors without logging the key. OpenAI and offline modes remain supported. Mocked tests do not make network calls.
**Data use:** Gemini API Free Tier prompt/output content may be used by Google to improve products. Use the synthetic Phase 8 database, not private or production memories, unless data-use terms have been reviewed.
**Validation:** API implementation validated with mocked SDK; no live Gemini request was made here. Live validation requires the user's Google AI Studio key and available free-tier model limits. Gemini docs: https://ai.google.dev/gemini-api/docs/billing and https://ai.google.dev/gemini-api/docs/pricing.

## DBG-011 — Phase 8 temporal/entity retrieval, corpus sweep and Memory Doctor — 2026-10-24
**Task:** Diagnose temporal retrieval and entity-centric ranking, build an ingestible mixed-context corpus, profile flat/graph retrieval across different corpus sizes and episode densities, instrument a sample agent loop, and add Memory Doctor.
**Changes:** `src/agm/retrieve.py` now recognizes entity-summary intent, prioritizes exact entity/attribute answer slots, and uses exact entity+attribute evidence for a temporal query only after the existing `as_of` eligibility filter. The D-024 threshold stays 0.25. Added a 44-record JSONL corpus, an idempotent guarded ingester, `agm doctor`, JSONL SQL/retrieval/event diagnostics, a flat/graph corpus-matrix harness, and offline/optional OpenAI agent runner. `--include-content` is explicit opt-in; default traces contain hashes and metadata rather than raw query/body text.
**Sample ingest:** 44 input records; 42 returned `added`, 1 `superseded`, 1 `quarantined`; 44 nodes and 44 tenant events on a fresh database. The expected instruction-like sample is quarantined. Memory Doctor completed 8 probes (entity-centric, direct owner, historical owner, unknown ID × flat/graph); all sample-probe correctness was 100%. SQLite integrity, missing FTS/embedding coverage, orphan edges/rows, active/temporal consistency, duplicate active fact keys and alias collisions are checked; the one quarantined item is an INFO diagnostic, not an audit error.
**Size/context matrix:** sizes 12/25/50; sparse/balanced/dense context (0/1/4 free-form episodes per entity); seeds 0/1/2; `k=8`; flat and graph; 27 cells total. Graph accuracy was 100% in each cell and unanswerable abstention correctness was 100%; flat accuracy averaged about 79.2% at size 12, 74.6% at size 25, and 67.9% at size 50. Graph p50 ranged from ~3.19 ms (12/sparse) to ~12.22 ms (50/dense) on the builder environment; graph p95 ranged from ~3.74 to ~14.40 ms. See `eval/results/phase8-benchmark-20261024T110135.355459Z.json`.
**Same-seed full-scale regression:** 200 entities, 2,000 episodes/seed, seeds 0–4, `k=8`, hash embedder, shared threshold 0.25. The five seed runs were executed separately and merged by the existing aggregator into `eval/results/phase8-synthetic-200x2000-5seeds-20261024T110557.327133Z.json`; configuration is unchanged from Phase 7. Graph overall accuracy 100%, stale-error 0%, abstention correctness 100%, p50 64.76 ms and p95 74.67 ms in the builder environment. Entity-centric and temporal graph accuracy are 100%; multi-hop is 100%. D-024 summary intentionally remains `graph not shown to help in this smoke test` because stale accuracy is tied at 100%, so the strict pre-declared condition that graph improve on both `multi_hop` and `stale` is not met. No generator or threshold tuning was done.
**Agent check:** offline graph and flat agent demos ran against the ingested sample database and wrote JSONL retrieval/answer logs. These runs validate data flow and instrumentation only; no live LLM request was made. Optional OpenAI integration is present but awaits user-provided local SDK/model credentials. Sample raw-content logs must be treated as local diagnostic artifacts, not production-safe telemetry.
**Tests in reconstructed builder snapshot:** full suite `80 passed, 1 skipped`; focused Phase 8/retrieval/evaluation tests `28 passed`; compileall and sample ingestion/doctor/agent commands passed. The skip requires the MCP SDK. This workspace derives from an older snapshot with the Phase 7 patch; user’s actual Windows v0.5.1 checkout still needs the full Phase 8 suite and both smoke clients rerun. The latest user-confirmed Windows Phase 7 baseline was 110 passed, MCP 12/12 and REST 11/11.
**Open:** Run the Phase 8 patch on Windows and rerun the matrix/full scale there; connect the optional real model using an approved synthetic dataset and inspect the resulting JSONL before calling Phase 8 complete. Synthetic scores remain subject to D-007.

## DBG-010 — Phase 7 retrieval diagnostic and baseline comparison — 2026-10-23
**Task:** Diagnose multi-hop accuracy 0%, poor abstention on unknown numeric service IDs, and high graph latency without generator/threshold tuning.
**Evidence before changes:** Phase 6 result `eval/results/20261023T155826.716282Z.json` had graph multi-hop accuracy 0%, unanswerable abstention correctness 0%, graph overall p50 about 781 ms and p95 about 1,354 ms in the builder snapshot. The user’s Windows run had graph p50 1,370 ms and p95 2,302 ms. A cProfile run on a 200-entity / 2,000-episode seeded store reported about 0.96 seconds for one representative directed graph query, 789 `sqlite3.Connection.execute` calls and 214 `independent_corroborations` calls; corroboration calls accounted for about 0.72 seconds cumulatively.
**Root causes:** Multi-hop wording did not specify exact path distance and the evaluation invoked default one-hop graph traversal for two-hop cases. Directed expansion could seed from an unrelated highly-ranked neighbouring service and the global top-hit pool could reintroduce unrelated candidates. Unknown identifiers such as `svc-012` or `svc-200` shared high-overlap words with existing facts, making ordinary fuzzy ranking unsuitable for identity checks. Graph candidate scoring repeated independent-corroboration SQL per row. Also, the graph expansion SQL limited rows before filtering ineligible/superseded relation support, allowing historical rows to crowd out the current target row.
**Changed:** Phase 7 adds explicit query-distance wording, graph depth=2 only for the multi-hop evaluation family, exact-entity anchoring and directed supported-relation traversal, a catalogue-backed unknown numeric-ID guard and a missing-filter abstention path, eligible-support filtering before fan-out limits, and batched corroboration lookup with semantic equivalence tests. The evaluation generator’s fact histories, relation chains, seeds, sizes and threshold are unchanged; D-024’s verdict rule is unchanged.
**After results:** 5 seeds, 200 entities, 2,000 episodes/seed, `k=8`, hash embedder; graph multi-hop 100% (95% CI 100–100%), all three modes correctly abstained on generated unknown service IDs, and graph unanswerable abstention correctness rose to 100%. Overall graph accuracy 94.2% (95% CI 91.39–96.8%), stale error 0%, abstention correctness 99.17% (95% CI 97.5–100%), p50 94.43 ms (95% CI 90.97–97.44), p95 124.88 ms (95% CI 112.18–137.67), mean graph expansion 7.075 nodes. See `PHASE7_REPORT.md` and `eval/results/20261023T184404.879694Z.json`.
**Validation in available builder snapshot:** full suite 72 passed, 1 skipped; compileall passed; the skip is the MCP stdio integration test because the MCP SDK is unavailable in this environment. The available builder code is derived from an older Phase 5 snapshot plus the Phase 6 overlay, not the complete Windows v0.5.1 checkout, so these figures are provisional until the patch is applied and the same full suite and evaluation are rerun on Windows. The user’s baseline run before Phase 7 recorded 104 passed and the REST smoke client 11/11 after its cleanup fix.
**Important:** User’s Windows graph performance targets (p50 improvement >=50% from 1,370 ms and p95 <1,000 ms) appear met numerically in the builder measurements but are **not yet confirmed on the same Windows environment**. D-021 through D-024 remain unchanged; D-007 synthetic benchmark caveat remains active.

---


## DBG-009 — Phase 6 synthetic evaluation v2 — 2026-10-23
**Task:** Replace the four-scenario smoke test as the main evaluation with a seeded multi-family comparison of `flat`, `flat_filter`, and `graph`, keeping `eval/stale_facts.py` and its test intact.
**Changed:** Added `eval/synthetic_v2.py`, `tests/test_eval_v2.py`, timestamped `eval/results/20261023T155826.716282Z.json`, Phase 6 README instructions, D-024, this report, and Phase 6-aware selective packaging. The generator covers `single_fact`, `stale`, `entity_centric`, `multi_hop`, `temporal`, and `unanswerable`; it records store and evaluation abstention separately and uses a fixed-seed 1,000-resample bootstrap CI.
**Tested in available builder snapshot:** `PYTHONPATH=src python -m pytest -q tests/test_eval_v2.py` — `5 passed in 6.20s`; `PYTHONPATH=src python -m pytest -q tests/test_eval.py tests/test_eval_v2.py` — `6 passed in 9.76s`; full snapshot suite — `66 passed, 1 skipped in 10.93s`; `PYTHONPATH=src python -m compileall -q src tests eval` — exit 0. The skipped test is `tests/test_mcp_stdio.py`, because the `mcp` dependency was not available in the builder runtime.
**Default evaluation:** `PYTHONPATH=src python eval/synthetic_v2.py --entities 200 --episodes 2000 --seeds 5 --k 8 --embedder hash --results-dir eval/results` completed with exit code 0 and saved the 300,469-byte JSON artifact above. Overall accuracy@k: flat 67.6%, flat_filter 80.0%, graph 74.0%; stale-error 0.0% for all; graph mean expanded count 18.85. Family verdicts: `single_fact` NOT SHOWN; `stale` NOT SHOWN; `entity_centric` FLAT BETTER; `multi_hop` NOT SHOWN; `temporal` FLAT BETTER; `unanswerable` NOT SHOWN. Exact metrics and confidence intervals are in `PHASE6_REPORT.md` and the JSON. The rule summary is `graph not shown to help in this smoke test`.
**Found/fixed:** The first report implementation could label graph-versus-flat `PROMISING` on a family where graph lost to `flat_filter`. Updated the label logic so `PROMISING` is shown only when the family meets the pre-declared BOTH-baselines rule. Added `test_graph_is_not_labelled_promising_if_flat_filter_wins`; D-024 and generator settings were not changed after observing results.
**Not run / blockers:** Both `python -m pip install -e ".[dev]"` and the no-build-isolation retry could not complete because DNS/network access was unavailable for setuptools/MCP packages. The smoke-client scripts are absent from the Phase 5 snapshot in this builder filesystem, so those commands returned `No such file or directory`; v0.5.1 smoke clients must be rerun in the owner's current checkout. `--embedder st` was not run because the optional package/model was unavailable.
**Scope preserved:** `D-021`, `D-022`, and `D-023` were not edited. The Windows `rest_smoke_client.py` temp-directory cleanup PermissionError shown in the owner's supplied baseline output remains out of this Phase 6 evaluation-only scope. Full regression verification must run on the actual v0.5.1 checkout; the builder workspace is an older Phase 5 package snapshot.


## DBG-007 — Phase 5 Windows verification and demo label cleanup — 2026-10-23
**Task:** Record the user's final Phase 5 Windows run and remove the stale Phase 3 label from the demo.
**Tested by user:** `python -m pip install -e ".[dev]"` succeeded; `python -m pytest -q` reported `61 passed` in 20.24s with one Starlette/httpx deprecation warning; `python eval/stale_facts.py` reported 100% accuracy for both modes, 0% stale error, 0% flat abstention, 25% graph abstention and 3 expanded items; demo handoff readback passed; lifecycle dry run reported zero candidates and no mutation; rebuild of separate empty `demo.db` returned zero nodes; `python scripts/pack.py` created both Phase 5 archives.
**Found:** The demo wrote and displayed `Phase 3` even though the current package is Phase 5.
**Fixed:** Demo now writes `Phase 5`; `tests/test_cli.py` asserts the correct phase label, that the stale label is absent, and that handoff readback succeeds. `scripts/pack.py` includes the new regression test.
**Caveat:** The synthetic evaluation remains a smoke test only, not evidence for or against H1–H7 (D-007). The final label patch needs its own test and package run.

## DBG-006 — Phase 5 evaluation and shadow lifecycle — 2026-10-23
**Task:** Add a reproducible synthetic flat-versus-graph evaluation, lazy decay scoring, a read-only lifecycle dry run, and handoff/readback coverage in the CLI demo.
**Tested:** `PYTHONPATH=src python -m pytest -q` — 60 passed, 1 skipped in 2.10s. The skip is `tests/test_mcp_stdio.py` because the official MCP SDK was unavailable in this builder runtime. `PYTHONPATH=src python eval/stale_facts.py --k 5` ran successfully and reported flat/graph accuracy 100%, stale-fact error 0%, flat abstention 0%, graph abstention 25%, and 3 graph-expanded candidate items. `PYTHONPATH=src python -m agm demo` completed write → correction → retrieve → delete → handoff → readback; the readback passed. `PYTHONPATH=src python -m agm lifecycle --db /tmp/agm-empty-phase5b.db --dry-run` exited 0 and made no view changes. `PYTHONPATH=src python -m compileall -q src tests eval` passed.
**Found:** The graph rank used persisted `decay_weight=1.0`, so recency/use had no effect; the CLI demo stopped before exercising handoff.
**Fixed:** Decay is computed lazily from idle time, usage, `derived_from` citations, corroboration, and pin state; lifecycle only reports candidates below the default 0.30 threshold; demo now saves/resumes a handoff and validates readback. D-019 and D-020 record the provisional formula and evaluation definition.
**Caveat:** The synthetic metrics are not evidence for or against H1–H7 (D-007). Windows Phase 5 verification is pending.

---


> Append-only. Every completed coding task gets an entry here, even "no issues found." Newest entries at top.

## DBG-005 — Phase 4 probation, revocation, handoff and readback — 2026-10-23
**Task:** Implement the high-stakes corroboration gate, replayable writer revocation/rollback, and cross-model handoff save/resume/readback.
**Tested:** `PYTHONPATH=src python -m pytest -q` — 55 passed, 1 skipped in 1.19s. Phase 4 tests assert low-trust facts and episodes are excluded from high-stakes expanded and flat retrieval until independently corroborated; revoking corroboration withdraws that evidence; revocation removes writer-authored items plus recursive `derived_from` descendants and remains stable after rebuild; `since` filters writes; handoff context fits its token budget; readback reports missing decisions/open items and wrong goals; packets are tenant-scoped and reconstructed by replay; REST handoff and admin-revoke routes work.
**Found:** The graph sufficiency gate can abstain on a long task summary with the default hash embedder, even where exact keywords are present; a loose readback overlap could confuse staging with production; the frozen `ResumeResult` could not return actual context.
**Fixed:** Handoff assembly falls back to the flat baseline when graph retrieval abstains; readback matching requires exact normalized containment or at least 0.60 token-set Jaccard similarity; D-016 logs the additive high-stakes parameter and handoff response fields. D-017 records replayable event semantics. `source_span` now creates a `derived_from` edge when its episode node exists.
**Open:** One MCP stdio test is skipped in this builder runtime because its official SDK is not installed, while the user previously ran the Phase 3 MCP test on Windows. Apply the overlay and rerun the full Phase 4 suite on Windows; inspect the package and review revocation's event-log retention behavior.

## DBG-004 — Phase 3 REST/MCP interfaces and guardrails — 2026-10-23
**Task:** Add scoped API-key authentication, REST routes, nine MCP tool names, secret redaction, instruction-like quarantine, examples, and package overlays.
**Tested:** `PYTHONPATH=src python -m pytest -q` — 42 passed, 1 skipped in 0.87s; `PYTHONPATH=src python -m compileall -q src tests` — exit code 0. The skipped test is the official MCP stdio client round-trip because the `mcp` package was not preinstalled.
**Found:** Initial REST tests injected a SQLite connection created in the main thread into TestClient's worker thread, triggering SQLite's thread guard. Attempting `pip install 'mcp>=2,<3'` failed because DNS/network access was unavailable in the builder environment.
**Fixed:** API tests now construct the store inside the FastAPI lifespan on the request thread. The package pins the FastMCP-compatible official `mcp>=1.26,<2` API and includes a conditional stdio integration test to run after installation. Quarantined nodes are filtered from both default retrieve and history surfaces. The packer creates both a workspace ZIP and a root-relative overlay, excludes `.git`, databases, caches, and local key files.
**Open:** Owner must install the Phase 3 dependencies on Windows, run all tests including the MCP stdio test, inspect the overlay archive, and obtain review before considering remote exposure.

## DBG-003 — Phase 2 package and final smoke checks — 2026-10-23
**Task:** Make the packer phase-aware, exclude `.git`, and assemble a local-overlay archive for applying Phase 2 to the complete Windows checkout.
**Tested:** `PYTHONPATH=src python -m pytest -q` — 31 passed in 0.55s; `PYTHONPATH=src python -m compileall -q src tests` — exit code 0; `PYTHONPATH=src python -m agm demo` — exit code 0; `PYTHONPATH=src python -m agm rebuild --db ./demo.db` — exit code 0 and 0 nodes in the separate empty database.
**Found:** The runtime export available to the builder does not contain every existing design document from the owner's repository, so a full-repository snapshot would not be safe as the only handoff artifact.
**Fixed:** `scripts/pack.py` now excludes `.git` and generated files and selects the Phase 2 archive when `PHASE2_REPORT.md` exists. A separate overlay archive includes implementation files and tests without replacing unrelated design files.
**Open:** Owner must run the tests on Windows and have the Phase 2 changes reviewed before `docs/phases.md` is marked complete.

## DBG-002 — Phase 2 graph retrieval and conflict handling — 2026-10-23
**Task:** Implement Phase 2 graph expansion, alias-aware entity identity, provisional trust/ranking, sufficiency and abstention, plus compare-and-swap contested writes.
**Tested:** `PYTHONPATH=src python -m pytest -q` — 31 passed in 0.48s on Python 3.13.5. Regression tests cover flat-baseline parity, one-hop/two-hop bounds, related entity expansion, alias-based writes, ambiguous aliases, stale base versions, trust-gap conflicts, D-008 weights, and deterministic replay of edges, aliases, FTS rows and embeddings after hard deletion.
**Found:** A replay test initially found that entity `created_event` and supersedes edges could differ after the original fact was scrubbed. Further tests found that writes and relation edges through an alias could lose their canonical identity during replay if the alias declaration was deleted.
**Fixed:** Skip edges to absent nodes; recompute alias mappings and FTS entity terms after hard delete; persist resolved canonical identity and relation target IDs in write-event payloads; calculate accepted version chains from active/superseded facts rather than letting contested candidates advance the accepted version.
**Open concerns:** The frozen `RetrieveResult` has no general warnings field, so retrieved conflicts are flagged through `Node.contested_with`; the originating contested `WriteResult` carries the explicit warning. D-008 scoring weights and the 10-year age factor are placeholders and need evaluation/calibration.

## DBG-001 — Docs scaffold consistency check — 2026-10-22
**Task:** Generate context.md and docs/ from Draft v5 (no code written yet).
**Tested:** Script checked that every docs/ file ends with the Next line, no TBD or template placeholders remain, the REST/MCP parity table lists 9 tools matching the Phase 3 brief, and all open items are marked "(open — confirm with user)".
**Found:** Nothing failing. Three open items remain by design: root folder path (context.md, workflow.md) and which hosted clients support custom connectors (trd.md). Contracts themselves are unreviewed by running code, so they may need adjustment once Phase 1 is built.
**Fixed:** None needed.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task — it routes you to the right file for what you are about to do.


## DBG-016 — Revoked node reappears after replay — 2026-10-25

**Symptom:** `revoke_writer(..., since=cutoff)` removes the selected post-cutoff node from the live materialized view, but the node returns after closing/reopening and rebuilding views.

**Evidence:** CI run 40188540997 failed this regression on Python 3.11, 3.12 and 3.13. The first attempted fix replayed revocation events a second time, but the same acceptance test still failed. Do not treat that approach as a fix.

**Candidate correction:** Branch `fix/revocation-replay-corrective`, latest candidate commit `4001f746d62d70a0062f8a5ac9992d4003e47c00`, collects stored tombstone IDs and re-derives nodes matching each revocation's tenant, writer and `since` cutoff, then enforces their removal as the final replay step. This deliberately treats revocation as a final-state constraint on materialized views.

**Validation:** NOT RUN for the candidate correction. Run `python -m pytest -q tests/test_privacy_edge_acceptance.py`, then `python -m pytest -q`, `git diff --check`, and exact-head CI. If the cutoff test still fails, inspect the persisted revoke payload and post-replay node/event IDs before attempting another code change.

**Process note:** PR #7 was merged despite failing CI, contrary to the project's no-merge-before-acceptance rule. Do not merge the corrective PR until validation passes.

## DBG-033 — Retention orphan-scrub scope regression

**Task:** Add a regression for the privacy boundary of `MemoryStore.expire_before` when source payloads belong to revoked writers and no longer have materialized nodes.

**Change:** Added a test with aged revoked source events in the current tenant/project, another project in the same tenant, and another tenant. The test requires expiry to scrub only the current tenant/project's orphan payloads and verifies that replay does not restore scrubbed content.

**Validation:** Test and full suite NOT RUN locally in this environment. Commit `ee81976c701e90c633b577a09aa7f6a26d762e14` has no visible CI status yet. The test must pass on exact-head CI before this acceptance check is considered verified.

**Related evidence:** User-reported Windows run: 213 passed, one Starlette/httpx deprecation warning; peak RSS 60,682,240 bytes; five concurrent repetitions with zero errors. These are user-supplied results, not independently rerun here.

## DBG-034 — Local-hub timeline and export acceptance coverage

**Task:** Strengthen M1 tests around deterministic metadata ordering and export serialization safety.

**Change:** Added tests that assert timeline entries are newest-first and invalid limits fail closed; repeated Obsidian exports are byte-for-byte stable; project frontmatter containing quotes/newlines is serialized as a scalar rather than injecting YAML keys; and secret-like text is redacted in exported content.

**Validation:** NOT RUN locally. Latest test commit is `881512bc1da1a0d67874d3ed5427b3beff0f0fe9`; no exact-head CI run was visible when recorded. Run `python -m pytest -q tests/test_local_hub.py`, then the full suite and package/hygiene checks on the exact candidate.


## DBG-035 — Local-hub acceptance CI failures corrected

**Evidence:** Exact-head GitHub Actions run [40213071743](https://github.com/yash936936/AGM/actions/runs/40213071743) exposed two failures in `tests/test_local_hub.py` across Ubuntu Python 3.11, 3.12 and 3.13: the timeline test incorrectly assumed `WriteResult.event_id` exists, and the export test hard-coded a JSON-escaping representation that did not match the actual project string/serializer output. The other 214 tests passed in the Ubuntu Python 3.11 job.

**Fix:** Removed the invalid `WriteResult.event_id` assumption; the test now checks the two timeline rows and their descending event IDs. The export test now derives the expected frontmatter scalar with `json.dumps` and checks that an injected newline key is not present in frontmatter.

**Validation:** Fix committed as `d8e8c7acff925d70d3167bb40f40b548bc3288e9`. Focused and full tests have not been run locally; exact-head CI must confirm the fix before this acceptance coverage is considered passing.

## DBG-036 — Export test used escaped newline characters instead of line breaks

**Evidence:** Exact-head run [40213224547](https://github.com/yash936936/AGM/actions/runs/40213224547) showed the timeline assertion was fixed, but the export test still failed because its fixture encoded literal backslash+n characters before `password=`. The redaction rule correctly expects a token boundary before the label, so that malformed fixture bypassed the intended boundary and did not represent a password on a new line.

**Fix:** Updated the note fixture to contain actual newline characters and the adversarial project label to contain an actual newline. This now tests the intended serialization-injection and secret-redaction behavior through the normal write path rather than a literal escape sequence.

**Validation:** Candidate test update `40ff30a5966b6e5539663ce9e25bd4c35f125765`. No local run; exact-head CI still required. Do not mark M1 acceptance passing until all matrix jobs complete successfully.

## DBG-037 — M1 session and connection scope validation

**Task:** Extend the local-hub acceptance audit after the export fixture passed CI.

**Changes:** Tightened `list_sessions` so limits must be actual integers (booleans, floats and strings are rejected with `ValueError`). Added acceptance coverage for session/connection isolation across both project and writer boundaries, and for invalid connection-scope input types.

**Validation:** Source commit `8eeca08ca33499217f6e1a3c582051576a6bd4e7`; test commit `42e3e638d8f051893c5a70ae26daba833be2f8c0`. Tests have not been run locally. Exact-head CI is required. Existing CI run [40213472988](https://github.com/yash936936/AGM/actions/runs/40213472988) passed all six matrix jobs for the prior candidate; it does not validate these new changes.

## DBG-038 — REST authorization coverage for M1 hub endpoints

**Evidence:** CI run [40214097156](https://github.com/yash936936/AGM/actions/runs/40214097156) passed all six Linux/Windows Python 3.11–3.13 jobs for the session/connection scope candidate. PR #18 was merged at `927553613e16413b367d91556252a75ede80adaa`.

**Change:** Added REST-level authorization tests for read-only session access (list allowed; create/close forbidden), connection endpoints requiring `admin`, and an admin-authorized connection create/list round trip that checks metadata-only output. Test commit `2085ba3b76652636152b3f4dccb627a426e7b123`.

**Validation:** NOT RUN locally; this new REST authorization coverage has no exact-head CI result yet. Do not treat it as passing until all six matrix jobs and package/hygiene checks complete on the exact candidate.

## DBG-039 — REST identity-boundary acceptance

**Evidence:** PR #19's exact-head run [40214468957](https://github.com/yash936936/AGM/actions/runs/40214468957) passed all six Linux/Windows Python 3.11–3.13 jobs, including tests, repository hygiene, whitespace and wheel inspection; PR #19 merged at `24072c84beb395fcf07af54c8628fd93d96b90c8`.

**Change:** Added end-to-end REST coverage proving sessions and connections are isolated across project, writer and tenant identities, and that session-list query limits outside the allowed integer range return 422. Test commit `613d96fcc453f6979eec16c9a68beb5e7d3c0f77`.

**Validation:** NOT RUN locally and no exact-head CI result yet. This is a new regression candidate; do not accept it until the full Linux/Windows Python 3.11–3.13 matrix passes.

## DBG-040 — REST identity-isolation candidate passed CI

**Evidence:** Exact-head workflow [40214773052](https://github.com/yash936936/AGM/actions/runs/40214773052) passed all six Ubuntu/Windows Python 3.11–3.13 jobs, including test suite, repository hygiene, whitespace and wheel/package inspection. PR #20 merged as `d4eff63b74c0ed37cdf52c1b71c7b951a26d4547`.

**Accepted for this commit:** REST session/connection isolation across tenant, project and writer identities, plus invalid session-list limit query handling. This is code-level acceptance evidence only; it does not close the broader M1 lifecycle audit, M0 release audit, held-out real-history evaluation, or independent security/privacy review.
## DBG-041 — Timeline project filter must precede limit

**Task:** Continue the consolidated M0/M1 audit after the REST identity-boundary tests merged.

**Finding:** `src/agm/local_hub.py::timeline` queried the newest `limit` events for a tenant and then filtered them by project in Python. Newer events in a sibling project could consume the entire page, causing the requested project's timeline to appear empty or incomplete. This violated expected project-scoped pagination.

**Fix candidate:** Branch `fix/m1-timeline-project-limit`, commits `d9b034804ca4065af8bc5b028f609790e6e75f3c` (SQL scoping fix) and `9992182f1551f64c67c1f1fcec2e95d0899695ec` (regression test). Project filtering now occurs in SQL before LIMIT; events without `ctx.project` retain the existing default-project/originating-writer compatibility behavior. The regression writes one local event followed by eight newer events in another project and checks that `timeline(..., limit=1)` still returns the local event.

**Validation:** NOT RUN locally. Exact-head CI, focused `tests/test_local_hub.py`, full pytest suite, wheel/package inspection, repository hygiene and `git diff --check` remain required. Do not merge until exact-head CI passes.

**Release status:** M0 remains IN PROGRESS, M1 remains PARTIAL / VERIFY. Real-history evaluation is NOT RUN and independent security/privacy review is NOT ESTABLISHED.
## DBG-042 — Default retention must preserve revoked pinned source payloads

**Finding:** `expire_before()` used materialized pinned node IDs to protect pinned content during orphan-event scrubbing. Revocation removes those nodes, so an aged pinned source event could be scrubbed by a default sweep despite the documented retain-pinned-by-default policy.

**Candidate fix:** Branch `fix/retention-preserve-revoked-pins-v2`, source commit `692e5d9c95290050d548d2ffd7550cef57693a52`, regression commit `0acae570159906e2715aaab8053f972f05976d37`. The orphan-event path now checks the stored source item's `pin` flag and skips pinned payloads unless `include_pinned=True`. The regression revokes a pinned writer, runs default expiry and replay, then verifies explicit opt-in can scrub the payload.

**Validation:** NOT RUN locally. Exact-head CI and packaging/hygiene checks required before merge. M0 remains IN PROGRESS; do not treat this fix as accepted until evidence passes.


## DBG-043 — Validate connection scopes and diagnostic timeouts — 2026-10-25

**Finding:** create_connection() used a truthiness fallback for scopes, so an explicitly empty scope list silently became memory:read instead of failing closed. Non-list/unhashable scope values could leak TypeError. test_connection() accepted invalid timeout values; zero, negative, non-finite, boolean, or string timeouts could raise inconsistent errors outside the diagnostic result contract.

**Change:** Apply the least-privilege default only when scopes are omitted (None); require explicit scopes to be a non-empty list of strings in the allowlist. Require diagnostic timeout to be a finite positive number and reject booleans.

**Tests:** Added malformed/empty scope cases and timeout boundary/type cases. Exact-head CI is required; local tests were not run in this remote editing environment.
