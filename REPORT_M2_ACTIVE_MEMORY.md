# M2 Implementation Report — Active-turn orchestration

**Status:** IMPLEMENTATION CANDIDATE / NOT ACCEPTED — targeted follow-up in progress  
**Updated:** 2026-10-26

## Implemented in the current candidate

- `begin_active_memory_turn()` delegates to the existing bounded, scoped, read-only context preparation.
- `review_active_memory_proposals()` evaluates proposals against the current user message and returns eligibility/rejection reasons. Eligibility is not authorization.
- `execute_authorized_memory_proposal()` is the explicit execution seam. It re-evaluates policy, checks the required scope, requires host authorization, requires confirmation for mutations, and delegates to existing `MemoryStore` methods for write, correction, history, and deletion.
- Tests cover authorization/scope/confirmation denial, the write/correction/history/delete lifecycle, rebuild/reopen, source-payload scrubbing, and cross-tenant isolation.
- No new dependency or REST/MCP public contract change is intended.

## Validation evidence

- Current candidate commit `d1717bf5e33442c0937a90ab09ae1fe95350f3ac`: GitHub Actions run [40228560284](https://github.com/yash936936/AGM/actions/runs/40228560284) completed successfully across all six Ubuntu/Windows Python 3.11–3.13 jobs.
- Follow-up guardrail tests merged in PR #47 at `4641796ef1a7ac6b3dfbac6abb33e04c63fb2f70`. Exact-head CI run [40229139385](https://github.com/yash936936/AGM/actions/runs/40229139385) passed all six Ubuntu/Windows Python 3.11–3.13 jobs, including tests, REST/MCP smoke clients, hygiene, whitespace, and package inspection.
- The successful run included the full test suite, repository hygiene, patch whitespace, REST integration smoke client, MCP fresh-session smoke client, and wheel/package inspection.
- Local focused pytest was not run because cloning the repository failed due to unavailable GitHub DNS/network access in that environment. CI is the available test evidence.
- Decision D-037 explicitly defines the new proposal executor as **library-only** for this iteration. REST and MCP retain their frozen direct-store contracts; their passing smoke tests do not prove parity for proposal policy, host confirmation, or the new executor. Exposing the executor through either adapter requires a separate contract decision and cross-surface tests.

## Acceptance checklist

- [x] Read-only before-turn context preparation.
- [x] Proposal policy review is separate from authorization.
- [x] Explicit host authorization and scope checks before execution.
- [x] Explicit confirmation for mutations.
- [x] Tests authored for write/correction/history/delete and rebuild/reopen.
- [x] Test authored for cross-tenant isolation.
- [x] Current-head full test suite and six-job CI matrix pass.
- [x] Current-head REST/MCP smoke clients, hygiene, whitespace, and package inspection pass.
- [x] Library-only boundary is formally documented in D-037; REST/MCP proposal-execution parity is intentionally not claimed.
- [x] Reference-host code review confirms the intended trust boundary is explicit: resolver and confirmation verifier are host-provided trusted callbacks, not an authentication system.
- [ ] Follow-up policy/executor target contract alignment passes exact-head CI and review.

## Follow-up found during review

The reference-host CI run passed, but code review found a policy/executor mismatch: policy review previously marked entity-only delete proposals eligible even though execution requires an exact memory ID, and history proposals could be eligible without the entity required by the executor. Branch `m2/policy-executor-contract-alignment` changes policy validation and regressions so these proposals are rejected before authorization/execution. This follow-up has not yet passed exact-head CI.

## Limitations and release gates

The authorization boolean and scopes are supplied by the calling host; this function is not itself an authentication boundary. Integrations must pass trusted authorization results and the caller's actual scoped `Ctx`. No LLM calls or background writes are introduced.

Held-out consented real-history evaluation, independent security/privacy review, and real third-party host integration remain **OPEN / PENDING**. This candidate is not production-ready and M2 is not accepted until the remaining review, parity decision, and external gates are addressed.
