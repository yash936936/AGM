# AGM M0 acceptance matrix

This matrix distinguishes implementation coverage from verification evidence. A passing local suite is necessary but is not, by itself, proof of production readiness.

| Requirement | Implementation / test evidence | Status before repository run |
|---|---|---|
| Guarded write is atomic | `write()` uses `BEGIN IMMEDIATE`; existing apply-failure rollback test | Implemented; prior suite reported passing |
| Quarantined write is atomic | `_atomic_mutation`; new failure-injection regression | Implemented; must run in full repository |
| Supersede is atomic | `_atomic_mutation`; new failure-injection regression verifies prior active node is preserved | Implemented; must run in full repository |
| Delete and payload scrub are atomic | `_atomic_mutation(checkpoint=True)`; new injected-failure regression verifies source payload and views roll back | Implemented; must run in full repository |
| Writer revocation is atomic | `_atomic_mutation(checkpoint=True)`; new injected-failure regression | Implemented; must run in full repository |
| Handoff packet save is atomic | `_atomic_mutation`; new injected-failure regression | Implemented; must run in full repository |
| View rebuild is atomic | `_atomic_mutation`; new injected replay-failure regression | Implemented; must run in full repository |
| Concurrent independent writers | Existing two-connection/thread regression | Prior suite reported passing; rerun required after this bundle |
| Retry/idempotency contracts | Existing exact-retry, payload mismatch, context mismatch, and no-op claim tests | Prior suite reported passing; rerun required after this bundle |
| Delete restores previous single-valued fact | Existing deletion/replay regression | Prior suite reported passing; rerun required after this bundle |
| SQLite secure-delete setting | Connection enables `PRAGMA secure_delete = ON`; new setting test | Implemented; test pending |
| WAL checkpoint after delete/revoke | Checkpoint occurs only after outer transaction commits | Implemented; physical-erasure validation remains limited |
| Event-log contract | Delete scrubs the source event payload in place, then appends a delete event | Explicit privacy exception to strict append-only immutability |
| Full AGM test suite on the user's checkout | Must run `python -m pytest -q` in repository root | **Unverified here** |
| CI matrix on Python 3.11, 3.12, 3.13 | Workflow exists at `.github/workflows/tests.yml` | **Unverified until a remote Actions run succeeds** |
| Repository hygiene | `.gitignore` excludes local databases, secrets, caches, and build output | Reviewed in bundle; tracked-file scan still required in the actual repository |

## Transaction contract

Public state-changing methods `write`, `write_quarantined`, `supersede`, `delete`, `revoke_writer`, `handoff_save`, and `rebuild_views` must either commit all event/view changes or roll back the operation. The shared mutation wrapper uses `BEGIN IMMEDIATE` at the outer boundary and a savepoint for nested public mutations. It does not commit a transaction owned by a caller.

## Deletion and replay contract

- Deleting a memory removes its derived node, FTS row, embedding, and edges through the delete event's view application.
- The deleted source event payload is replaced with `{"scrubbed":true}` in the same transaction, so replay skips the erased source payload.
- The delete event retains the item identifier and, when applicable, the predecessor identifier needed to restore the prior active value during replay.
- SQLite `secure_delete` is enabled and the WAL is checkpointed with `TRUNCATE` after a successful delete/revoke commit.
- These measures are not a universal physical-erasure guarantee. External backups, copied database files, filesystem snapshots, storage-device behavior, and already-exported data are outside this local SQLite guarantee and require separate operational controls.

## Release gate

M0 must not be called fully accepted until the full test suite passes on the user's complete repository, the CI matrix has a successful run, and a tracked-file scan confirms no secrets or local database artifacts are committed. Record the actual test count, commit SHA, and CI run URL in this file when available; do not infer them from earlier runs.
