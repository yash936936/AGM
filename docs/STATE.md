# State — AGM prototype

Rewritten in place; the dated history is in `status.md`. Last updated 2026-11-19.

## Where we are
Version 0.7.0, local-only prototype. PR #62 merged as `6d6732b` (D-050 documentation convention update). Main CI run #667 passed all six Ubuntu/Windows Python 3.11–3.13 jobs on that exact head. The separate `chore/repo-tidy` branch is two commits ahead of its merge base and twelve commits behind current main; its D-049/build-plan/prompt work is already represented on main through PR #62. The remaining tidy changes were ported through PR #63 and merged as `88044a1`; its exact-head run #685 passed all eight Ubuntu/Windows Python 3.11–3.14 jobs. The old `chore/repo-tidy` branch remains stale and was not merged directly. PR #61 is unrelated (`cleanup/lean-v0.6`).

## Tests
Local report dated 2026-11-17: 308 passed, 2 xfailed on Windows, Python 3.14; hygiene scan PASS (126 tracked paths). The historical 2026-11-17 report's two xfails were the two `hint` variants of one strict xfail in `tests/test_relation_wording.py::test_two_hop_reaches_the_second_dependency_owner`. Batch 1 removes the marker and adds targeted regression coverage; exact-head test validation is pending. PR #63 added Python 3.14 and exact-head CI run #685 passed all eight Ubuntu/Windows Python 3.11–3.14 jobs. CI #641's failed Windows 3.13 job was inspected: 287 passed, one duration-mode benchmark test failed because a 0.5-second window recorded zero successful requests. The test window is now 2.0 seconds; validation is pending.

## Blockers
- R0.5: the two formerly uncommitted test files are present in `main` and run in CI, but the old local working-folder copy cannot be retired or verified from GitHub.
- R0.5 remains open until the old local working-folder copy is retired by its owner.
- DBG-002 is diagnosed; its timing-test stabilization is pending CI. DBG-007 and the two former xfail variants remain pending exact-head test and benchmark evidence.
- Remote use needs an independent reviewer (R3.5) and a deploy account (R3.6).

## Next work
1. Retire the old local working folder to close R0.5; GitHub cannot verify the user's local disk.
2. Complete Batch 1 PR #64: pass all eight CI jobs, run and inspect the paired before/after benchmark artifact, fix any regressions, then update the benchmark report and acceptance docs. Do not merge on source review alone.
3. Resolve R0.4 by adding the release/changelog procedure after retrieval behavior is accepted. Prepare Batch 2 only after the user supplies and freezes 20–40 consented real-history cases.

## Evidence so far (synthetic only)
Graph retrieval is NOT JUSTIFIED under the pre-registered v3 rule (hash and spaCy embedders). It wins only multi-hop, and a post-hoc iterative flat baseline erases even that. See `benchmarks/r2_labelled_v3.md` and `benchmarks/r2_post_hoc_iterative_baseline.md`. Unproven until real data (G1).

## Open defects
DBG-002 (Windows duration-test timing failure diagnosed; 2.0-second test stabilization pending CI), DBG-007 (retrieval fixes implemented in PR #64; pending tests and benchmark), DBG-008 (two strict xfail marks removed in PR #64; pending exact-head CI).

## Open external gates
Held-out real-history evaluation NOT RUN. Independent security and privacy review NOT PERFORMED. Real third-party host integration NOT VERIFIED. Independent acceptance sign-off OPEN. Not production-ready; loopback only.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
