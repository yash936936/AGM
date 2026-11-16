# State — AGM prototype

Rewritten in place; the dated history is in `status.md`. Last updated 2026-11-17.

## Where we are
Version 0.7.0, local-only prototype. At the time this PR was opened, `main` was at `51cf26a` (D-048, R2.6e, Apache-2.0). The separate `chore/repo-tidy` branch exists at `89c2f45` and contains the benchmark-folder tidy, build plan, prompts and D-049; it has not been merged and no PR for that branch was found during this review. PR #62 (`docs/convention-update`) contains the D-050 documentation convention update and is based on that `main` commit. Do not treat PR #61 as the merge for `chore/repo-tidy`: PR #61 merged the distinct `cleanup/lean-v0.6` branch.

## Tests
Local report dated 2026-11-17: 308 passed, 2 xfailed on Windows, Python 3.14; hygiene scan PASS (126 tracked paths). The two xfails remain unexplained (DBG-008). CI run #642 is historical evidence on an earlier commit, not validation of this documentation branch. PR #62's own CI matrix must be checked on its final head before merge.

## Blockers
- Phase 2 needs your 20–40 real cases written and frozen (R2.2). Nothing in this repo can replace them.
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
