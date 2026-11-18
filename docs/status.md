# Status log — AGM prototype

## 2026-11-19 — Draft release notes and local tagging procedure
**Did:** added `CHANGELOG.md` and `docs/release-procedure.md` for the v0.7.0 local prototype. The procedure requires exact-head eight-job CI, test/hygiene/package checks, accepted retrieval benchmarks and a clean main tree before tagging. It explicitly does not authorize PyPI publication or remote deployment.
**Tests:** documentation-only changes; not run locally. The release tag is NOT created because Batch 1 is not yet accepted.
**Next:** complete PR #64's exact-head CI and benchmark evidence, then finish release checks before tagging.


## 2026-11-19 — Batch 1 validation and CI #641 diagnosis
**Did:** inspected the historical failed Windows Python 3.13 job from CI run #641. The failure was the 0.5-second duration-mode REST benchmark test recording zero successful requests; the other five matrix jobs passed and run #642 later passed. Increased that test's duration to 2.0 seconds while keeping the slow RSS-probe regression. Removed the opt-in label condition from the paired before/after retrieval benchmark so the job runs on pull requests.
**Tests:** no local test run. The 2.0-second change is pending exact-head CI. Current PR CI has not yet completed; no benchmark result is claimed.
**Next:** review all eight matrix jobs and the paired benchmark artifact, fix any regressions, then update acceptance docs and merge only after the exact head is green.



> Append-only. Newest entry at top. One entry per work session or review; current state lives in `STATE.md`, defects in `debug.md`, decisions in `decisions.md`.


## 2026-11-19 — Batch 1 retrieval implementation started
**Did:** implemented exact hyphen-aware entity scoping in flat and graph retrieval; expanded owner and on-call answer-slot phrases; added direct and relation-target answer-slot evidence checks; removed the two strict xfail parameter marks; added regression tests for five owner phrasings, sibling entities, missing attributes, and vector/whole-log baseline behavior. Added an optional `eval-sentence-transformer` extra and paired base/head benchmark workflow with BM25, vector-only and whole-log modes.
**Tests:** NOT RUN locally. CI and paired benchmark are pending on the exact Batch 1 head. No before/after result is claimed yet.
**Next:** validate syntax and all tests on Ubuntu/Windows Python 3.11–3.14; inspect benchmark artifacts and repair any regressions before merging.

## 2026-11-19 — Phase 0 reconciliation started
**Did:** confirmed PR #62 merged at `6d6732b`; main CI run #667 passed all six Ubuntu/Windows Python 3.11–3.13 jobs. Reviewed `chore/repo-tidy`: D-049, the build plan and prompts are already represented on main; ported the remaining local-artifact ignore rules and prepared benchmark-history cleanup. Added Python 3.14 to the CI matrix. Identified DBG-008's two xfails as the two hint variants of one strict R2.6c test in `tests/test_relation_wording.py`. Confirmed `test_retrieve.py` and `test_privacy_edge_acceptance.py` are tracked in main; retiring the old local working-folder copy remains an owner-side check.
**Tests:** NOT RUN locally; no repository checkout is available in this execution environment. Existing main CI #667: 6/6 pass on Python 3.11–3.13. Expanded matrix CI pending.
**Next:** complete the reconciled Phase 0 port and verify CI; then fix R2.6f/c/d and add the Batch 1 baselines and optional sentence embedder.


## 2026-11-17 — PR #62 consistency review
**Did:** reconciled the contributor reading order with `context.md` as the repository entry point; clarified that `chore/repo-tidy` is separate from merged PR #61; aligned the roadmap's current status with D-047/D-048 and the current state report; labelled CI #642 as historical evidence.
**Tests:** documentation-only edits. Code tests and hygiene scan NOT RUN in this review. PR #62 CI must pass on its final head before merge.
**Next:** finish the PR review, then handle `chore/repo-tidy` as a separate branch/PR.

## 2026-11-17 — Docs convention adopted (D-050)
**Phase:** 0 (cleanup and docs), see `BUILD-PLAN.md`.
**Did:** moved benchmark snapshots to `docs/benchmarks/history/`; added build plan, prompts, `phases.md` (now historical), `debug.md`, rewritten `appflow.md`, `STATE.md`, `components/`, `readme.md`; context rewritten to the source-of-truth form; `status.md` changed from a rewritten summary to this log.
**Tests:** 308 passed, 2 xfailed (Windows, Python 3.14). Hygiene PASS.
**Last debug:** DBG-008. **Last decision:** D-050.
**Next up:** merge, then Batch 1.

## 2026-11-05 — D-048 and Apache-2.0 (reconstructed)
**Did:** relation-following no longer depends on query wording (held-out criteria met); licence added. Full detail: `decisions.md` D-048, `debug.md` DBG-006.
**Tests:** 308 passed, 2 xfailed after the patch.

Entries before this one are in `git log` and tag `archive/pre-cleanup-main`.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
