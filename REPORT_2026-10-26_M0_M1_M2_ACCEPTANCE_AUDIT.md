# REPORT_2026-10-26_M0_M1_M2_ACCEPTANCE_AUDIT

## Files changed
- eval/stale_facts.py: added --archive-size to vary unrelated synthetic archive records and emitted the size in JSON and text metadata.
- tests/test_eval.py: added CLI coverage for zero and negative archive size, plus JSON metadata.
- tests/test_m2_acceptance_lifecycle.py: added same-tenant cross-project context isolation and authorized correction/delete replay/reopen coverage.
- docs/benchmarks/synthetic_retrieval_smoke.md: documented archive-size sweeps and limitations.
- docs/acceptance/m0_m1_m2_traceability_audit.md: mapped M0/M1/M2 requirements to existing tests and explicitly recorded open gaps and external gates.
- context.md, docs/status.md, docs/debug.md: task/status records.

## What the new tests are intended to prove
- Benchmark CLI tests: archive-size configuration is validated and appears in machine-readable output.
- Project isolation test: active-memory context preparation does not include a same-tenant memory from another project.
- M2 lifecycle test: correction requires authorization/scope/confirmation, retains correction history, hard deletion scrubs deleted current content, and replay/reopen does not restore the deleted value.

## Validation
- Local pytest: NOT RUN in this remote editing environment.
- GitHub Actions exact-head run [40304904729](https://github.com/yash936936/AGM/actions/runs/40304904729): all six Ubuntu/Windows Python 3.11–3.13 jobs passed. PR #56 merged at `8a3cecbfadc9b349cc95618967298bfa85a71a2e`.
- The same exact-head workflow passed the repository test matrix, REST/MCP smoke clients, hygiene, whitespace, and package inspection jobs (all six jobs successful).
- External held-out real-history evaluation: NOT RUN.
- Independent security/privacy review: NOT PERFORMED.
- Real third-party-host integration: NOT VERIFIED.

## Contract concerns
- No REST path, MCP tool name, public model, dependency, or executor-surface change is intended.
- D-037 remains in force: proposal execution is library-only.

## Assumptions and unfinished items
- The synthetic archive-size sweep is a diagnostic for size sensitivity, not a concurrent load test or a production benchmark.
- Full end-to-end latency, concurrent/sustained throughput, uncertainty estimates, and pinned-environment multi-run results remain future benchmark work.
- The acceptance matrix needs independent reviewer sign-off.
- The three external release gates remain open; M2 is NOT ACCEPTED and AGM is NOT certified production-ready.