# Trust and lifecycle

**Purpose:** decide whom to believe, protect what is stored, and remove it correctly.

**Files**
- `src/agm/guard.py`: `sanitize_value`, `sanitize_task_state`, `inspect_write_item`, `guarded_write`. Runs inside `MemoryStore` for every caller; adapters contain no safety logic.
- `src/agm/trust.py`: tier weights, age and recency scoring, independent corroborations, probation, effective confidence, ranking score, decay weight, lifecycle candidates. Coefficients are provisional (D-008).
- `src/agm/lifecycle.py`: `MemoryLifecycle.before_turn` and `after_turn`, assistant-turn orchestration over the store.
- Delete, `expire_before` and `revoke_writer` live in `store.py`.

**Semantics (do not blur)**
- `delete` is a hard purge: content, derived data and the original event payload are scrubbed and the WAL flushed.
- `revoke_writer` is a rollback: that writer's views are cleared, events kept for audit.
- `expire_before` is a core-only sweep scoped to tenant and project, judged on event creation time, skipping pinned items unless `include_pinned=True`. It is not a guarantee about backups or filesystem snapshots.
- A fact whose tier outranks the new writer's by two or more levels is not overwritten; the new claim becomes contested.

**Easy to break:** any new method that persists user-supplied strings must sanitize them and be tested through the library directly, not only through REST.

**Tests:** `test_guard.py`, `test_guard_core.py`, `test_trust.py`, `test_trust_phase2.py`, `test_lifecycle.py`, `test_delete_ondisk.py`, `test_m1_retention.py`, `test_m2_acceptance_lifecycle.py`, `test_privacy_edge_acceptance.py`.
**Decisions:** D-008, D-023, D-040, D-041, D-045. **Open work:** R3.x (audit log, key expiry and rotation).

---
**Next:** Return to [`context.md`](../../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
