# M0/M1 completion work — evidence report

## Scope and current branch

This report describes changes on `work/m0-m1-completion`. Public `main` was not modified by this work. The branch is nine commits ahead of main at the time this report was drafted; see the branch comparison and CI run links below.

## Changes in this branch

- Updated M0 acceptance addendum to record exact public CI run evidence and keep separate gates explicit.
- Hardened `scripts/evaluate_real_history.py` with validated scenario labels, fixture validation, configured threshold reporting, scenario coverage and zero-tolerance leak handling for tenant-isolation, deletion and revocation scenario classes.
- Expanded `tests/test_real_history_eval.py` with negative evaluator cases for missed expected values, forbidden-value leaks, incorrect abstention, malformed JSONL, duplicate case IDs, missing forbidden sentinels in zero-tolerance cases, and tenant isolation.
- Updated `docs/M1_KICKOFF.md`, `docs/debug.md`, `docs/status.md`, and `PHASE9_REPORT.md` to accurately report scope, evidence and remaining gates.

## CI evidence

Latest branch run: [GitHub Actions run 40124507744](https://github.com/yash936936/AGM/actions/runs/40124507744), commit `187998b20a4cd7b0d6728e0075af9750602a9fe4`.

- Python 3.11: `168 passed, 1 warning in 12.81s`
- Python 3.12: `168 passed, 1 warning in 8.08s`
- Python 3.13: `168 passed, 1 warning in 14.53s`

All three jobs also passed the configured repository hygiene and `git diff --check` steps. The warning is the Starlette/httpx TestClient deprecation.

Earlier baseline run [40118798582](https://github.com/yash936936/AGM/actions/runs/40118798582), commit `f150a1996bda6292fae295c65ce14d9faf17a06b`, reported 153 passing tests on each Python version before the branch-specific M1 evaluator tests.

## What the current benchmark does and does not prove

The evaluator writes seeded memory fixtures, closes and reopens SQLite, then scores retrieved values and abstention. Scenario labels categorize cases; they do not execute deletion or writer revocation operations. The M0 acceptance unit tests separately exercise persistence, correction/history, tenant isolation, hard-delete scrub, replay, revocation, guard behavior and atomic mutation failure paths. M1 still needs end-to-end lifecycle scenarios that perform correction/delete/revoke and then query after restart/replay.

The default evaluator thresholds (case pass rate, expected-value recall and abstention accuracy) are conservative operational defaults, not thresholds validated against real users. They must be reviewed and frozen before evaluating held-out data. A one-case synthetic smoke benchmark must not be described as real-history evidence.

## Required regression commands on the local Windows checkout

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

Inspect the created archives and verify that no database, WAL/SHM file, credentials, `.env`, `.venv`, cache, or `.egg-info` artifact is included. The MCP smoke client must actually run rather than be skipped. Preserve the complete output and record any failures in `docs/debug.md` before considering M0/M1 complete. These commands were **NOT RUN in the current GitHub-connector execution environment**.

## Release blockers that remain

- Local Windows full regression and both smoke clients are not yet verified on the final branch.
- The M1 acceptance suite needs end-to-end mutation cases for correction, deletion and revocation across close/reopen/replay.
- Retention/expiry behavior needs an explicit implemented policy and test; the existing decay lifecycle is a read-only dry run.
- No consented, de-identified held-out real-history dataset was supplied; real-history evaluation is NOT RUN.
- Production security/privacy review is NOT ESTABLISHED.
- No ZIP should be delivered until the remaining implementation and target-environment regression checks have passed.

## Contract concerns and assumptions

- Frozen model, REST, MCP, and CLI contracts were not intentionally changed.
- No new dependency was added.
- Writer revocation remains an auditable rollback retaining source events; hard delete remains the scrubbing path.
- Default benchmark thresholds are provisional, not empirical production thresholds.
