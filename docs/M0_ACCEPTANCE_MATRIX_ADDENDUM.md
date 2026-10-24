# M0 release-gate addendum

Update this table only with evidence tied to the target commit. The public CI evidence below is for the M0 baseline commit and does not verify later local M1 commits.

| Gate | Evidence | Status |
|---|---|---|
| Public CI Python 3.11 | [Run 40118798582](https://github.com/yash936936/AGM/actions/runs/40118798582), commit `f150a1996bda6292fae295c65ce14d9faf17a06b`; log: `153 passed, 1 warning in 10.99s` | Passed for that commit |
| Public CI Python 3.12 | Same run and commit; log: `153 passed, 1 warning in 14.02s` | Passed for that commit |
| Public CI Python 3.13 | Same run and commit; log: `153 passed, 1 warning in 11.89s` | Passed for that commit |
| Local full suite on current Windows checkout | `python -m pytest -q` | Pending user-run verification |
| Persistent cross-session recall | `python -m pytest -v tests/test_m0_history_acceptance.py` | Covered by public CI baseline; rerun after current branch changes |
| Tenant isolation | M0 acceptance and REST/MCP/library coverage | Covered by public CI baseline; rerun after current branch changes |
| Correction/current-history behavior | M0 acceptance, store, replay tests | Covered by public CI baseline; rerun after current branch changes |
| Delete after reopen/rebuild and disk/WAL scrub | `tests/test_m0_history_acceptance.py`, `tests/test_delete_ondisk.py`, replay tests | Covered by public CI baseline; rerun after current branch changes |
| Atomicity/failure injection | Store mutation failure-injection tests | Covered by public CI baseline; rerun after current branch changes |
| Repository hygiene | `python scripts/check_repo_hygiene.py` in CI | Passed for public CI baseline |
| Patch whitespace | `git diff --check` in CI | Passed for public CI baseline |
| Consented, de-identified held-out real-history evaluation | Frozen protocol + dataset hash/version + aggregate report + reviewer sign-off | NOT RUN; no eligible dataset supplied |
| Production security/privacy review | Review artifact for authz, retention, deletion, backup/WAL, export, incident response | NOT ESTABLISHED |

## Transaction and deletion contract

Public state-changing methods `write`, `write_quarantined`, `supersede`, `delete`, `revoke_writer`, `handoff_save`, and `rebuild_views` must either commit all event/view changes or roll back the operation. Delete scrubs the source event payload in place, then appends a delete event; this is a documented privacy exception to strict event-log immutability. Revocation clears searchable views but retains source events for audit.

SQLite secure-delete and WAL checkpointing are local mitigations, not a universal physical-erasure guarantee. Backups, copied files, filesystem snapshots, storage-device remnants, and already-exported data require separate operational controls.

## Release gate

M0 implementation tests and the public Python 3.11/3.12/3.13 CI matrix passed on commit `f150a1996bda6292fae295c65ce14d9faf17a06b`. This does not close real-history evaluation or production security/privacy review. Any later code change requires the tests and CI matrix to be rerun against that exact changed tree.