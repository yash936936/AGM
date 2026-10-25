## 2026-10-25 — Benchmark acceptance suite and keyword baseline in review

**Current branch:** `work/benchmark-acceptance-baselines`, based on PR #15's peak-RSS/concurrency candidate.

**Implemented in this increment:** strengthened Windows peak-working-set API signatures; added opt-in `--repetitions` with per-run concurrent p50/p95/p99, throughput and error summaries; added `examples/benchmark_acceptance.synthetic.jsonl` with 10 labelled cases covering cross-session recall, relevance, abstention, temporal correction, deletion, revocation, expiry and tenant isolation; added a token-overlap lexical baseline to paired reports and standalone `python -m eval.keyword_baseline`.

**Validation:** PR #15 exact-head CI passed all six Linux/Windows Python 3.11–3.13 jobs in [run 40210586141](https://github.com/yash936936/AGM/actions/runs/40210586141). Initial run [40211567298](https://github.com/yash936936/AGM/actions/runs/40211567298) caught a lexical tokenization-regex bug, now corrected on the latest head. Follow-up exact-head CI [40211660005](https://github.com/yash936936/AGM/actions/runs/40211660005) is pending, including the Windows RSS assertion. User-run PR #15 smoke output used one synthetic case, had zero concurrent errors, and reported peak RSS as null; it is not a quality or capacity claim.

**Still blocked:** the 10-case suite is synthetic; no consented, de-identified held-out dataset was supplied, so real-history results remain NOT RUN. Independent security/privacy review remains NOT ESTABLISHED. Do not claim production readiness.

## 2026-10-25 — Benchmark runner merged; operation and load metrics extended

**Merged:** [PR #13](https://github.com/yash936936/AGM/pull/13) added paired flat-vs-graph evaluation. [PR #14](https://github.com/yash936936/AGM/pull/14) added operation-level timings and removed the input dataset filename from aggregate output.

**Current increment:** `work/benchmark-rss-concurrency` adds a best-effort cross-platform process peak RSS metric and opt-in concurrent retrieval load measurements (p50/p95/p99, throughput, errors, elapsed time). The report protocol advances to `paired_flat_vs_graph_v3`.

**Verification:** PR #14 exact-head GitHub Actions passed all six Linux/Windows Python 3.11–3.13 jobs in [run 40210191011](https://github.com/yash936936/AGM/actions/runs/40210191011). The current increment still requires its own exact-head CI.

**Still blocked:** No consented, de-identified held-out dataset was supplied, so real-history results remain NOT RUN. Independent security/privacy review remains NOT ESTABLISHED. A standalone keyword baseline remains NOT RUN. Do not claim production readiness.

## 2026-10-25 — Paired retrieval benchmark runner merged; operation metrics follow-up in progress

**PR:** [#13](https://github.com/yash936936/AGM/pull/13), merged. Follow-up branch: `work/benchmark-operation-metrics`.

**Change:** Added `eval/benchmark_runner.py` to compare flat and graph retrieval on the same labelled JSONL cases, reporting retrieval/end-to-end latency percentiles, recall/pass rates, abstention accuracy, forbidden-value leakage, cases/second and SQLite file size. Default output omits case IDs and raw memory content. The existing evaluator now captures retrieval-call latency and database file size.

**Verification:** User-reported local checks on the merged candidate: wheel build succeeded; package inspection passed (28 entries, 23 Python modules); full suite `208 passed, 1 warning`; repository hygiene passed (155 tracked paths); `git diff --check` passed; working tree clean. Follow-up changes on this branch still require exact-head CI.

**Still blocked:** No consented, de-identified held-out dataset was supplied, so real-history results remain NOT RUN. Independent security/privacy review remains NOT ESTABLISHED. Peak process RSS, concurrent-load throughput and a standalone keyword baseline are not yet measured. Do not claim production readiness.

## 2026-10-25 — M1 owner/session/connection increment in review

**PR:** [#11](https://github.com/yash936936/AGM/pull/11), branch `feat/m1-owner-sessions-connections`, draft; exact-head CI pending.

**Implemented in candidate:** one-time local owner-key bootstrap command; persistent tenant/project/writer-scoped session create/list/close endpoints; scoped REST connection registry; least-privilege memory scopes; loopback-only health diagnostics; Linux/Windows CI matrix for Python 3.11–3.13; built-wheel hygiene inspection; focused tests for bootstrap, sessions, registry scoping, endpoint validation and failed diagnostics.

**Revocation update:** Current main commit `bffa7ff652df55308004a867ab2a6dec9f1c24cb` passed run [40193212194](https://github.com/yash936936/AGM/actions/runs/40193212194): 193 passed on Python 3.11, 3.12 and 3.13. This resolves the previously recorded cutoff-revocation regression for that tested commit; retain the regression test as a release gate.

**Still blocked:** held-out real-history evaluation requires a consented, de-identified dataset and frozen protocol; independent security/privacy review requires an actual reviewer and signed findings. Do not claim production readiness. Windows and package checks are newly added to CI and remain pending until PR #11 jobs finish. Local tests were not run because this environment cannot resolve GitHub for cloning.

## 2026-10-25 — M1 local hub implementation increment

**Branch/PR:** `feat/m0-m1-completion`, [PR #10](https://github.com/yash936936/AGM/pull/10), draft.
**Implemented in this increment:** `src/agm/local_hub.py` supplies a project-scoped metadata timeline, deterministic read-only graph snapshot, and guarded Obsidian export. Focused tests are in `tests/test_local_hub.py`. D-030 records the design and its boundaries.
**Verification:** Local tests NOT RUN because GitHub DNS/network was unavailable to the execution environment. Actions run 40192632664 was triggered; check its final conclusion before considering the branch verified.
**Still open:** M1 owner authentication/bootstrap, session lifecycle, connection registry and real connection diagnostics. M0 full exact-head acceptance, cutoff-revocation regression verification, local Windows smoke/packaging checks, held-out real-history evaluation and independent security/privacy review. M0/M1 are not complete or production accepted.

## 2026-10-25 — fast-track audit and exact-head CI blocker

**Review branch:** `debug/revocation-replay-fasttrack-review`; public `main` was not changed by this review. Baseline main head: `fb732d2e49bc99205cd14964a9d0ba01163bfbb0`.

**ZIP disposition:** The ZIP is a partial plan/test overlay whose assumptions conflict with the current roadmap and decision log. It was not applied wholesale. The repo-aligned plan is `prompts/fasttrack_debug_plan_revised.md` on the review branch.

**Highest-priority issue:** Main's latest Actions run [40189884890](https://github.com/yash936936/AGM/actions/runs/40189884890) fails on Python 3.11, 3.12 and 3.13. The failing cutoff-revocation test shows an item reappearing after database reopen and `rebuild_views()`. All three jobs reported `1 failed, 189 passed, 1 warning`; hygiene and whitespace checks passed. This is still unresolved and is the first coding gate.

**Verification actually performed:** Reviewed current repository entry point, agent rules, roadmap, status, decisions, debug log, store implementation, acceptance test, and CI job output remotely. Created review branch and committed the revised plan plus this audit log. No local code/test execution was available here. Local Windows tests, smoke clients, evaluation, packaging, and final archive inspection are NOT RUN.

**Next:** Fix the revocation replay regression with the smallest contract-preserving change, then validate the retention implementation against D-028/D-029 and audit actual M0 gaps. Build M1 features only after a source/test inventory and scope decision.

## 2026-10-25 — M1 end-to-end mutation benchmark cases added; release gates remain open
**Branch:** work/m0-m1-completion. Public main remains unchanged.

**CI evidence for evaluator operation tests:** Run [40124787565](https://github.com/yash936936/AGM/actions/runs/40124787565), commit 20ea048a887ad9b31a36a7615ac12f841cdfea01: Python 3.11 `171 passed, 1 warning in 9.46s`; Python 3.12 `171 passed, 1 warning in 13.68s`; Python 3.13 `171 passed, 1 warning in 15.78s`. The latest code/test tree passed all three environments. The subsequent docs-only updates require a final branch-head CI run.

**M1 changes:** The evaluator now executes correction, hard delete, and writer revocation with actual MemoryStore methods, closes/reopens after operations, rebuilds views from the event log, then queries and scores expected/forbidden values and abstention. Negative tests cover missed expected values, forbidden-value leaks, incorrect abstention, malformed schema, duplicate cases, zero-tolerance sentinel requirements, tenant isolation, and end-to-end correction/delete/revocation.

**Still open:** The evaluator threshold values are operational defaults and must be reviewed and frozen before held-out use. The existing retention/decay path is read-only dry run; an explicit expiry/retention operation and acceptance policy is not delivered. Local Windows regression and required smoke clients, simulation, package inspection, and final tree hygiene are NOT RUN here. Real consented held-out evaluation is NOT RUN. Production security/privacy review is NOT ESTABLISHED. Do not ship a ZIP until implementation and target-environment checks are complete.


## 2026-10-25 — M0–M4 roadmap documented; branch-local verification recorded

**Roadmap:** [M0–M4 roadmap](M0_M4_ROADMAP.md) now defines goals, deliverables, acceptance conditions, status vocabulary, release gates and execution order for storage correctness, local-first hub, live multi-agent memory, teams and hosted deployment.

**Branch:** `work/m0-m1-completion`; `main` remains unchanged.

**User-reported local Windows/Git Bash evidence on commit `46d954c`:**
- `python -m pytest -q`: 182 passed, 1 deprecation warning.
- MCP smoke: 12/12 passed.
- REST smoke: 11/11 passed.
- `eval/stale_facts.py`: 7 scenarios, 0 mismatches.
- compileall, repository hygiene, `git diff --check`, and package creation completed.
- Synthetic active-memory simulation completed; results are diagnostic, not production-quality evidence.
- Synthetic real-history evaluator: one cross-session recall case passed. This is not held-out real-history acceptance.

**Retention:** `MemoryStore.expire_before` and `tests/test_m1_retention.py` are present. Coverage includes cutoff validation, pinned-memory policy, tenant/project scoping, revoked-writer payload scrubbing and replay/rebuild. Remaining review must verify the full mutation contract, atomic rollback/failure injection, idempotent repeat expiry, replay safety, and the declared audit/deletion guarantees. Do not mark M0 closed from test count alone.

**M0–M4 disposition:** M0 remains in progress pending retention-contract review and exact-head CI/package inspection. M1 is partial and must be audited against the owner login, agent connection/session, timeline, graph snapshot and Obsidian export requirements. M2, M3 and M4 are not accepted until their own integration and operational acceptance gates pass. Real-history acceptance remains NOT RUN because no eligible dataset is available; independent security/privacy review remains NOT ESTABLISHED.

**Next:** implement and test remaining M0 gaps, then update the acceptance matrix with evidence tied to the resulting candidate commit. Do not merge or claim production readiness while mandatory gates are open.

## 2026-10-25 — Revocation replay cutoff regression

**Original PR:** https://github.com/yash936936/AGM/pull/7 was merged despite failing acceptance CI. This is recorded as a process error; do not infer correctness from the merge.

**Failure evidence:** GitHub Actions run 40188540997 failed on Python 3.11, 3.12 and 3.13. The cutoff test found that a post-cutoff node reappeared after reopen/rebuild. The original replay-pass change did not resolve it.

**Corrective branch:** `fix/revocation-replay-corrective`, latest candidate commit `4001f746d62d70a0062f8a5ac9992d4003e47c00`. The candidate enforces stored tombstone IDs after replay and also re-derives matching source nodes from each revocation event's tenant, writer and `since` cutoff. This is a candidate fix, not yet validated.

**Validation:** NOT RUN at this candidate head. Required next: focused edge acceptance tests, full pytest suite, `git diff --check`, and CI on the exact branch head. Do not merge this corrective branch or claim the issue fixed until all pass.

**Release status:** Revocation replay correctness remains unresolved; production readiness is not established.

## 2026-10-25 — Retention orphan-scrub scope regression added

**Branch:** `work/benchmark-acceptance-baselines`.

**Change:** Added a regression that creates aged, revoked source events in the current project, another project in the same tenant, and another tenant. It asserts that expiry scrubs only the current tenant/project's orphan payloads and that replay does not reintroduce scrubbed content. This extends the existing retention scope, idempotency and rollback coverage.

**Validation:** The focused test and full suite have NOT been run in this environment. The new commit is `ee81976c701e90c633b577a09aa7f6a26d762e14`; no CI status was visible for that commit at the time of this update. Do not treat this test as passing until exact-head CI completes.

**Benchmark evidence update:** Follow-up exact-head CI run [40211660005](https://github.com/yash936936/AGM/actions/runs/40211660005) and latest docs-head run [40211734663](https://github.com/yash936936/AGM/actions/runs/40211734663) passed all six Linux/Windows Python 3.11–3.13 jobs. User-reported Windows benchmark evidence: full suite `213 passed, 1 warning`; peak RSS `60,682,240` bytes; five repetitions, four workers, 1,000 requests per mode per repetition, zero errors; median concurrent p95 126.4 ms flat / 132.3 ms graph, throughput 89.0 / 86.4 requests/s. On the 10-case synthetic suite, flat and graph each passed 100% with 100% expected-value recall and zero forbidden-value leaks; keyword baseline passed 90% and abstention accuracy was 90%. These are synthetic/user-reported measurements, not held-out real-history or production-capacity evidence.

**Still blocked:** held-out consented real-history evaluation is NOT RUN; independent security/privacy review is NOT ESTABLISHED. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY.

