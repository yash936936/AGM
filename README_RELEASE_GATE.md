# AGM M0 release-gate follow-up overlay

This overlay adds local repository-hygiene tooling and synthetic durable-memory acceptance tests. It does not replace AGM source files, create branches, or create PRs.

## Apply

Extract into the root of the existing AGM repository, merging `scripts/`, `tests/`, and `docs/`. Back up files first. The CI workflow already included in the prior M0 overlay should remain at `.github/workflows/tests.yml`.

## Run

```bash
python -m pytest -v tests/test_m0_history_acceptance.py
python -m pytest -q
python scripts/check_repo_hygiene.py
git diff --check
```

The hygiene scan requires Git and must run from inside the repository. Review any finding locally; the script does not print matching secret values. It is heuristic and is not a substitute for secret scanning/history review.

## Remote CI

Push the applied changes through your normal workflow. In GitHub Actions, record the successful Python 3.11, 3.12, and 3.13 jobs against the same commit SHA. The included/previous workflow cannot be declared green until GitHub actually runs it.

## Real user histories

See `docs/REAL_HISTORY_ACCEPTANCE.md`. The tests added here are synthetic acceptance tests, not a real-user benchmark. Do not commit raw histories or personal data. A consented, de-identified held-out dataset and a preregistered scoring protocol are required before making a production-readiness claim.
