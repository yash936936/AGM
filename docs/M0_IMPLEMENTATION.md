# AGM M0 implementation notes

This overlay extends the previously validated M0 baseline with uniform transaction boundaries and failure-injection coverage.

## Mutation guarantees

- `write()` keeps its existing `BEGIN IMMEDIATE` read/decide/append/apply transaction.
- `write_quarantined()`, `supersede()`, `delete()`, `revoke_writer()`, `handoff_save()`, and `rebuild_views()` use a shared atomic mutation wrapper.
- The wrapper starts `BEGIN IMMEDIATE` for an outer operation and a SQLite savepoint for a nested operation. It rolls back on any exception and never commits a transaction owned by an outer caller.
- Delete and writer revocation checkpoint the WAL only after the successful outer transaction commits.
- `PRAGMA secure_delete=ON` is enabled for each store connection. This is a mitigation, not a guarantee against independent backups, snapshots, copied database files, or storage-device remnants.

## Test coverage added

- Failure injection for quarantined writes, supersede, delete, revoke, handoff save, and replay/view rebuild.
- Independent-connection visibility during an uncommitted write.
- Secure-delete setting verification.

## Event history and deletion

AGM's delete behavior intentionally scrubs the deleted source event payload in place, then appends a delete event that retains the identifier and restoration metadata needed for replay. Therefore, the event table is append-oriented but is not strictly immutable under privacy deletion. See `M0_ACCEPTANCE_MATRIX.md` for the exact contract and remaining release gate.

## Verification state

The earlier user-reported baseline was 141 passed and one non-fatal deprecation warning. That run predates the additional transaction changes and tests in this overlay. The full suite and remote CI matrix must be rerun after applying this overlay to the complete repository. Do not mark M0 accepted until those results are recorded.
