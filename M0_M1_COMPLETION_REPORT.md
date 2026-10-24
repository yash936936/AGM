# M0/M1 completion work — evidence report

## Scope and branch

This work is on `work/m0-m1-completion`; public `main` has not been modified. This report separates code/CI evidence from checks that require the user's local Windows checkout and from real-history/security acceptance.

## Implemented in this branch

- M0 acceptance addendum records CI evidence for the exact baseline commit and keeps real-history and security/privacy review as separate gates.
- `scripts/evaluate_real_history.py` validates JSONL schema, case IDs, contexts, scenarios and operations; reports configurable case-pass, expected-value recall and abstention thresholds; emits scenario coverage and aggregate-only metrics; and blocks on forbidden-value leaks.
- Benchmark cases can run actual `MemoryStore.supersede`, `MemoryStore.delete`, and `MemoryStore.revoke_writer` operations. The evaluator closes/reopens SQLite around operations, rebuilds views from the event log, and then queries for current, stale, and forbidden values.
- The schema now requires a correction operation for `current_vs_stale`, a delete operation for `deletion`, and a writer-revocation operation for `revocation`. This prevents a scenario label alone from claiming mutation coverage.
- Tests cover expected-value misses, forbidden-value leaks, wrong abstention, malformed JSONL, duplicate IDs, missing sentinels, tenant isolation, correction across replay, deletion across rebuild, revocation across rebuild, and mismatched scenario/operation combinations.
- M0/M1 status, kickoff, debug, Phase 9 and completion documentation were updated to distinguish passing CI from open release gates.

## Latest CI evidence for evaluator hardening

[GitHub Actions run 40124931082](https://github.com/yash936936/AGM/actions/runs/40124931082), commit `5122f24f1bcc7bd40ec7607f6d28bdeb28e2bffa):

- Python 3.11: `174 passed, 1 warning in 12.12s`
- Python 3.12: `174 passed, 1 warning in 13.19s`
- Python 3.13: `174 passed, 1 warning in 14.96s`

All three jobs passed the configured repository-hygiene and `git diff --check` steps. The warning is the Starlette/httpx TestClient deprecation. This run predates the next documentation-only report refresh; check CI on the final branch head before treating the branch snapshot as verified.

Earlier baseline run [40118798582](https://github.com/yash936936/AGM/actions/runs/40118798582), commit `f150a1996bda6292fae295c65ce14d9faf17a06b`, reported 153 passing tests on each Python version before the branch-specific M1 evaluator tests.

## What this does not prove

- Synthetic fixtures validate code paths; they are not real-history evidence.
- The default 0.95 thresholds are provisional operational defaults, not empirical production targets. Review and preregister them before running a held-out benchmark.
- The evaluator covers correction/delete/revoke operations but does not replace separate store-level checks for authorization, transaction atomicity, physical deletion boundaries, retention, backups, or incident response.
- The existing decay/lifecycle CLI is a read-only dry run. An explicit expiry/retention mutation policy and acceptance test remain open.
- No consented, de-identified held-out real-history dataset was supplied; real-history evaluation is NOT RUN.
- Production security/privacy review is NOT ESTABLISHED.

## Required local Windows verification

From the repository root in the activated project virtual environment, run:

```bash
python -m pip install -e ".[dev]"
python -m compileall -q src tests eval scripts examples
python -m pytest -q
python examples/mcp_smoke_client.py
python examples/rest_smoke_client.py
python eval/stale_facts.py
python eval/active_memory_simulation.py
python scripts/check_repo_hygiene.py
git diff --check
python scripts/pack.py
git status --short
```

Inspect both archives and verify that no database, WAL/SHM file, credentials, `.env`, `.venv`, cache, or `.egg-info` artifact is included. Confirm the MCP smoke client actually runs rather than being skipped. Preserve output and record failures in `docs/debug.md`. These commands were NOT RUN in the GitHub-connector execution environment.

## Release decision

Do not mark M0/M1 production acceptance complete or ship a ZIP until final branch-head CI passes, local Windows regression/smoke/simulation/packaging checks pass, expiry/retention policy is explicitly implemented and tested, held-out real-history evaluation passes preregistered criteria, and security/privacy review is documented.
