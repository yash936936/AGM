## 2026-10-26 — REST soak/RSS benchmark CI repair submitted

The existing PR #60 branch `bench/soak-rss-followup` had failing workflow [40308707267](https://github.com/yash936936/AGM/actions/runs/40308707267): literal backslash-n sequences caused a SyntaxError and duration/RSS CLI arguments were missing. The script and instructions have been corrected on that same branch. Exact-head CI after the repair is NOT YET VERIFIED; local pytest was NOT RUN in the remote editing environment.

M0/M1/M2 repository coverage is already merged through PR #56 and its exact-head CI [40304904729](https://github.com/yash936936/AGM/actions/runs/40304904729). Remaining acceptance blockers are independent acceptance-matrix sign-off, held-out consented real-history evaluation, independent security/privacy review, and real third-party-host integration. Do not mark M2 accepted or AGM production-ready until these gates have actual evidence.

---
