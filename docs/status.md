# Status log — AGM prototype

## 2026-11-17 — PR #62 consistency review
**Did:** reconciled the contributor reading order with `context.md` as the repository entry point; clarified that `chore/repo-tidy` is separate from merged PR #61; aligned the roadmap's current status with D-047/D-048 and the current state report; labelled CI #642 as historical evidence.
**Tests:** documentation-only edits. Code tests and hygiene scan NOT RUN in this review. PR #62 CI must pass on its final head before merge.
**Next:** finish the PR review, then handle `chore/repo-tidy` as a separate branch/PR.


> Append-only. Newest entry at top. One entry per work session or review; current state lives in `STATE.md`, defects in `debug.md`, decisions in `decisions.md`.

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
