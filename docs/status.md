## 2026-10-26 — Concurrent REST retrieval benchmark candidate

Branch `bench/rest-concurrent-load` adds `eval/rest_concurrent_benchmark.py`, which launches the real local REST API and measures concurrent HTTP retrieval endpoint latency, p50/p95/p99, successful throughput, request/error counts, and workload/environment metadata. Includes an integration test and scope/limitations documentation. Exact-head CI is pending. This is synthetic loopback diagnostic evidence only, not a production benchmark; memory/RSS, cold start, sustained load, real-history evaluation and external host integration are not measured. Held-out consented real-history evaluation, independent security/privacy review, real third-party-host integration, and independent acceptance-matrix sign-off remain OPEN. M2 remains NOT ACCEPTED; do not claim production readiness.

---

## 2026-10-26 — Repeated-run synthetic benchmark candidate

Branch `bench/repeated-run-uncertainty` adds `eval/repeated_retrieval_benchmark.py`, which launches independent synthetic benchmark processes, retains raw per-run JSON, and summarizes run-level medians with deterministic 95% percentile-bootstrap intervals. It also adds `tests/test_repeated_retrieval_benchmark.py` and usage/limitations documentation. This is a candidate until exact-head CI passes. It remains sequential retrieval-only synthetic timing; concurrency, host/API end-to-end latency, sustained load, real-history evaluation, and release gates are not covered.

---

## 2026-10-26 — Consolidated M0/M1/M2 acceptance audit merged

PR [#56](https://github.com/yash936936/AGM/pull/56) merged at `8a3cecbfadc9b349cc95618967298bfa85a71a2e`. Exact-head workflow [40304904729](https://github.com/yash936936/AGM/actions/runs/40304904729) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. It adds M0/M1/M2 requirement-to-test traceability, a same-tenant cross-project active-context isolation regression, an authorized correction/delete/rebuild/reopen lifecycle regression, and configurable synthetic archive-size benchmark sweeps.

Local pytest was NOT RUN in the remote editing environment. The traceability matrix needs independent reviewer sign-off. Benchmark sweeps remain synthetic and sequential; concurrent load, end-to-end latency and uncertainty reporting remain unimplemented. External release gates remain: consented held-out real-history evaluation NOT RUN, independent security/privacy review NOT PERFORMED, and real third-party-host integration NOT VERIFIED. **M2 remains NOT ACCEPTED; production readiness is not established.**

---

## 2026-10-26 — M2 closure audit merged; external gates remain open

**Status: M2 IMPLEMENTATION VERIFIED BY REPOSITORY CI; M2 NOT ACCEPTED.** PR #51 merged at `28fd9f5030f670ee16ff363d3594ad3b4a80914f`. Corrected exact-head GitHub Actions run [40300716725](https://github.com/yash936936/AGM/actions/runs/40300716725) passed all six Ubuntu/Windows Python 3.11–3.13 jobs, covering the full test suite, REST/MCP smoke clients, repository hygiene, whitespace, and wheel/package inspection. Local pytest was NOT RUN in the remote editing environment.

**Audit result:** Policy/executor target alignment, including the correction target guard, is implemented and covered by regression tests. The proposal executor remains library-only under D-037; REST/MCP smoke tests are adapter smoke tests, not executor-parity evidence. The reference host is an integration harness, not a production authentication implementation.

**Still open:** held-out consented real-history evaluation; independent security/privacy review; actual integration acceptance by a real third-party host. M2 and production readiness remain NOT ACCEPTED until these external gates are completed.

---

## 2026-10-26 — Reference host integration harness candidate

**Status: MERGED REFERENCE HARNESS; M2 NOT ACCEPTED.** PR #49 merged at `5fffbb23d0591a48f0bbd82472cbc0c4f3cd52ba`; exact-head run [40298108786](https://github.com/yash936936/AGM/actions/runs/40298108786) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. Added `src/agm/reference_host.py` as a dependency-free example of trusted host identity resolution, scoped `Ctx`/permissions, current-message proposal review, host-verified mutation confirmation, and explicit executor invocation. Added tests for missing identity, confirmation denial, tenant isolation, rejected proposals not mutating the event log, and the correction/history/delete/rebuild lifecycle.

**Validation:** Local pytest NOT RUN in this remote editing environment. A follow-up branch `m2/policy-executor-contract-alignment` tightens history/delete target validation; its exact-head CI is pending. See `REPORT_M2_REFERENCE_HOST.md`.

**External gates:** Real third-party host integration remains OPEN; this harness is not itself a third-party host. Held-out consented real-history evaluation and independent security/privacy review remain OPEN / PENDING.

---

## 2026-10-26 — M2 proposal executor surface boundary and guardrail CI

PR #47 merged at `4641796ef1a7ac6b3dfbac6abb33e04c63fb2f70`. Exact-head GitHub Actions run [40229139385](https://github.com/yash936936/AGM/actions/runs/40229139385) passed all six Ubuntu/Windows Python 3.11–3.13 jobs, including the full test suite, REST smoke, MCP fresh-session smoke, hygiene, whitespace, and package inspection.

Added D-037 to explicitly define `execute_authorized_memory_proposal()` as a library-only API while REST/MCP keep their frozen direct-store contracts. This avoids claiming parity for proposal-policy and confirmation behavior that the adapters do not expose. Any future adapter integration requires a separate contract decision and cross-surface tests.

**Status:** M2 remains IMPLEMENTATION CANDIDATE / NOT ACCEPTED. Remaining code-review items include trusted-host authorization integration and any decision to expose proposal execution through adapters. Held-out real-history evaluation, independent security/privacy review, and third-party host integration remain OPEN / PENDING.

---

## 2026-10-26 — M2 authorized execution candidate

**Status:** IMPLEMENTATION CANDIDATE / NOT ACCEPTED. Added `execute_authorized_memory_proposal()` to connect policy review to existing scoped store methods for write, correction, history, and deletion. It re-evaluates policy, checks the required scope, requires host authorization, and requires confirmation for mutations.

**Regression coverage authored:** explicit authorization/scope/confirmation denial; write, correction, history, delete; rebuild/reopen and deleted-payload scrubbing; tenant isolation. These tests and the implementation have not yet passed current-head CI.

**Validation evidence:** Prior candidate commit `5dcf7d86818f9a4c3bd9a7c8350235934ac92340` passed all six CI jobs in [run 40227572306](https://github.com/yash936936/AGM/actions/runs/40227572306), but that run predates these changes and is not evidence for the current head. Local execution was blocked because GitHub DNS/network access was unavailable. Current-head CI and adapter parity remain pending. See `REPORT_M2_ACTIVE_MEMORY.md`.

**External gates:** Held-out real-history evaluation, independent security/privacy review, and third-party host integration remain **OPEN / PENDING**.

---

## 2026-10-26 — M2 active-turn orchestration candidate

**Status:** IMPLEMENTED CANDIDATE / NOT ACCEPTED. Added `src/agm/active_memory_turn.py` for read-only pre-answer context preparation and proposal review. Eligible proposals are surfaced for host review only; this code does not persist them or grant mutation authorization.

**Tests added:** `tests/test_active_memory_turn.py` covers read-only event-log behavior, context budget validation, proposal eligibility/rejection, and the host authorization boundary.

**Validation:** NOT RUN in this remote editing environment. Focused/full pytest, REST/MCP smoke clients, hygiene/whitespace/package checks, and exact-head CI remain pending. See `REPORT_M2_ACTIVE_MEMORY.md`.

**External gates:** Held-out real-history evaluation, independent security/privacy review, and third-party host integration remain **OPEN / PENDING**.

---

## 2026-10-26 — M2 kickoff and external gates status

### External release gates

| Gate | Status | Pending evidence |
|---|---|---|
| Held-out real-history evaluation | **OPEN / PENDING** | Consented, de-identified dataset and reviewed benchmark results |
| Independent security/privacy review | **OPEN / PENDING** | Independent reviewer findings and sign-off |
| Third-party host integration | **OPEN / PENDING** | Recorded test against a real host using synthetic data |

These gates remain pending until the required evidence is actually produced and reviewed. Documentation and synthetic CI do not close them.

### M2: active memory behavior

**Status: STARTED, implementation not yet accepted.** Begin with `docs/acceptance/m2_active_memory_execution_brief.md`. Existing `active_memory.py` prepares pre-answer context and `active_memory_policy.py` evaluates proposed operations; M2 must verify and connect the before/during/after-turn lifecycle while preserving explicit authorization for mutations, tenant/project scope, replay safety, untrusted-memory boundaries, and frozen adapter contracts.

**Validation:** No tests run for M2 in this remote repository-editing step. Do not claim implementation or acceptance until code changes have exact-head CI and review evidence.
## 2026-10-26 — External-gate tracking documentation CI verified

**PR:** [#42](https://github.com/yash936936/AGM/pull/42), merged at `0d1b60bd3d27e8422c0fd31f3714d03a17fadc61`.
**Exact-head CI:** [Run 40226444920](https://github.com/yash936936/AGM/actions/runs/40226444920) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. Each job completed pytest, REST and MCP fresh-session smoke clients, repository hygiene, whitespace checks, and wheel/package inspection.
**Scope:** Documentation-only status tracking. This validates the repository workflow at the PR head; it does not close the held-out real-history evaluation, independent security/privacy review, or real third-party host integration gates. All three remain OPEN.

---

## 2026-10-26 — External release-gate protocols merged

**PR:** [#41](https://github.com/yash936936/AGM/pull/41), merge commit `73b56aa7b9a98cbe185c3d27c736667cb42e9d5a`.

Added:
- `docs/acceptance/real_history_evaluation_protocol.md`: consent, minimization, held-out split hygiene, frozen thresholds, baselines, metrics, stop conditions, and required evidence.
- `docs/acceptance/security_privacy_review_checklist.md`: independent reviewer scope, threat model, lifecycle/privacy/API checks, finding triage, and sign-off.
- `docs/acceptance/third_party_host_validation.md`: safe synthetic setup, host/version record, interoperability matrix, and sanitized evidence requirements.

**Status:** Protocols are documented, but all three release gates remain OPEN. No consented dataset was provided, no independent review was conducted, and no real third-party host was tested. Documentation does not substitute for external evidence.

**Validation:** No tests were run in this environment. Exact-head workflow runs were not visible at the time of review. Do not infer CI success from the merge.

---

## 2026-10-26 — M0 and M1 acceptance PRs merged

### M0 retention/replay
- **Merged:** [PR #39](https://github.com/yash936936/AGM/pull/39), `ff74460daf3c6585c5820e380320cb8cfc134475`.
- **CI:** [Run 40224653021](https://github.com/yash936936/AGM/actions/runs/40224653021), all six Ubuntu/Windows Python 3.11–3.13 jobs passed, including full tests, hygiene, whitespace and package inspection.
- **Verified regression:** Revoked pinned source content remains retained under default expiry across replay; explicit `include_pinned=True` scrubs it while preserving the revocation audit event.

### M1 lifecycle and adapters
- **Merged:** [PR #40](https://github.com/yash936936/AGM/pull/40), `d27c6475d51263df6b75a0309438530b352665d6`.
- **CI:** [Run 40224688462](https://github.com/yash936936/AGM/actions/runs/40224688462), all six Ubuntu/Windows Python 3.11–3.13 jobs passed, including full tests, REST smoke client, MCP fresh-session smoke client, hygiene, whitespace and package inspection.
- **Verified regression:** Cross-session recall after correction, history retention, deletion of both versions, and no retrieval or source-payload resurfacing after rebuild/reopen.

### Remaining release gates
- **Held-out, consented real-history evaluation:** NOT COMPLETED. No such dataset/results were supplied or generated by CI.
- **Independent security/privacy review:** NOT COMPLETED. Requires an actual independent review.
- **External real-host integration:** Repository REST/MCP smoke clients pass in CI; validation against a real third-party host remains separate.

M0 retention/replay regression and M1 core lifecycle/adapter CI items are verified. Do not label the overall production-readiness gate complete while the external evaluation and review remain open.

---

## 2026-10-26 — M1 cross-session lifecycle acceptance candidate

**Branch:** `acceptance/m1-cross-session-lifecycle-closure`.

**Change:** Adds `test_cross_session_recall_correction_delete_and_rebuild`, covering recall from a fresh `MemoryStore`, correction history, hard deletion of both versions, and no retrieval or source-payload resurfacing after rebuild and reopen.

**Validation:** Exact-head CI pending. Existing merged CI verifies the bounded before-turn context, positional API compatibility, provenance, boundary escaping, quarantine snapshot filtering, and Obsidian source-span metadata. The full M1 matrix is not yet closed: local Windows smoke clients, held-out consented real-history evaluation, and independent security/privacy review remain open.
## 2026-10-26 — M0 retention and replay closure candidate

**Branch:** `acceptance/m0-retention-replay-closure`.

**Change:** Adds `test_revoked_pinned_source_survives_default_expiry_and_replay`: revoked pinned source content must survive default expiry and a view rebuild, then be scrubbed only with `include_pinned=True`, while the compact revocation audit event remains. This closes a specific missing regression, not the whole M0 matrix.

**Validation:** Exact-head CI pending. Do not mark M0 complete until the full current-main acceptance matrix is green and reviewed. Held-out real-history evaluation and independent security/privacy review remain open release gates.

---

## 2026-10-26 — M1 Obsidian export provenance merged

**Merged:** PR [#37](https://github.com/yash936936/AGM/pull/37), merge commit `f19aa818a00dc9995077721fc108c08d295362a7`.

**Validation:** Exact-head CI [40223870098](https://github.com/yash936936/AGM/actions/runs/40223870098) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. Regression coverage verifies source episode ID and start/end span coordinates in deterministic export frontmatter.

**Status:** M1 remains PARTIAL / VERIFY because the full acceptance matrix and local Windows integration checks remain outstanding. M0 remains IN PROGRESS; real-history evaluation and independent security/privacy review remain open.

---

## 2026-10-26 — M1 lifecycle context review fixes merged

**Merged:** PR [#34](https://github.com/yash936936/AGM/pull/34), merge commit `1c546392267cdd86a97b76e4979fae26cb141033`.

**Validation:** Exact-head CI [40223512300](https://github.com/yash936936/AGM/actions/runs/40223512300) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. Fixes preserve positional request compatibility, retain source provenance, and prevent untrusted memory values from creating new context lines or closing record framing.

**Status:** M1 remains PARTIAL / VERIFY; M0 remains IN PROGRESS. Held-out real-history evaluation and independent security/privacy review remain open.

---

## 2026-10-26 — M1 Obsidian export provenance follow-up on current main

**Finding:** `export_obsidian()` exported stable memory IDs and event metadata but omitted source episode/span fields, losing provenance required by the M1 acceptance contract.

**Change:** Branch `fix/m1-obsidian-export-provenance-v2` adds `source_episode_id`, `source_span_start`, and `source_span_end` frontmatter fields and a regression test using a synthetic source episode/span.

**Validation:** NOT RUN locally in this remote editing environment. Exact-head CI and review pending. M1 remains PARTIAL / VERIFY; M0 remains IN PROGRESS. Held-out real-history evaluation and independent security/privacy review remain open.

---

## 2026-10-26 — M1 lifecycle context review follow-up in progress

**Finding:** PR #32's bounded before-turn lifecycle change passed exact-head CI run [40221564276](https://github.com/yash936936/AGM/actions/runs/40221564276), all six Ubuntu/Windows Python 3.11–3.13 jobs. Review then identified that adding `token_budget` in the middle of `BeforeTurnRequest` shifted existing positional arguments, shared context rendering dropped source provenance, and raw memory text could forge a closing memory-record delimiter.

**Candidate:** `fix/m1-lifecycle-context-review-findings` appends `token_budget` to preserve the old positional signature, includes provenance in the shared renderer, flattens newlines and escapes angle-bracket delimiters in untrusted values, and adds regression tests.

**CI feedback:** Initial follow-up run [40222469817](https://github.com/yash936936/AGM/actions/runs/40222469817) found two test-fixture issues: the 180-token budget became too small after provenance was restored, and the boundary test passed literal backslash-n characters rather than line breaks. The budget is now 240 and the boundary test uses actual newlines. Latest-head run [40222677766](https://github.com/yash936936/AGM/actions/runs/40222677766) is queued.

**Validation:** NOT RUN locally in this remote editing environment. Exact-head CI and review are pending. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY. Held-out consented real-history evaluation and independent security/privacy review remain open.

---

## 2026-10-26 — M1 lifecycle context review follow-up in progress

**Finding:** PR #32's bounded before-turn lifecycle change passed exact-head CI run [40221564276](https://github.com/yash936936/AGM/actions/runs/40221564276), all six Ubuntu/Windows Python 3.11–3.13 jobs. Review then identified that adding `token_budget` in the middle of `BeforeTurnRequest` shifted existing positional arguments, shared context rendering dropped source provenance, and raw memory text could forge a closing `<memory_records>` delimiter.

**Candidate:** `fix/m1-lifecycle-context-review-findings` appends `token_budget` to preserve the old positional signature, includes provenance in the shared renderer, flattens newlines and escapes angle-bracket delimiters in untrusted values, and adds regression tests.

**Validation:** NOT RUN locally in this remote editing environment. Exact-head CI and review are pending. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY. Held-out consented real-history evaluation and independent security/privacy review remain open.
## 2026-10-26 — M1 lifecycle review follow-up in progress

**Finding:** Post-merge review of PR #32 identified three issues: adding `token_budget` in the middle of the dataclass fields breaks existing positional callers; shared context rendering drops `Node.provenance`; and multiline memory text can imitate a closing `</memory_records>` boundary.

**Change candidate:** Branch `fix/m1-lifecycle-review-findings` appends the budget field after existing fields, serializes provenance into the bounded record, flattens CR/LF from untrusted memory text, and adds regression tests for positional compatibility, provenance retention, and boundary-injection resistance.

**Validation:** Initial exact-head CI run [40222174178](https://github.com/yash936936/AGM/actions/runs/40222174178) exposed two test issues (short record exceeded the original small budget after provenance metadata was added; the adversarial fixture used literal backslash-n sequences instead of actual line breaks). Both test fixtures were corrected and a direct provenance-rendering regression was added. A fresh exact-head CI run is required; local tests remain NOT RUN in this remote editing environment. PR #32 itself merged at `63826e826a2de02ec83fb284acae687f17293025` with run [40221564276](https://github.com/yash936936/AGM/actions/runs/40221564276) passing six jobs; those results do not validate this follow-up. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY.

---

## 2026-10-25 — M1 before-turn context budget enforcement in review

**Branch:** `fix/m1-bounded-before-turn-context`.

**Finding:** The older `MemoryLifecycle.before_turn()` rendered every retrieved item directly and accepted an unbounded `top_k`; the separate active-memory packer already provided token-budget enforcement, but this lifecycle entry point did not use it.

**Change:** Delegate rendering to `prepare_turn_context()`, add an explicit token budget, require positive integer `top_k` and token budget values, and test that oversized records are omitted while included IDs match the rendered context.

**Merged baseline:** PR [#31](https://github.com/yash936936/AGM/pull/31), merge commit `7d44e3fdea3a7cf87319b92efd52ebcca0bb7129`; exact-head CI run [40221085442](https://github.com/yash936936/AGM/actions/runs/40221085442) passed all six Linux/Windows Python 3.11–3.13 jobs.

**Validation:** New exact-head CI pending; local tests NOT RUN in this remote editing environment. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY.

---

## 2026-10-25 — M1 graph snapshot quarantine filter in review

**Branch:** `fix/m1-snapshot-quarantine-filter`.

**Finding:** `graph_snapshot()` returned every node in tenant/project scope, including nodes marked `quarantined`. Unlike ordinary retrieval and Obsidian export, the snapshot path did not exclude instruction-like quarantined content.

**Change:** Filter quarantined nodes at the node query and at edge endpoint subqueries. Add a regression that stores instruction-like text, confirms the write was quarantined, and asserts neither the node nor its marker appears in the snapshot.

**Merged M0 baseline:** PR [#30](https://github.com/yash936936/AGM/pull/30), merge commit `409e5136b5af626b14349417ccdc7a2b8bc6c209`; exact-head CI run [40220628800](https://github.com/yash936936/AGM/actions/runs/40220628800) passed all six Linux/Windows Python 3.11–3.13 jobs.

**Validation:** New exact-head CI pending; local tests NOT RUN in this remote editing environment. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY.

---

## 2026-10-25 — M0 orphan-scrub failure rollback candidate

**Branch:** `test/m0-orphan-scrub-rollback`.

**Coverage added:** The expiry sweep deletes an aged live item and then encounters a forced SQLite trigger failure while scrubbing an aged revoked-writer orphan payload. The regression checks that the earlier live-item deletion, both source payloads, event count, and transaction state are rolled back; reopening and rebuilding views must preserve the live item and keep the revoked orphan absent.

**Merged baseline:** PR [#29](https://github.com/yash936936/AGM/pull/29), merge commit `85b8c55555866fa67ad1008b073b28429e73a798`; exact-head CI run [40219869374](https://github.com/yash936936/AGM/actions/runs/40219869374) passed all six Linux/Windows Python 3.11–3.13 jobs.

**Validation:** New candidate CI pending; local tests NOT RUN in this remote editing environment. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY; held-out real-history evaluation and independent security/privacy review remain open.

---

## 2026-10-25 — Multi-item expiry sweep atomicity regression in review

**Candidate branch:** `test/m0-multi-item-expiry-rollback`.

**Coverage added:** A two-item expiry sweep now injects failure after the second real nested delete handler has mutated views. Assertions verify that the entire sweep restores both source payloads, event count, both active nodes, transaction state, and retrieval after reopen/rebuild.

**Baseline:** PR [#28](https://github.com/yash936936/AGM/pull/28) merged at `9db3fbaf9dc3a039f2198b6c61e9340619df7f9b`; exact-head CI run [40219212770](https://github.com/yash936936/AGM/actions/runs/40219212770) passed all six Linux/Windows Python 3.11–3.13 jobs.

**Validation:** Follow-up exact-head CI pending. Local tests NOT RUN in this remote editing environment. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY; held-out real-history evaluation and independent security/privacy review remain open.

---

## 2026-10-25 — Post-mutation expiry rollback acceptance merged

**Merged:** PR [#28](https://github.com/yash936936/AGM/pull/28), merge commit `9db3fbaf9dc3a039f2198b6c61e9340619df7f9b`.

**Validation:** Exact-head CI run [40219212770](https://github.com/yash936936/AGM/actions/runs/40219212770) passed all six Linux/Windows Python 3.11–3.13 jobs, including the full test suite, repository hygiene, whitespace checks, and wheel/package inspection. The regression invokes the real nested delete handler and then injects failure, exercising rollback after the handler's view mutation; it verifies payload/event count, active node state, transaction closure, and retrieval after reopen/rebuild.

**Limits:** Local tests NOT RUN in this remote editing environment. This is synthetic failure-injection coverage, not independent security/privacy review. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY. Held-out consented real-history evaluation remains NOT RUN and independent security/privacy review remains NOT ESTABLISHED.

---

## 2026-10-25 — Expiry rollback regression strengthened after review

**Merged baseline:** PR [#27](https://github.com/yash936936/AGM/pull/27) merged at `2a9a003b7bfa4bf162661e420a692e155b7b1719`; exact-head CI run [40218590007](https://github.com/yash936936/AGM/actions/runs/40218590007) passed all six Linux/Windows Python 3.11–3.13 jobs.

**Review follow-up:** The original failure injection occurred before the nested delete handler mutated derived views. Candidate branch `test/m0-expiry-post-mutation-rollback` changes the hook to invoke the real handler and then raise, so the test checks rollback after the nested handler has performed its mutation.

**Validation:** Exact-head CI for this follow-up is pending. Local tests NOT RUN in this remote editing environment. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY. Held-out consented real-history evaluation remains NOT RUN and independent security/privacy review remains NOT ESTABLISHED.

---

## 2026-10-25 — M0 expiry atomic-rollback regression in review

**Candidate branch:** `test/m0-expiry-atomic-rollback`.

**Coverage added:** Inject a failure during the nested delete operation inside an expiry sweep and assert that source payload scrubbing, event insertion, and node-state changes all roll back together. Reopen the database and rebuild views to confirm the memory remains retrievable.

**Validation:** NOT RUN locally in this remote editing environment. Exact-head Linux/Windows Python 3.11–3.13 CI, repository hygiene, whitespace checks, and wheel/package inspection are required before acceptance. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY. Held-out real-history evaluation remains NOT RUN and independent security/privacy review remains NOT ESTABLISHED.

---

## 2026-10-25 — M0 retention orphan-scrub scope acceptance merged

**Merged:** PR [#26](https://github.com/yash936936/AGM/pull/26), merge commit `f68aa2878e662ee7cb46099612aef27d60cfb4d1`.

**Validation:** Exact-head CI run [40217991980](https://github.com/yash936936/AGM/actions/runs/40217991980) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. The regression covers tenant/project scope for orphan source-payload scrubbing after writer revocation, idempotent repeated expiry, and isolation after reopen/rebuild. Local tests were not run in this remote editing environment.

**Remaining gates:** M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY. Held-out consented real-history evaluation is NOT RUN and independent security/privacy review is NOT ESTABLISHED.

---

## 2026-10-25 — M0 retention orphan-scrub scope acceptance in review

**Candidate branch:** `test/m0-retention-orphan-scope`.

**Coverage added:** Create aged source events in the target tenant/project, a sibling project, and a sibling tenant; revoke the target writer to create an orphan source event; run expiry twice; assert only the target project source payload is scrubbed and the decision survives view rebuild/reopen. The regression uses synthetic marker strings only.

**Validation:** NOT RUN locally in this remote editing environment. Exact-head Linux/Windows Python 3.11–3.13 CI, package inspection, repository hygiene, and whitespace checks are required before acceptance. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY. Held-out real-history evaluation remains NOT RUN and independent security/privacy review remains NOT ESTABLISHED.

---

## 2026-10-25 — Connection validation merged; post-merge test cleanup in review

**Merged:** PR [#24](https://github.com/yash936936/AGM/pull/24), merge commit `571edd5082b10bfcce169d4e3fddddedee1e8aeb`. Exact-head CI run [40216605734](https://github.com/yash936936/AGM/actions/runs/40216605734) passed all six Linux/Windows Python 3.11–3.13 jobs.

**Change:** Explicit empty or malformed connection scope values now fail closed; only omitted scopes default to `memory:read`. Diagnostic timeouts must be finite positive numbers and cannot be booleans.

**Follow-up:** A post-merge audit found the new parameterized scope/timeout test block was duplicated. Branch `chore/post-merge-audit-cleanup` removes the duplicate definition while retaining the test cases. Cleanup CI is pending; do not treat that branch as verified yet.

**Release status:** M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY. Held-out real-history evaluation is NOT RUN and independent security/privacy review is NOT ESTABLISHED.

---

## 2026-10-25 — M1 connection input-validation follow-up

**Branch:** `fix/hub-connection-validation`.

**Finding/change:** Explicit `scopes=[]` previously defaulted silently to `memory:read`; malformed scope types could raise inconsistent exceptions, and invalid diagnostic timeouts were not rejected at the API-helper boundary. The candidate distinguishes omitted scopes from explicit empty lists, validates scope types, and requires finite positive diagnostic timeouts.

**Validation:** Local tests NOT RUN. Exact-head CI, package inspection, repository hygiene and whitespace checks are required before acceptance. M1 remains PARTIAL / VERIFY; M0 remains IN PROGRESS. Real-history evaluation and independent security/privacy review remain open.

---

## 2026-10-25 — Benchmark acceptance suite and keyword baseline in review

**Current branch:** `work/benchmark-acceptance-baselines`, based on PR #15's peak-RSS/concurrency candidate.

**Implemented in this increment:** strengthened Windows peak-working-set API signatures; added opt-in `--repetitions` with per-run concurrent p50/p95/p99, throughput and error summaries; added `examples/benchmark_acceptance.synthetic.jsonl` with 10 labelled cases covering cross-session recall, relevance, abstention, temporal correction, deletion, revocation, expiry and tenant isolation; added a token-overlap lexical baseline to paired reports and standalone `python -m eval.keyword_baseline`.

**Validation:** PR #15 exact-head CI passed all six Linux/Windows Python 3.11–3.13 jobs in [run 40210586141](https://github.com/yash936936/AGM/actions/runs/40210586141). Initial run [40211567298](https://github.com/yash936936/AGM/actions/runs/40211567298) caught a lexical tokenization-regex bug, now corrected on the latest head. Follow-up exact-head CI [40211660005](https://github.com/yash936936/AGM/actions/runs/40211660005) is pending, including the Windows RSS assertion. User-run PR #15 smoke output used one synthetic case, had zero concurrent errors, and reported peak RSS as null; it is not a quality or capacity claim.

**Still blocked:** the 10-case suite is synthetic; no consented, de-identified held-out dataset was supplied, so real-history results remain NOT RUN. Independent security/privacy review remains NOT ESTABLISHED. Do not claim production readiness.

## 2026-10-25 — Benchmark runner merged; operation and load metrics extended

**Merged:** [PR #13](https://github.com/yash936936/AGM/pull/13) added paired flat-vs-graph evaluation. [PR #14](https://github.com/yash936936/AGM/pull/14) added operation-level timings and removed the input dataset filename from aggregate output.

**Current increment:** `work/benchmark-rss-concurrency` adds a best-effort cross-platform process peak RSS metric and opt-in concurrent retrieval load measurements (p50/p95/p99, throughput, errors, elapsed time). The report protocol advances to `paired_flat_vs_graph_v3`.

**Verification:** PR #14 exact-head GitHub Actions passed all six Linux/Windows Python 3.11–3.13 jobs in [run 40210191011](https://github.com/yash936936/AGM/actions/runs/40210191011). The current increment still requires its own exact-head CI.

**Still blocked:** No consented, de-identified held-out dataset was supplied, so real-history results remain NOT RUN. Independent security/privacy review remains NOT ESTABLISHED. A standalone keyword baseline remains NOT RUN. Do not claim production readiness.

## 2026-10-25 — Paired retrieval benchmark runner merged; operation metrics follow-up in progress

**PR:** [#13](https://github.com/yash936936/AGM/pull/13), merged. Follow-up branch: `work/benchmark-operation-metrics`.

**Change:** Added `eval/benchmark_runner.py` to compare flat and graph retrieval on the same labelled JSONL cases, reporting retrieval/end-to-end latency percentiles, recall/pass rates, abstention accuracy, forbidden-value leakage, cases/second and SQLite file size. Default output omits case IDs and raw memory content. The existing evaluator now captures retrieval-call latency and database file size.

**Verification:** User-reported local checks on the merged candidate: wheel build succeeded; package inspection passed (28 entries, 23 Python modules); full suite `208 passed, 1 warning`; repository hygiene passed (155 tracked paths); `git diff --check` passed; working tree clean. Follow-up changes on this branch still require exact-head CI.

**Still blocked:** No consented, de-identified held-out dataset was supplied, so real-history results remain NOT RUN. Independent security/privacy review remains NOT ESTABLISHED. Peak process RSS, concurrent-load throughput and a standalone keyword baseline are not yet measured. Do not claim production readiness.

## 2026-10-25 — M1 owner/session/connection increment in review

**PR:** [#11](https://github.com/yash936936/AGM/pull/11), branch `feat/m1-owner-sessions-connections`, draft; exact-head CI pending.

**Implemented in candidate:** one-time local owner-key bootstrap command; persistent tenant/project/writer-scoped session create/list/close endpoints; scoped REST connection registry; least-privilege memory scopes; loopback-only health diagnostics; Linux/Windows CI matrix for Python 3.11–3.13; built-wheel hygiene inspection; focused tests for bootstrap, sessions, registry scoping, endpoint validation and failed diagnostics.

**Revocation update:** Current main commit `bffa7ff652df55308004a867ab2a6dec9f1c24cb` passed run [40193212194](https://github.com/yash936936/AGM/actions/runs/40193212194): 193 passed on Python 3.11, 3.12 and 3.13. This resolves the previously recorded cutoff-revocation regression for that tested commit; retain the regression test as a release gate.

**Still blocked:** held-out real-history evaluation requires a consented, de-identified dataset and frozen protocol; independent security/privacy review requires an actual reviewer and signed findings. Do not claim production readiness. Windows and package checks are newly added to CI and remain pending until PR #11 jobs finish. Local tests were not run because this environment cannot resolve GitHub for cloning.

## 2026-10-25 — M1 local hub implementation increment

**Branch/PR:** `feat/m0-m1-completion`, [PR #10](https://github.com/yash936936/AGM/pull/10), draft.
**Implemented in this increment:** `src/agm/local_hub.py` supplies a project-scoped metadata timeline, deterministic read-only graph snapshot, and guarded Obsidian export. Focused tests are in `tests/test_local_hub.py`. D-030 records the design and its boundaries.
**Verification:** Local tests NOT RUN because GitHub DNS/network was unavailable to the execution environment. Actions run 40192632664 was triggered; check its final conclusion before considering the branch verified.
**Still open:** M1 owner authentication/bootstrap, session lifecycle, connection registry and real connection diagnostics. M0 full exact-head acceptance, cutoff-revocation regression verification, local Windows smoke/packaging checks, held-out real-history evaluation and independent security/privacy review. M0/M1 are not complete or production accepted.

## 2026-10-25 — fast-track audit and exact-head CI blocker

**Review branch:** `debug/revocation-replay-fasttrack-review`; public `main` was not changed by this review. Baseline main head: `fb732d2e49bc99205cd14964a9d0ba01163bfbb0`.

**ZIP disposition:** The ZIP is a partial plan/test overlay whose assumptions conflict with the current roadmap and decision log. It was not applied wholesale. The repo-aligned plan is `prompts/fasttrack_debug_plan_revised.md` on the review branch.

**Highest-priority issue:** Main's latest Actions run [40189884890](https://github.com/yash936936/AGM/actions/runs/40189884890) fails on Python 3.11, 3.12 and 3.13. The failing cutoff-revocation test shows an item reappearing after database reopen and `rebuild_views()`. All three jobs reported `1 failed, 189 passed, 1 warning`; hygiene and whitespace checks passed. This is still unresolved and is the first coding gate.

**Verification actually performed:** Reviewed current repository entry point, agent rules, roadmap, status, decisions, debug log, store implementation, acceptance test, and CI job output remotely. Created review branch and committed the revised plan plus this audit log. No local code/test execution was available here. Local Windows tests, smoke clients, evaluation, packaging, and final archive inspection are NOT RUN.

**Next:** Fix the revocation replay regression with the smallest contract-preserving change, then validate the retention implementation against D-028/D-029 and audit actual M0 gaps. Build M1 features only after a source/test inventory and scope decision.

## 2026-10-25 — M1 end-to-end mutation benchmark cases added; release gates remain open
**Branch:** work/m0-m1-completion. Public main remains unchanged.

**CI evidence for evaluator operation tests:** Run [40124787565](https://github.com/yash936936/AGM/actions/runs/40124787565), commit 20ea048a887ad9b31a36a7615ac12f841cdfea01: Python 3.11 `171 passed, 1 warning in 9.46s`; Python 3.12 `171 passed, 1 warning in 13.68s`; Python 3.13 `171 passed, 1 warning in 15.78s`. The latest code/test tree passed all three environments. The subsequent docs-only updates require a final branch-head CI run.

**M1 changes:** The evaluator now executes correction, hard delete, and writer revocation with actual MemoryStore methods, closes/reopens after operations, rebuilds views from the event log, then queries and scores expected/forbidden values and abstention. Negative tests cover missed expected values, forbidden-value leaks, incorrect abstention, malformed schema, duplicate cases, zero-tolerance sentinel requirements, tenant isolation, and end-to-end correction/delete/revocation.

**Still open:** The evaluator threshold values are operational defaults and must be reviewed and frozen before held-out use. The existing retention/decay path is read-only dry run; an explicit expiry/retention operation and acceptance policy is not delivered. Local Windows regression and required smoke clients, simulation, package inspection, and final tree hygiene are NOT RUN here. Real consented held-out evaluation is NOT RUN. Production security/privacy review is NOT ESTABLISHED. Do not ship a ZIP until implementation and target-environment checks are complete.


## 2026-10-25 — M0–M4 roadmap documented; branch-local verification recorded

**Roadmap:** [M0–M4 roadmap](M0_M4_ROADMAP.md) now defines goals, deliverables, acceptance conditions, status vocabulary, release gates and execution order for storage correctness, local-first hub, live multi-agent memory, teams and hosted deployment.

**Branch:** `work/m0-m1-completion`; `main` remains unchanged.

**User-reported local Windows/Git Bash evidence on commit `46d954c`:**
- `python -m pytest -q`: 182 passed, 1 deprecation warning.
- MCP smoke: 12/12 passed.
- REST smoke: 11/11 passed.
- `eval/stale_facts.py`: 7 scenarios, 0 mismatches.
- compileall, repository hygiene, `git diff --check`, and package creation completed.
- Synthetic active-memory simulation completed; results are diagnostic, not production-quality evidence.
- Synthetic real-history evaluator: one cross-session recall case passed. This is not held-out real-history acceptance.

**Retention:** `MemoryStore.expire_before` and `tests/test_m1_retention.py` are present. Coverage includes cutoff validation, pinned-memory policy, tenant/project scoping, revoked-writer payload scrubbing and replay/rebuild. Remaining review must verify the full mutation contract, atomic rollback/failure injection, idempotent repeat expiry, replay safety, and the declared audit/deletion guarantees. Do not mark M0 closed from test count alone.

**M0–M4 disposition:** M0 remains in progress pending retention-contract review and exact-head CI/package inspection. M1 is partial and must be audited against the owner login, agent connection/session, timeline, graph snapshot and Obsidian export requirements. M2, M3 and M4 are not accepted until their own integration and operational acceptance gates pass. Real-history acceptance remains NOT RUN because no eligible dataset is available; independent security/privacy review remains NOT ESTABLISHED.

**Next:** implement and test remaining M0 gaps, then update the acceptance matrix with evidence tied to the resulting candidate commit. Do not merge or claim production readiness while mandatory gates are open.

## 2026-10-25 — Revocation replay cutoff regression

**Original PR:** https://github.com/yash936936/AGM/pull/7 was merged despite failing acceptance CI. This is recorded as a process error; do not infer correctness from the merge.

**Failure evidence:** GitHub Actions run 40188540997 failed on Python 3.11, 3.12 and 3.13. The cutoff test found that a post-cutoff node reappeared after reopen/rebuild. The original replay-pass change did not resolve it.

**Corrective branch:** `fix/revocation-replay-corrective`, latest candidate commit `4001f746d62d70a0062f8a5ac9992d4003e47c00`. The candidate enforces stored tombstone IDs after replay and also re-derives matching source nodes from each revocation event's tenant, writer and `since` cutoff. This is a candidate fix, not yet validated.

**Validation:** NOT RUN at this candidate head. Required next: focused edge acceptance tests, full pytest suite, `git diff --check`, and CI on the exact branch head. Do not merge this corrective branch or claim the issue fixed until all pass.

**Release status:** Revocation replay correctness remains unresolved; production readiness is not established.

## 2026-10-25 — Retention orphan-scrub scope regression added

**Branch:** `work/benchmark-acceptance-baselines`.

**Change:** Added a regression that creates aged, revoked source events in the current project, another project in the same tenant, and another tenant. It asserts that expiry scrubs only the current tenant/project's orphan payloads and that replay does not reintroduce scrubbed content. This extends the existing retention scope, idempotency and rollback coverage.

**Validation:** The focused test and full suite have NOT been run in this environment. The new commit is `ee81976c701e90c633b577a09aa7f6a26d762e14`; no CI status was visible for that commit at the time of this update. Do not treat this test as passing until exact-head CI completes.

**Benchmark evidence update:** Follow-up exact-head CI run [40211660005](https://github.com/yash936936/AGM/actions/runs/40211660005) and latest docs-head run [40211734663](https://github.com/yash936936/AGM/actions/runs/40211734663) passed all six Linux/Windows Python 3.11–3.13 jobs. User-reported Windows benchmark evidence: full suite `213 passed, 1 warning`; peak RSS `60,682,240` bytes; five repetitions, four workers, 1,000 requests per mode per repetition, zero errors; median concurrent p95 126.4 ms flat / 132.3 ms graph, throughput 89.0 / 86.4 requests/s. On the 10-case synthetic suite, flat and graph each passed 100% with 100% expected-value recall and zero forbidden-value leaks; keyword baseline passed 90% and abstention accuracy was 90%. These are synthetic/user-reported measurements, not held-out real-history or production-capacity evidence.

**Still blocked:** held-out consented real-history evaluation is NOT RUN; independent security/privacy review is NOT ESTABLISHED. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY.

## 2026-10-25 — M1 local-hub acceptance tests expanded

**Change:** Added focused tests for timeline newest-first ordering and invalid-limit rejection, plus deterministic repeat export and YAML-frontmatter injection resistance for an adversarial project label containing quotes and a newline. The export test also checks secret redaction in the exported body.

**Validation:** Tests and full suite NOT RUN locally. Candidate commit `881512bc1da1a0d67874d3ed5427b3beff0f0fe9`; exact-head CI is not yet visible. Do not treat the new M1 tests as passing until CI executes on this head.

**M1 status:** PARTIAL / VERIFY. Existing coverage establishes scoped metadata timeline, deterministic scoped snapshot, secret-scrubbed Obsidian export and snapshot-copy semantics. Owner-auth bootstrap, session/connection API scope isolation, connection diagnostics token secrecy, and export deletion policy still require end-to-end acceptance review on an exact candidate. 


## 2026-10-25 — M1 local-hub CI assertion fixes

GitHub Actions run [40213071743](https://github.com/yash936936/AGM/actions/runs/40213071743) failed two newly added local-hub tests on Ubuntu Python 3.11–3.13: one referenced a nonexistent `WriteResult.event_id`; the other over-specified JSON string escaping in exported frontmatter. Both test assertions were corrected in commit `d8e8c7acff925d70d3167bb40f40b548bc3288e9`. The full suite was otherwise 214 passed in the Python 3.11 job. This fix is not accepted until exact-head CI passes across the Linux/Windows Python 3.11–3.13 matrix. M0 remains IN PROGRESS, M1 remains PARTIAL / VERIFY; real-history evaluation and independent security/privacy review remain open release gates.

## 2026-10-25 — Follow-up on remaining local-hub export failure

Run [40213224547](https://github.com/yash936936/AGM/actions/runs/40213224547) confirmed the timeline test fix and reported one remaining export-test failure: the fixture used literal backslash+n sequences, so the password label did not have the intended token boundary. The fixture now uses actual line breaks for both the note and adversarial project metadata (test commit `40ff30a5966b6e5539663ce9e25bd4c35f125765`). Exact-head CI must pass before accepting this change; M1 remains PARTIAL / VERIFY and M0 remains IN PROGRESS.

## 2026-10-25 — M1 session/connection scope acceptance expanded

The corrected export fixture candidate passed all six Linux/Windows Python 3.11–3.13 jobs in [CI run 40213472988](https://github.com/yash936936/AGM/actions/runs/40213472988), including hygiene, whitespace, tests and wheel inspection. Follow-on work adds project/writer isolation tests for sessions and connections and strict integer validation for session-list limits. Current implementation/test commits are `8eeca08ca33499217f6e1a3c582051576a6bd4e7` and `42e3e638d8f051893c5a70ae26daba833be2f8c0`; the subsequent documentation commits are not validation. Exact-head CI remains required. M1 stays PARTIAL / VERIFY; M0 stays IN PROGRESS.

## 2026-10-25 — REST authorization acceptance added

Session/connection scope changes passed all six Linux/Windows Python 3.11–3.13 jobs in [run 40214097156](https://github.com/yash936936/AGM/actions/runs/40214097156); PR #18 merged. New REST-level tests now cover session read/write permissions and admin-only connection management, including metadata-only connection listing (test commit `2085ba3b76652636152b3f4dccb627a426e7b123`). These new tests are not yet validated by exact-head CI. M0 remains IN PROGRESS and M1 remains PARTIAL / VERIFY; real-history and independent security/privacy gates remain open.

## 2026-10-25 — REST identity isolation coverage added

PR #19 passed all six Linux/Windows Python 3.11–3.13 jobs in [run 40214468957](https://github.com/yash936936/AGM/actions/runs/40214468957) and merged. Follow-up acceptance tests now exercise session/connection isolation across tenant, project and writer identities plus REST query validation for session-list limits. Test commit `613d96fcc453f6979eec16c9a68beb5e7d3c0f77`; exact-head CI is pending/not yet visible. M0 remains IN PROGRESS, M1 remains PARTIAL / VERIFY, and held-out real-history plus independent security/privacy review remain open.

## 2026-10-25 — REST identity-isolation candidate validated and merged

PR #20 passed exact-head CI [run 40214773052](https://github.com/yash936936/AGM/actions/runs/40214773052): all six Ubuntu/Windows Python 3.11–3.13 jobs passed tests, repository hygiene, whitespace checks and wheel/package inspection. Merged commit: `d4eff63b74c0ed37cdf52c1b71c7b951a26d4547`. This validates the added REST tests for tenant/project/writer isolation and invalid session-list limits on that candidate. M0 remains IN PROGRESS and M1 remains PARTIAL / VERIFY. Held-out consented real-history evaluation remains NOT RUN; independent security/privacy review remains NOT ESTABLISHED.
## 2026-10-25 — M1 timeline project-limit starvation regression

**Branch:** `fix/m1-timeline-project-limit`.

**Audit finding:** `timeline()` selected the newest N events for the entire tenant and only then filtered by project in Python. A high-volume sibling project could consume the limit and hide all events for the caller's project. This is a correctness/availability bug in the local-hub timeline, despite the existing scope checks.

**Change:** Move project scoping into the SQL predicate before LIMIT, retaining the legacy-event rule (events without project metadata are only visible to their originating writer for the default project). Added a regression with eight newer sibling-project events and `limit=1`.

**Validation:** Local tests NOT RUN in this environment. Exact-head GitHub Actions, full suite, package inspection, repository hygiene and whitespace checks are pending. Do not merge or treat M1 timeline acceptance as passed until these checks complete.

**Milestone disposition:** M0 IN PROGRESS; M1 PARTIAL / VERIFY; M2–M4 NOT ACCEPTED. Held-out real-history evaluation NOT RUN; independent security/privacy review NOT ESTABLISHED.
## 2026-10-25 — M0 retention policy regression for revoked pinned memories

**Branch:** `fix/retention-preserve-revoked-pins-v2`.

**Finding:** Revocation removes a writer's materialized nodes but leaves source payloads for audit. The orphan-event expiry loop could scrub an aged pinned memory's source payload under the default policy because it only checked pinned IDs from currently materialized nodes.

**Change:** Inspect the source event's stored item pin flag when scrubbing orphan events. Preserve pinned source payloads unless `include_pinned=True`; add a regression covering default expiry, rebuild/replay, and explicit opt-in.

**Validation:** Local tests NOT RUN here. Exact-head CI, full suite, package inspection, repository hygiene and whitespace checks are pending. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY. Real-history evaluation and independent security/privacy review remain open.


## 2026-10-26 — Synthetic benchmark JSON output merged; phase and release gates

PR #54 merged at `a93d3a8ca62dce336caf36367a6ee0e5744f0349`. Exact-head CI run [40303228204](https://github.com/yash936936/AGM/actions/runs/40303228204) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. The synthetic retrieval smoke benchmark now emits machine-readable JSON with runtime/platform/configuration metadata, quality metrics, retrieval-only p50/p95/p99, sequential throughput, error counts, and explicit caveats. See `docs/benchmarks/synthetic_retrieval_smoke.md`.

This is still a four-scenario synthetic smoke test using `hash-256-v1`; it is not a production benchmark, has no real-history data, and is not evidence for/against H1–H7. Local pytest was NOT RUN in the remote editing environment.

### Remaining M0 / M1 / M2 work

- **M0 — retention/replay:** the revoked-pinned-source regression and exact-head CI are merged/verified (PR #39). Remaining: conduct a focused review of the complete M0 acceptance matrix against current main, confirm all expiry/revocation/pinning/orphan-scrub and whole-sweep rollback cases are represented, and record any missing cases with exact-head CI evidence. The older status entries in this file are historical candidate notes; use merged PRs and current CI as the authority.
- **M1 — lifecycle and adapters:** core cross-session recall/correction/history/delete/rebuild and REST/MCP fresh-session smoke coverage are merged/verified (PR #40 and follow-up CI). Remaining: audit the current acceptance matrix end-to-end for scope isolation, bounded before-turn context/provenance, quarantine/snapshot/export privacy, and adapter contract coverage; run the Windows smoke clients in the target integrator environment if required and capture evidence. Repository CI is not a real-host integration test.
- **M2 — active-memory lifecycle:** implementation and guardrails are CI-verified through PRs #47, #49, #50, #51 and #52, but **M2 is NOT ACCEPTED**. Remaining code/product decision: decide whether proposal execution should stay library-only or receive a separately approved REST/MCP contract and corresponding parity tests. Current D-037 intentionally keeps it library-only.
- **External release gates (block production acceptance):** (1) held-out evaluation on explicitly consented, de-identified real-user histories; (2) independent security/privacy review and sign-off; (3) a recorded integration test against an actual independently maintained third-party host. All three remain OPEN / NOT RUN or NOT VERIFIED. Do not mark production-ready until evidence is reviewed.
- **Benchmarking:** synthetic JSON/text diagnostics are available; still needed for claims about retrieval quality/latency are controlled, repeated runs with pinned commit/environment and, for release acceptance, the held-out protocol's frozen baselines/thresholds, uncertainty reporting, end-to-end latency and privacy/lifecycle cases. No current synthetic result closes that gate.
