## 2026-10-26 — REST soak/RSS benchmark CI repair submitted

PR #60 branch `bench/soak-rss-followup` had failing exact-head CI run [40308707267](https://github.com/yash936936/AGM/actions/runs/40308707267). The failures came from literal backslash-n characters in `eval/rest_concurrent_benchmark.py` and missing duration/RSS CLI implementation. The script and benchmark instructions have now been corrected on the same PR branch. New exact-head CI is **NOT YET VERIFIED**; do not report the repair as passing until a fresh workflow completes.

M0/M1/M2 repository regression coverage and traceability audit are already merged in PR #56 with exact-head CI [40304904729](https://github.com/yash936936/AGM/actions/runs/40304904729) passing all six Ubuntu/Windows Python 3.11–3.13 jobs. Independent acceptance-matrix sign-off remains OPEN. External release gates remain OPEN: held-out explicitly consented real-history evaluation NOT RUN, independent security/privacy review NOT PERFORMED, and actual third-party-host integration NOT VERIFIED. M2 is NOT ACCEPTED; production readiness is not established.

---
