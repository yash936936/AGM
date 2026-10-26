## DBG-068 — REST soak/RSS benchmark syntax and CLI fix — 2026-10-26

**Branch:** `bench/soak-rss-followup`, existing PR #60. The latest observed CI run before this fix was [40308707267](https://github.com/yash936936/AGM/actions/runs/40308707267).

**Observed failure:** all six Python/OS jobs failed during pytest because `eval/rest_concurrent_benchmark.py` contained literal backslash-n sequences in a dictionary and did not define `--duration-seconds` / `--sample-interval`. The failing tests were the three in `tests/test_rest_concurrent_benchmark.py`. The log showed 274 passed and 3 failed in the Windows Python 3.13 job; the other matrix jobs also failed in the same test step. Hygiene and whitespace checks completed successfully.

**Fix committed:** rewrote the benchmark script to remove the syntax errors, add duration-mode worker loops, add positive-value validation, and periodically sample process RSS/working-set on supported operating systems. Updated the benchmark instructions to describe the actual behavior and limitations.

**Validation:** exact-head CI after fix: NOT YET VERIFIED. Do not mark tests passed until the new workflow result is observed. Local pytest: NOT RUN in this remote editing environment.

**Release boundary:** this fixes the observed benchmark test failure only. M0/M1/M2 repository acceptance evidence is recorded in `docs/acceptance/m0_m1_m2_traceability_audit.md`; independent acceptance-matrix sign-off and external real-history, security/privacy, and third-party-host gates remain OPEN. M2 remains NOT ACCEPTED.
