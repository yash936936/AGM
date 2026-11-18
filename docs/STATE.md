# State — AGM prototype

Rewritten in place; the dated history is in `status.md`. Last updated 2026-11-19.

## Where we are
Version 0.7.0, local-only prototype. PR #62 merged as `6d6732b` (D-050 documentation convention update). Main CI run #667 passed all six Ubuntu/Windows Python 3.11–3.13 jobs on that exact head. The separate `chore/repo-tidy` branch is two commits ahead of its merge base and twelve commits behind current main; its D-049/build-plan/prompt work is already represented on main through PR #62. The remaining tidy changes are being ported onto `chore/phase0-reconciled` to avoid merging a stale divergent branch. PR #61 is unrelated (`cleanup/lean-v0.6`).

## Tests
Local report dated 2026-11-17: 308 passed, 2 xfailed on Windows, Python 3.14; hygiene scan PASS (126 tracked paths). The two xfails are the two `hint` parameter variants of one strict xfail in `tests/test_relation_wording.py::test_two_hop_reaches_the_second_dependency_owner`; both are marked for R2.6c because low lexical similarity causes abstention before expansion. This is now identified, not fixed. Main CI run #667 passed six jobs on Python 3.11–3.13. Python 3.14 is being added to the matrix; its CI result is pending.

## Blockers
- R0.5: the two formerly uncommitted test files are present in `main` and run in CI, but the old local working-folder copy cannot be retired or verified from GitHub.
- Remote use needs an independent reviewer (R3.5) and a deploy account (R3.6).
- The 2 xfails and the unread CI #641 failure (DBG-002) need an owner.

## Next work
1. Complete review and merge PR #62 after its final-head CI passes. Separately raise/review the `chore/repo-tidy` branch; do not assume PR #61 covered it. Retire the old working folder only after R0.5 is verified.
2. Batch 1 (retrieval correctness): R2.6f, R2.6c, R2.6d, R2.1, R2.3, R0.3, R0.4, X1. Batch plan and status: `BUILD-PLAN.md`; prompts: `PROMPTS.md`.
3. In parallel, write the real cases for batch 2.

## Evidence so far (synthetic only)
Graph retrieval is NOT JUSTIFIED under the pre-registered v3 rule (hash and spaCy embedders). It wins only multi-hop, and a post-hoc iterative flat baseline erases even that. See `benchmarks/r2_labelled_v3.md` and `benchmarks/r2_post_hoc_iterative_baseline.md`. Unproven until real data (G1).

## Open defects
DBG-002 (unread CI #641 failure), DBG-007 (answer-slot wording, abstention, sibling-entity leaks), DBG-008 (2 xfails).

## Open external gates
Held-out real-history evaluation NOT RUN. Independent security and privacy review NOT PERFORMED. Real third-party host integration NOT VERIFIED. Independent acceptance sign-off OPEN. Not production-ready; loopback only.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
