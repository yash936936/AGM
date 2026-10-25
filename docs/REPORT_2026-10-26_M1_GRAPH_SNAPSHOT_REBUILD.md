# Report — 2026-10-26 M1 graph snapshot rebuild acceptance

## Files changed
- `tests/test_local_hub.py`: verify a scoped graph snapshot is identical before and after `MemoryStore.rebuild_views()`.
- `context.md`, `docs/status.md`, `docs/debug.md`: document the acceptance gap and validation state.

## What the test proves
The generated graph snapshot remains marked as a snapshot and has identical nodes, a non-empty node-to-node `derived_from` edge, and digest after materialized views are rebuilt from the event log.

## Validation
- Local tests: NOT RUN in this remote editing environment.
- Exact-head CI, repository hygiene, whitespace checks, and wheel/package inspection: PENDING.

## Contract concerns and assumptions
- Snapshot determinism is measured as equality of the returned data structure, including `snapshot_id`.
- The test does not substitute for independent evaluation of graph retrieval quality or held-out real-history tests.

## Unfinished items
- Exact-head CI and review pending.
- M1 remains PARTIAL / VERIFY; M0 remains IN PROGRESS.
- Held-out consented real-history evaluation and independent security/privacy review remain open release gates.
