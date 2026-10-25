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
