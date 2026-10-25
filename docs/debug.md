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

