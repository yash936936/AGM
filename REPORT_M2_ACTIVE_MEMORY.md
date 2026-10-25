# M2 Implementation Report — Active-turn orchestration

**Status:** IMPLEMENTATION CANDIDATE / NOT ACCEPTED  
**Updated:** 2026-10-26

## Implemented in the current candidate

- `begin_active_memory_turn()` delegates to the existing bounded, scoped, read-only context preparation.
- `review_active_memory_proposals()` evaluates proposals against the current user message and returns eligibility/rejection reasons. Eligibility is not authorization.
- `execute_authorized_memory_proposal()` is the explicit execution seam. It re-evaluates policy, checks the required scope, requires host authorization, requires confirmation for mutations, and delegates to existing `MemoryStore` methods for write, correction, history, and deletion.
- Tests now cover authorization/scope/confirmation denial, the write/correction/history/delete lifecycle, replay/reopen, source-payload scrubbing, and cross-tenant isolation.
- No new dependency or REST/MCP public contract change is intended.

## Validation evidence

- Prior candidate commit `5dcf7d86818f9a4c3bd9a7c8350235934ac92340`: GitHub Actions run [40227572306](https://github.com/yash936936/AGM/actions/runs/40227572306) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. This run predates the authorized-execution and lifecycle-test changes and is **not** validation of the current head.
- Current candidate commit: `f0f2913874b3319894e64e642bc513b83f59493a`.
- Local focused pytest: NOT RUN. Attempted repository clone for local execution, but network DNS resolution for GitHub failed in this environment.
- Current-head focused/full pytest, REST smoke, MCP smoke, hygiene, whitespace, package inspection: PENDING exact-head CI evidence.
- Library/REST/MCP parity for the newly added execution seam: NOT VERIFIED. The new seam is a library API; existing adapter contracts are unchanged, but adapter execution-path parity has not been demonstrated.

## Acceptance checklist

- [x] Read-only before-turn context preparation.
- [x] Proposal policy review is separate from authorization.
- [x] Explicit host authorization and scope checks before execution.
- [x] Explicit confirmation for mutations.
- [x] Tests authored for write/correction/history/delete and replay/reopen.
- [x] Test authored for cross-tenant isolation.
- [ ] Current-head focused and full test suites pass.
- [ ] Current-head six-job CI matrix passes.
- [ ] Current-head REST/MCP smoke clients and hygiene/package checks pass.
- [ ] Library/REST/MCP execution parity is tested or documented as intentionally library-only.
- [ ] Code review accepts the authorization contract and test evidence.

## Limitations and release gates

The authorization boolean and scopes are supplied by the calling host; this function is not itself an authentication boundary. Integrations must pass trusted authorization results and the caller's actual scoped `Ctx`. No LLM calls or background writes are introduced.

Held-out consented real-history evaluation, independent security/privacy review, and real third-party host integration remain **OPEN / PENDING**. This candidate is not production-ready and M2 is not accepted until current-head validation and review are complete.
