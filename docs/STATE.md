# State — AGM prototype

Last updated 2026-11-20. Entry point: [`context.md`](../context.md).

## Where we are

AGM is a v0.7.x local-only prototype. PR #66 merged as `9622a53`, adding isolated before/after synthetic benchmark environments. Follow-up retrieval fixes are on `main`:
- `b5b6e73`: correct exact-entity boundary matching.
- `77ec098`: separate the flat `location` answer slot from `region` and preserve direct entity facts for relationally worded queries.
- `d7816d9`: apply the same `location`/`region` answer-slot distinction in graph retrieval.

Exact-head GitHub Actions run [#781](https://github.com/yash936936/AGM/actions/runs/44638717065), commit `d7816d9`, passed all eight Ubuntu/Windows Python 3.11–3.14 jobs. Those jobs include pytest, repository hygiene, REST smoke client and package inspection. Run #780 on `77ec098` failed two historical-location tests; #781 passed after the graph slot-mapping fix.

## Batch 1 acceptance

**NOT ACCEPTED.** The paired benchmark job was skipped on push runs #780 and #781. The last available paired synthetic result was on `c6e9eb7`, not the final merged head. It showed 50.7% unanswerable correctness, below the roadmap requirement of at least 80%; synthetic results are diagnostic only. A final-head paired artifact and resolution of the unanswerable threshold are still required. No real-history evidence exists.

## Next work

1. Run the paired base/head synthetic benchmark against the final retrieval code and inspect its artifact. Do not treat it as real-history evidence.
2. Address the Batch 1 unanswerable-correctness gap without reducing single-fact recall by more than 0.02; rerun tests and benchmark.
3. Batch 2 is **BLOCKED** on the owner freezing 20–40 de-identified, consented cases locally under the private `eval/real/` path. The repository already has the local authoring script, evaluator, keyword baseline, protocol and runbook. Do not create/run the real-history harness or evaluation before the cases are frozen. Raw cases must not be committed or uploaded; share aggregate reports only.
4. After the cases are frozen, build the aggregate-only multi-baseline runner and agent A/B harness described in `docs/BUILD-PLAN.md`.

## Evidence and external gates

Synthetic benchmark evidence is diagnostic only. G1 (whether graph retrieval should remain on by default) is OPEN. Held-out real-history evaluation is NOT RUN. Independent security/privacy review is NOT PERFORMED. Third-party host validation is NOT VERIFIED. Remote access remains loopback-only; the project is not production-ready.

## Open defects and blockers

- DBG-007 / DBG-010: Batch 1 answer-slot, abstention and sibling-entity behavior is implemented, but acceptance is pending final benchmark evidence and the ≥0.80 unanswerable target.
- R0.5: old local working-folder retirement cannot be verified from GitHub.
- R0.4: changelog and local release procedure exist; v0.7.0 tagging remains gated on Batch 1 acceptance and package checks.
- R2.2–R2.4 / G1: blocked on the frozen private 20–40-case real-history set.
- R3.5: independent security reviewer not yet supplied.
- R3.6: deploy account and tested controlled deployment remain outstanding.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task.
