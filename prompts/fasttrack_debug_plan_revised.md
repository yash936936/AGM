# AGM fast-track plan (revised after repository review)

## Entry point and starting state
Start at context.md, then read AGENTS.md, docs/status.md, docs/architecture.md, docs/decisions.md, docs/debug.md, and docs/M0_M4_ROADMAP.md before changing code.

Repository: https://github.com/yash936936/AGM
Main head reviewed: fb732d2e49bc99205cd14964a9d0ba01163bfbb0
Baseline branch: main
Review branch: debug/revocation-replay-fasttrack-review
Source ZIP: fasttrack.zip

## Why the ZIP plan must change
The ZIP's m0_m1_fast_track.md describes an older/measured starting state and proposes a broad M0+M1 build, including temporal validation gaps and the whole owner-auth/session/connection/timeline/snapshot/export/UI feature set. It must not be applied as-is:
- Repository context.md says the next scoped task is evaluation-focused and treats Phase 6+ as already implemented.
- docs/M0_M4_ROADMAP.md and docs/status.md define M0 as still in progress, M1 as partial/verify, and require exact-head evidence.
- Current main has explicit retention decisions D-028/D-029 and active revocation replay acceptance work. Do not duplicate or contradict these decisions.
- The ZIP test_m0_open_gaps.py does not match the current checkout: current GitHub returns 404 for tests/test_m0_open_gaps.py on main. Do not add stale tests wholesale or preserve xfails without comparing with actual current behavior.
- Do not wholesale change version to 0.6.0 or add M1 features before reconciling the frozen contracts and current roadmap.

## Gate 0 — preserve scope, establish actual head
1. Run `git status --short --branch`, record HEAD SHA, and verify branch is `debug/revocation-replay-fasttrack-review`.
2. Confirm clean working tree; never overwrite user edits.
3. Read the exact current implementations of revoke_writer, event replay/rebuild, delete/scrub semantics, and the acceptance test.
4. Keep services loopback-only, no new dependencies, parameterized SQL, core guard, event-first writes, tenant filtering, and no stdout in library/MCP code.
5. Do not merge to main. No code changes before understanding the replay bug.

## Gate 1 — fix current release-blocking regression first
Observed in main CI run 40189884890 on Python 3.11, 3.12 and 3.13:
`tests/test_privacy_edge_acceptance.py::test_revocation_since_cutoff_preserves_older_memory_after_rebuild_and_reopen` fails.
At the current state the later node is absent immediately after `revoke_writer`, but it reappears after closing/reopening and calling `rebuild_views()`.
The job reports `1 failed, 189 passed, 1 warning`; hygiene and `git diff --check` pass. Do not describe this as fixed.

Investigate:
- the revoke event payload, tombstone IDs, writer/tenant scope, `since` cutoff semantics based on source event created_at, and replay order;
- interactions between source-event event IDs and revocation cutoff timestamps;
- whether the test's direct timestamp UPDATE is reflected in the event payload and whether the implementation is incorrectly using HLC/valid_from or current event metadata;
- whether final replay enforcement runs inside the same atomic transaction and across all view rebuild paths.

Implement the smallest correct fix preserving these contracts:
- revoke_writer with no cutoff purges all eligible memories for that tenant/writer;
- with since=cutoff only newer matching source events are removed and older data remains;
- tenant isolation is strict even if writer IDs match;
- results persist across close/open, rebuild, replay and repeated calls;
- event-first and delete-vs-revoke semantics stay intact; do not resurrect or scrub unrelated data.
Add a regression test if one is missing, but do not weaken the existing test.
After implementation, run the focused test, then the full suite, then git diff --check and repository hygiene. Never claim local Windows results from hosted Linux CI or vice versa.

## Gate 2 — audit retention/expiry M0 contract
D-028 and D-029 already define expire_before(ctx, cutoff, include_pinned=False), scoped to tenant/project and based on source event created_at, atomic across the sweep, skipping pinned items unless opted in, and scrubbing eligible orphan source payloads.
Review implementation against the decision and docs/M0_ACCEPTANCE_MATRIX.md. Test cutoff parsing, tenant/project isolation, pinned behavior, failure-injection rollback, idempotent repeat, replay/rebuild safety, and whether expiry can remove or retain source payloads contrary to contract.
Do not replace this operation with the ZIP's broader redesign. Log any new decision as the next free D-number; never edit old decisions.

## Gate 3 — classify and close genuine M0 gaps
Diff actual current code/tests against docs/M0_ACCEPTANCE_MATRIX.md and the frozen contracts. Do not assume the ZIP's test list is accurate. Add tests first for any genuine missing contract, then fix it. Particularly audit:
- late-arriving older facts and valid-time history;
- validation limits at core and REST boundaries;
- idempotency and same-instant conflicts;
- guard coverage on every persisted string/write path;
- delete, revocation, retention, replay/rebuild and failure rollback;
- cross-tenant object-ID substitution;
- repository hygiene and tracked binary/data artifacts.
For each gap record implementation, test path, actual command output, and status. Do not change public REST/MCP/model contracts without a numbered decision.

## Gate 4 — M1 gap inventory, not a one-pass feature dump
Compare actual src/ and tests/ with all six M1 items from docs/M0_M4_ROADMAP.md:
1. owner authentication/local identity;
2. agent connection registry and scoped tokens;
3. sessions and connection diagnostics;
4. timeline;
5. graph snapshot;
6. Obsidian export.
List each as IMPLEMENTED / PARTIAL / MISSING with file and test evidence. Build only the explicitly chosen M1 scope after the M0 blockers are closed and current architecture/decisions are reconciled.
The ZIP proposal for login cookie, CSRF, scrypt, connection token snippets, UI, and session hub_event schema is a future specification candidate, not approved implementation scope. If approved later, freeze contracts and add a design-decision entry first.

## Verification sequence
Run after each coherent package:
1. `python -m pytest -q tests/test_privacy_edge_acceptance.py`
2. `python -m pytest -q`
3. `python -m compileall -q src tests eval scripts examples`
4. repository hygiene script and `git diff --check`
5. `python examples/mcp_smoke_client.py`
6. `python examples/rest_smoke_client.py`
7. `python eval/stale_facts.py`
8. any required M0 acceptance/expiry tests and active-memory simulation
9. `python scripts/pack.py` and inspect archive contents for databases, secrets, caches, tracked logs, and accidental build output
10. Verify CI on the exact final commit in Python 3.11, 3.12, 3.13; explicitly inspect each result.

If a command cannot run in the available environment, record NOT RUN with its reason. Keep CI, local Linux/macOS, and local Windows evidence distinct. Do not fabricate timings, test counts, results, or logs.

## Required documentation at the end
Prepend new entries to docs/debug.md and docs/status.md. Add a docs/decisions.md entry only when a design choice is actually made; use the next free ID and preserve previous text. Update docs/M0_ACCEPTANCE_MATRIX.md with exact-head evidence, not optimistic status. Deliver a report named `AGM_DEBUG_FASTTRACK_REPORT.md` with:
- baseline and final commit SHAs;
- files changed and reason for every file;
- real command output or NOT RUN per command;
- test cases and invariants covered;
- CI run links and per-Python results;
- open bugs, contract concerns, decisions needing owner confirmation;
- deferred M1 work and external gates (real-history evaluation, security/privacy review);
- packaging/hygiene results.
No merge until every mandatory code gate passes. Do not claim production readiness; real-history evaluation and independent security/privacy review are separate gates.

## Deferred
Do not implement the full M1 owner/auth/session/connection/UI stack during the first repair pass. Do not add dependencies, hosted deployment, teams/workspaces, remote binding, broad refactors, or unrelated styling. Keep any unapproved expansion as a separately documented proposal.
