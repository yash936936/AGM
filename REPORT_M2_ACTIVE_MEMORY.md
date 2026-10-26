# M2 Implementation Report — Active-turn orchestration

**Status:** IMPLEMENTATION VERIFIED BY REPOSITORY CI; M2 NOT ACCEPTED  
**Updated:** 2026-10-26

## Implemented in the current candidate

- `begin_active_memory_turn()` delegates to the existing bounded, scoped, read-only context preparation.
- `review_active_memory_proposals()` evaluates proposals against the current user message and returns eligibility/rejection reasons. Eligibility is not authorization.
- `execute_authorized_memory_proposal()` is the explicit execution seam. It re-evaluates policy, checks the required scope, requires host authorization, requires confirmation for mutations, and delegates to existing `MemoryStore` methods for write, correction, history, and deletion.
- Tests cover authorization/scope/confirmation denial, the write/correction/history/delete lifecycle, rebuild/reopen, source-payload scrubbing, and cross-tenant isolation.
- No new dependency or REST/MCP public contract change is intended.

## Validation evidence

- PR #47 merged at `4641796ef1a7ac6b3dfbac6abb33e04c63fb2f70`; exact-head run [40229139385](https://github.com/yash936936/AGM/actions/runs/40229139385) passed all six Ubuntu/Windows Python 3.11–3.13 jobs.
- PR #49 reference-host harness merged at `5fffbb23d0591a48f0bbd82472cbc0c4f3cd52ba`; exact-head run [40298108786](https://github.com/yash936936/AGM/actions/runs/40298108786) passed all six jobs.
- PR #50 policy/executor target alignment merged at `cd1f5d43bb155041129e100c1737d5c5360a7fb0`; exact-head run [40299531993](https://github.com/yash936936/AGM/actions/runs/40299531993) passed all six Ubuntu/Windows Python 3.11–3.13 jobs.
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
- [x] Policy/executor target contract alignment: history requires an entity and delete requires an exact target ID; PR #50 exact-head CI passes.
- [x] Reference-host trust boundary reviewed as a harness: host callbacks must resolve trusted identity/scopes and confirmation.
- [ ] Independent code/security review and end-to-end integration in a real third-party host.

## Review findings closed in repository code

The review-discovered mismatch is fixed in merged PR #50: history proposals without an entity and delete proposals without an exact target memory ID are rejected by policy before execution. Regression tests cover both cases. Exact-head run [40299531993](https://github.com/yash936936/AGM/actions/runs/40299531993) completed successfully on all six Ubuntu/Windows Python 3.11–3.13 jobs. This is repository-level validation, not independent security sign-off or proof of third-party-host interoperability.

## Limitations and release gates

The authorization boolean and scopes are supplied by the calling host; this function is not itself an authentication boundary. Integrations must pass trusted authorization results and the caller's actual scoped `Ctx`. No LLM calls or background writes are introduced.

Held-out consented real-history evaluation, independent security/privacy review, and real third-party host integration remain **OPEN / PENDING**. This candidate is not production-ready and M2 is not accepted. The library-only executor boundary is intentional under D-037; REST/MCP smoke tests do not establish executor parity. M2 implementation behavior has passing repository CI, but independent security review and a real third-party host run remain required. Held-out consented real-history evaluation, independent security/privacy review, and real third-party host integration remain OPEN / PENDING.
