# M0/M1/M2 Acceptance Traceability Audit

**Audit date:** 2026-10-26  
**Scope:** Repository evidence and gaps; not a production certification.  
**Evidence rule:** A test file existing is not the same as a passing test run. For CI evidence, use the linked exact-head workflow runs. PR #56's added tests passed in exact-head workflow [40304904729](https://github.com/yash936936/AGM/actions/runs/40304904729), all six Ubuntu/Windows Python 3.11–3.13 jobs.

## M0 — Retention, deletion, replay

| Requirement | Existing evidence | Status / remaining work |
|---|---|---|
| Cross-session recall after close/reopen | [test_m0_history_acceptance.py](../../tests/test_m0_history_acceptance.py) | Repository regression exists; covered by the full suite in exact-head CI [40304904729](https://github.com/yash936936/AGM/actions/runs/40304904729). |
| Current-value correction and history retention | Same M0 acceptance file; [test_replay.py](../../tests/test_replay.py) | Repository regressions exist; current merged-head CI passed. |
| Hard deletion cannot resurface after rebuild/reopen | M0/M1 acceptance tests; [test_delete_ondisk.py](../../tests/test_delete_ondisk.py) | Repository regressions exist; keep on-disk/WAL and replay checks in the release gate. |
| Expiry, pinned-item policy, cutoff validation, idempotence | [test_m1_retention.py](../../tests/test_m1_retention.py) | Multiple regressions exist; full suite passed on PR #56's exact head. |
| Revoked source cleanup, pinned revoked sources, scoped orphan scrub | [test_m1_retention.py](../../tests/test_m1_retention.py), [test_privacy_edge_acceptance.py](../../tests/test_privacy_edge_acceptance.py) | Multiple regressions exist; external policy review still required. |
| Whole-sweep rollback after nested delete or orphan-scrub failure | Privacy-edge acceptance tests | Failure-injection regressions exist; exact-head CI passed. |
| Full acceptance matrix independently reviewed | No independent reviewer evidence in repository | **OPEN** — obtain reviewer sign-off; do not infer closure from test count. |

## M1 — Lifecycle, isolation, and adapters

| Requirement | Existing evidence | Status / remaining work |
|---|---|---|
| Fresh-session recall, correction/history, delete/rebuild | [test_m1_acceptance.py](../../tests/test_m1_acceptance.py), [test_m0_history_acceptance.py](../../tests/test_m0_history_acceptance.py) | Core lifecycle regression exists. |
| Tenant boundary on retrieval/deletion/revocation | M0 acceptance and privacy-edge tests | Core tenant cases exist. |
| Project boundary in active-memory context assembly | New [test_m2_acceptance_lifecycle.py](../../tests/test_m2_acceptance_lifecycle.py) | Added explicit same-tenant, cross-project context regression; passed in exact-head CI [40304904729](https://github.com/yash936936/AGM/actions/runs/40304904729). |
| REST and MCP fresh-session client behavior | [REST smoke client](../../examples/rest_smoke_client.py), [MCP smoke client](../../examples/mcp_smoke_client.py), .github/workflows/tests.yml | CI runs both smoke clients; they are not a third-party host test. |
| Bounded context, provenance, conflict handling, untrusted-data delimiters | [test_active_memory.py](../../tests/test_active_memory.py), [test_active_memory_turn.py](../../tests/test_active_memory_turn.py) | Library-level tests exist; external model/host behavior remains unverified. |
| Quarantine, export privacy, and adapter contract coverage across every path | Guard/privacy tests and REST/MCP tests | **PARTIAL** — requires explicit reviewer walk-through of all data surfaces and target environment. |

## M2 — Active memory before/during/after a turn

| Requirement | Existing evidence | Status / remaining work |
|---|---|---|
| Before-turn retrieval is bounded, read-only, scoped, and labels memory untrusted | test_active_memory.py, test_active_memory_turn.py | Core tests exist. New project-isolation regression added in this PR. |
| Proposal evaluation requires user-grounded evidence and explicit intent | test_active_memory_policy.py | Core policy cases exist. |
| Eligibility is not authorization; scopes and confirmation gate mutations | test_active_memory_turn.py, test_reference_host.py | Core authorization tests exist; the reference host is only a harness. |
| Correct, then delete; replay/reopen preserves correction history and prevents deleted content resurfacing | New test_m2_acceptance_lifecycle.py | Added end-to-end library executor regression; passed in exact-head CI [40304904729](https://github.com/yash936936/AGM/actions/runs/40304904729). |
| REST/MCP proposal-executor parity | D-037 intentionally keeps proposal execution library-only | **OUT OF SCOPE BY DECISION** unless a numbered decision changes the frozen contract. Existing REST/MCP smoke does not prove parity. |
| Full M2 acceptance and release sign-off | External evaluation/review absent | **NOT ACCEPTED**. |

## Benchmark status

The synthetic smoke supports text/JSON output and a configurable unrelated archive size (--archive-size) for size-sensitivity sweeps. Its four hand-authored scenarios, weak hash embedder, sequential retrieval-only timing, and lack of concurrency/end-to-end latency mean it remains a diagnostic—not a production benchmark. It does not close H1–H7 or the held-out evaluation gate.

Examples:

```bash
python eval/stale_facts.py --archive-size 0 --repeats 25 --format json
python eval/stale_facts.py --archive-size 1000 --repeats 25 --format json
```

For a credible comparison, pin the commit, environment and dependencies; run repeated sizes under controlled load; preserve raw aggregate output; and report variance/confidence intervals. This simple size sweep does not itself provide those controls or confidence intervals.

## External release gates — all remain open

1. **Held-out consented real-history evaluation:** NOT RUN. Follow [the protocol](real_history_evaluation_protocol.md); consent, de-identification, approvals, frozen labels/thresholds and independent review are prerequisites.
2. **Independent security/privacy review:** NOT PERFORMED. Use [the checklist](security_privacy_review_checklist.md) and record reviewer findings/sign-off.
3. **Real third-party host integration:** NOT VERIFIED. Follow [the host validation protocol](third_party_host_validation.md); the reference host harness is not an independently maintained host.

These require people, approved data, or an external host and cannot be honestly completed by repository edits alone. No synthetic fixture, local test, or green CI matrix closes them.