## 2026-10-26 — Reference host harness merged; policy alignment follow-up

PR #49 merged at `5fffbb23d0591a48f0bbd82472cbc0c4f3cd52ba`; exact-head run [40298108786](https://github.com/yash936936/AGM/actions/runs/40298108786) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. The harness does not close the real third-party-host gate. Follow-up branch `m2/policy-executor-contract-alignment` makes history proposals require an entity and deletion proposals require an exact target memory ID, matching executor requirements. Local pytest NOT RUN here; follow-up CI pending. M2 and external release gates remain unaccepted.

## 2026-10-26 — Reference host integration harness candidate

Added `src/agm/reference_host.py` plus `tests/test_reference_host.py` as a dependency-free host wiring example for trusted identity-to-`Ctx`/scope mapping, proposal review, host-verified mutation confirmation, and explicit execution. Report: `REPORT_M2_REFERENCE_HOST.md`. Local pytest NOT RUN here; exact-head CI pending. This harness does not itself close the real third-party-host gate. Real-history evaluation and independent security/privacy review remain open.

## 2026-10-26 — M2 guardrail tests validated; executor surface boundary recorded

PR #47 merged at `4641796ef1a7ac6b3dfbac6abb33e04c63fb2f70`. Exact-head CI run [40229139385](https://github.com/yash936936/AGM/actions/runs/40229139385) passed all six Ubuntu/Windows Python 3.11–3.13 jobs, including full pytest, REST/MCP smoke clients, hygiene, whitespace, and package inspection. The added tests cover action-specific scopes, history reads without mutation confirmation, and re-evaluation of proposal evidence against the current user message.

D-037 now records that `execute_authorized_memory_proposal()` is intentionally library-only for this iteration. REST/MCP remain on frozen direct-store contracts; their smoke tests do not establish parity for the proposal-policy/confirmation path. See `REPORT_M2_ACTIVE_MEMORY.md`. M2 remains an implementation candidate, not accepted. Held-out consented real-history evaluation, independent security/privacy review, and third-party host integration remain OPEN / PENDING.

---

## 2026-10-26 — M2 kickoff: active memory behavior

M0/M1 repository acceptance changes are merged and their cited CI runs passed. The three external release gates are **OPEN / PENDING**: held-out consented real-history evaluation, independent security/privacy review, and real third-party host integration. Do not treat pending evidence as passed.

M2 starts with the active-memory lifecycle: prepare relevant profile/preferences, active goals, and query context before answering; evaluate any proposed write/correction/history/delete against the current user message during the turn; and keep execution of mutations behind explicit user intent, confirmation where needed, and existing scoped store APIs. Retrieved memory remains untrusted data. No automatic LLM execution or background mutation is in scope for the kickoff.

Brief: `docs/acceptance/m2_active_memory_execution_brief.md`. First implementation target is a tested orchestration seam around the existing `active_memory.py` and `active_memory_policy.py`, without changing frozen REST/MCP contracts or adding dependencies. This is a kickoff, not a claim that M2 is complete.

## 2026-10-26 — M0/M1 acceptance PRs merged

PR #39 merged at `ff74460daf3c6585c5820e380320cb8cfc134475`. Its exact-head CI run [40224653021](https://github.com/yash936936/AGM/actions/runs/40224653021) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. It adds coverage for revoked pinned source retention across default expiry and replay, plus explicit expiry scrubbing while retaining the revocation audit event.

PR #40 merged at `d27c6475d51263df6b75a0309438530b352665d6`. Its exact-head CI run [40224688462](https://github.com/yash936936/AGM/actions/runs/40224688462) passed all six Ubuntu/Windows Python 3.11–3.13 jobs, including the full pytest suite, REST integration smoke client, MCP fresh-session smoke client, hygiene, whitespace, and package inspection. It adds cross-session recall/correction/delete/rebuild coverage and makes REST/MCP smoke clients part of CI.

**Status:** The named M0 retention/replay regression and repository CI acceptance are verified. M1 core cross-session lifecycle and adapter smoke coverage are verified by CI. Do not claim the entire production release gate is closed: held-out, consented real-history evaluation and independent security/privacy review remain incomplete. A real external host smoke test is also distinct from the repository smoke clients.



## 2026-10-26 — M0/M1 closure PRs prepared

M0 candidate branch `acceptance/m0-retention-replay-closure` adds a regression proving that a revoked pinned source payload survives default retention and replay, and is scrubbed only when `include_pinned=True`. Exact-head CI is pending; do not mark M0 closed until the complete acceptance suite passes and evidence is reviewed.

M1 candidate branch `acceptance/m1-cross-session-lifecycle-closure` adds a fresh-store/rebuild regression for cross-session recall, correction history, hard deletion, and no resurfacing after replay. Exact-head CI is pending. Local Windows smoke-client execution, held-out consented real-history evaluation, and independent security/privacy review cannot be claimed from repository CI and remain open release gates.
# Context — Adaptive Graph Memory (AGM) prototype

> Entry point. Read this file first at the start of a session, then check `docs/status.md` before changing code.

## What this project is

AGM is a model-agnostic memory layer for AI agents, based on `Adaptive_Graph_Memory_Draft_v5.md`. Its source of truth is an append-only event log with rebuildable SQLite views. The user has verified all five implementation phases on Windows. Version 0.5.1 adds supervisor hardening: the guard now lives in the core (D-021). The user's last Windows run was 61 passed at 0.5.0; the supervisor's run of 0.5.1 is 97 passed on Linux, Windows rerun pending. REST/MCP adapters, API-key authentication, guardrails, trust probation, revocation, handoff/readback, synthetic flat-vs-graph evaluation, lazy decay and read-only lifecycle dry run are implemented. Confidence and evaluation metrics remain provisional; the synthetic evaluation is not evidence for or against H1–H7.

## Latest implementation audit

PR #37 merged at `f19aa818a00dc9995077721fc108c08d295362a7`. Exact-head CI run [40223870098](https://github.com/yash936936/AGM/actions/runs/40223870098) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. Obsidian exports now retain source episode IDs and source-span start/end coordinates in frontmatter.

PR #34 merged at `1c546392267cdd86a97b76e4979fae26cb141033`; exact-head CI run [40223512300](https://github.com/yash936936/AGM/actions/runs/40223512300) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. Lifecycle context now preserves positional `BeforeTurnRequest` compatibility and provenance, and escapes untrusted delimiters.


M1 audit found that Obsidian export omitted `source_episode`, `span_start`, and `span_end` from its node query and frontmatter, despite the roadmap requiring provenance. Branch `fix/m1-obsidian-export-provenance-v2` adds these fields and a regression test on current main. Exact-head CI pending; M1 remains PARTIAL / VERIFY.


PR #32 merged at `63826e826a2de02ec83fb284acae687f17293025`; exact-head CI run [40221564276](https://github.com/yash936936/AGM/actions/runs/40221564276) passed all six Ubuntu/Windows Python 3.11–3.13 jobs. Post-merge review identified three lifecycle context issues (positional compatibility, provenance preservation, and untrusted delimiter escaping); branch `fix/m1-lifecycle-context-review-findings` addresses them with regression tests. Initial run [40222469817](https://github.com/yash936936/AGM/actions/runs/40222469817) exposed two test-fixture issues: the bounded-context budget was too small after provenance was restored, and the delimiter test used literal backslash-n text. Both fixtures have been corrected. Latest-head run [40222677766](https://github.com/yash936936/AGM/actions/runs/40222677766) is queued. M0 remains IN PROGRESS; M1 remains PARTIAL / VERIFY.

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
