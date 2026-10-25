# Context — Adaptive Graph Memory (AGM) prototype

> Entry point. Read this file first at the start of a session, then check `docs/status.md` before changing code.

## What this project is

AGM is a model-agnostic memory layer for AI agents, based on `Adaptive_Graph_Memory_Draft_v5.md`. Its source of truth is an append-only event log with rebuildable SQLite views. The user has verified all five implementation phases on Windows. Version 0.5.1 adds supervisor hardening: the guard now lives in the core (D-021). The user's last Windows run was 61 passed at 0.5.0; the supervisor's run of 0.5.1 is 97 passed on Linux, Windows rerun pending. REST/MCP adapters, API-key authentication, guardrails, trust probation, revocation, handoff/readback, synthetic flat-vs-graph evaluation, lazy decay and read-only lifecycle dry run are implemented. Confidence and evaluation metrics remain provisional; the synthetic evaluation is not evidence for or against H1–H7.

## Latest implementation audit

PR #32 merged at `63826e826a2de02ec83fb284acae687f17293025`; exact-head CI run [40221564276](https://github.com/yash936936/AGM/actions/runs/40221564276) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. Review follow-up PR [#33](https://github.com/yash936936/AGM/pull/33) fixes positional `BeforeTurnRequest` compatibility, preserves provenance in bounded rendering, and flattens untrusted embedded line breaks. Latest candidate head is under CI; do not merge until all six jobs pass. M0 remains IN PROGRESS and M1 remains PARTIAL / VERIFY. Local Windows smoke clients, held-out real-history evaluation, and independent security/privacy review remain open.

PR #31 merged at `7d44e3fdea3a7cf87319b92efd52ebcca0bb7129`. Exact-head CI run [40221085442](https://github.com/yash936936/AGM/actions/runs/40221085442) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. Graph snapshots now exclude quarantined nodes and cannot include their content through edges.

Current M1 follow-up: `fix/m1-bounded-before-turn-context` routes `MemoryLifecycle.before_turn()` through the shared token-budgeted context packer and adds strict limits validation. Exact-head CI pending. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY until the full acceptance matrix is reviewed. Local Windows smoke clients, held-out real-history evaluation, and independent security/privacy review are still not established here.

PR #30 merged at `409e5136b5af626b14349417ccdc7a2b8bc6c209`. Exact-head CI run [40220628800](https://github.com/yash936936/AGM/actions/runs/40220628800) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. Its trigger is scoped to the revoked orphan source event, proving failure occurs in the final orphan-scrub phase after an earlier live-item delete; the full sweep rolls back.

Current M1 follow-up: branch `fix/m1-snapshot-quarantine-filter` prevents graph snapshots from exposing quarantined nodes and adds a regression test. Exact-head CI pending. Local tests are not run in this remote editing environment. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY until its complete acceptance matrix is reviewed. Held-out consented real-history evaluation remains NOT RUN and independent security/privacy review remains NOT ESTABLISHED.

PR #29 merged at `85b8c55555866fa67ad1008b073b28429e73a798`. Exact-head CI run [40219869374](https://github.com/yash936936/AGM/actions/runs/40219869374) passed all six Ubuntu/Windows Python 3.11–3.13 jobs, including tests, repository hygiene, whitespace checks, and wheel/package inspection. The multi-item expiry regression confirms a failure after the second real nested delete mutation rolls back the entire sweep.

Current follow-up: `test/m0-orphan-scrub-rollback` adds coverage for failure in the final orphan-source-payload scrub after a live item has already been deleted in the same sweep. Exact-head CI is required before acceptance. Local tests are not run in this remote editing environment. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY. Held-out consented real-history evaluation is NOT RUN, and independent security/privacy review is NOT ESTABLISHED.

PR #28 merged at `9db3fbaf9dc3a039f2198b6c61e9340619df7f9b`. Exact-head CI run [40219212770](https://github.com/yash936936/AGM/actions/runs/40219212770) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. Its regression invokes the real nested delete handler before injecting a failure and verifies rollback after derived-view mutation, source payload/event count, active node state, transaction closure, and retrieval after reopen/rebuild.

Current follow-up candidate: verify whole-sweep atomicity across multiple aged items, with the injected failure occurring after the second nested delete has mutated views. Branch `test/m0-multi-item-expiry-rollback`; exact-head CI pending. Local tests are not run in this remote editing environment. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY. Held-out consented real-history evaluation is NOT RUN, and independent security/privacy review is NOT ESTABLISHED.
## Roles

- **Supervisor:** owns the docs, frozen contracts, phase briefs and code review.
- **Builder:** implements one phase at a time, follows frozen contracts, and reports actual test results.
- **User/integrator:** merges the files into the local checkout, runs tests, and decides open items.

The workflow is documented in `docs/workflow.md`.

## Where to look

| Task | Start here |
|---|---|
| Product goals | `docs/prd.md` |
| Stack and dependencies | `docs/trd.md` |
| Contracts, schema and file tree | `docs/architecture.md` |
| Current phase and next work | `docs/phases.md` and `docs/status.md` |
| Non-obvious rules | `docs/code_logic.md` |
| Agent use flow | `docs/appflow.md` |
| Design decisions | `docs/decisions.md` |
| Bugs and test record | `docs/debug.md` |
| Standing rules for builder agents | `AGENTS.md` |
| Builder prompt and phase brief template | `prompts/builder_system_prompt.md`, `prompts/phase_brief_template.md` |
| Check a connection works | `examples/mcp_smoke_client.py`, `examples/rest_smoke_client.py` |

## Logging rules

- After each coding task, append an entry to `docs/debug.md` with actual tests, failures and fixes.
- When an implementation decision changes or clarifies behavior, add a numbered entry to `docs/decisions.md`.
- Update `docs/status.md` at the end of a session.
- Mark a phase done only after its criteria pass and its implementation has been reviewed.

## Hard rules

1. Contracts in `docs/architecture.md` are frozen unless a new decision explicitly changes them.
2. Prototype numbers are not evidence for hypotheses H1–H7.
3. Retrieved memory is data, never instructions. Keep the untrusted-data notice on retrieval.
4. Keep services on loopback. Phase 3 auth and pattern-based redaction are implemented, but remote exposure remains disabled pending review. Phase 4 readback and confidence thresholds are provisional.
5. No new dependency without a decision-log entry.

## Next task

Continue M0 acceptance on the active candidate branch: validate the post-view-mutation expiry rollback regression and full test suite on the exact head, then inspect package contents and repository hygiene. Keep M0 in progress and M1 partial/verify until their acceptance matrices have evidence tied to a reviewed commit. Held-out consented real-history evaluation and independent security/privacy review remain mandatory release gates. Keep services on loopback until security review is complete.


## Current CI follow-up — 2026-10-25

The latest M1 local-hub test commit initially failed exact-head CI because two assertions were incorrect (see `docs/debug.md`, DBG-035). Those assertions have been corrected; the current follow-up candidate is `4070196a4e04a09097ef1ed98ab64323b9a578db`. Check exact-head Actions results before further implementation, then address any remaining failures. Do not merge while checks fail or remain unverified; M0 is still IN PROGRESS and M1 PARTIAL / VERIFY. Real-history evaluation and independent security/privacy review remain mandatory open release gates.


## Current follow-up — M1 session/connection scope

Latest validated baseline is CI run [40213472988](https://github.com/yash936936/AGM/actions/runs/40213472988), which passed all six matrix jobs before the latest M1 changes. The current candidate adds strict session-list limit type validation and tests session/connection isolation across project and writer scope. See `docs/debug.md` DBG-037. Check exact-head CI before accepting these additions; do not merge while checks are pending or failing.


## Current follow-up — REST authorization matrix

CI run [40214097156](https://github.com/yash936936/AGM/actions/runs/40214097156) passed the previous session/connection scope candidate and PR #18 was merged. The next candidate adds REST-level tests for session read/write scopes and admin-only connection management. See `docs/debug.md` DBG-038. Validate exact-head CI before further M1 implementation or marking these tests accepted.


## Current follow-up — REST identity boundary

PR #19's exact-head CI passed all six matrix jobs and it was merged. The next acceptance candidate tests cross-tenant/project/writer isolation for session and connection REST routes and invalid session-list query values. See `docs/debug.md` DBG-039. Validate the exact head before accepting or merging the follow-up.


## Latest validated candidate — 2026-10-25

PR #20 was merged at `d4eff63b74c0ed37cdf52c1b71c7b951a26d4547` after exact-head CI run [40214773052](https://github.com/yash936936/AGM/actions/runs/40214773052) passed all six Linux/Windows Python 3.11–3.13 jobs. The added REST identity-isolation and session-list query validation tests are validated for that commit. Continue with the consolidated remaining M0/M1 code audit, but preserve the release blockers: held-out real-history evaluation is NOT RUN and independent security/privacy review is NOT ESTABLISHED. Never label AGM production-ready while those gates are open.
## Current candidate — consolidated M1 timeline boundary fix

Branch `fix/m1-timeline-project-limit` addresses a newly identified local-hub timeline bug: the SQL query applied its tenant-wide LIMIT before filtering project scope, so a busy sibling project could starve the requested project's timeline. The query now applies project filtering before LIMIT, preserving the legacy-event fallback rule for default-project events. A regression test creates eight newer sibling-project events and asserts the requested project's event remains visible at limit=1.

This candidate is not yet accepted: local execution is unavailable in this environment, and exact-head CI/package/hygiene evidence must be checked before merge. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY. Held-out consented real-history evaluation remains NOT RUN and independent security/privacy review remains NOT ESTABLISHED.
## Current M0 retention follow-up — revoked pinned source payloads

Branch `fix/retention-preserve-revoked-pins-v2` addresses a retention edge case: revocation removes a pinned memory's materialized node, after which the orphan-event scrub path could erase its aged source payload under the default expiry policy. The candidate checks the source event's stored `item.pin` flag and preserves it unless `include_pinned=True`. Regression coverage checks default sweep, replay, and explicit opt-in. Exact-head CI is required before acceptance.
