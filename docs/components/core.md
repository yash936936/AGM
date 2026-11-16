# Core

**Purpose:** the event-sourced store every other part calls. All behaviour lives in `MemoryStore`; adapters only authenticate, build a `Ctx` and call it.

**Files**
- `src/agm/store.py`: `MemoryStore` (`write`, `write_quarantined`, `supersede`, `retrieve`, `history`, `delete`, `expire_before`, `rebuild_views`, `revoke_writer`, `handoff_save/resume/readback`), `canonical_entity`, `sanitize_fts_query`. Largest file in the repo.
- `src/agm/events.py`: append-only event log, `HybridLogicalClock`, `append_event`, `decode_payload`.
- `src/agm/db.py`: SQLite connection, schema creation, FTS5 check.
- `src/agm/models.py`: frozen public contracts (`Ctx`, `WriteItem`, `WriteResult`, `Node`, `RetrieveResult`, `TaskState`, `Packet` and others).
- `src/agm/bootstrap.py`: one-time owner key creation.

**Write path:** auth context → redact secrets → screen instruction-like text (quarantine on a hit) → assign tier → append event (idempotency check) → apply to views (ADD, SUPERSEDE, NOOP or CONTESTED) → embed and index. Same value from a different, independent writer corroborates; the same writer repeating never does.

**Easy to break**
- Every mutation must append an event first and replay identically; each new mutation needs a replay test (`tests/test_replay.py`).
- `events` is the only source of truth; `nodes`, `edges`, `entities`, FTS and `embeddings` are views.
- Contracts in `models.py` are frozen; a change needs a `D-0NN` entry first.
- Tenant filter on every query; add a cross-tenant test for any new read path.

**Tests:** `test_store.py`, `test_replay.py`, `test_contested.py`, `test_delete_ondisk.py`, `test_e2e_rest.py`.
**Decisions:** D-006, D-046. **Open work:** R5.3 (event-log versioning and upgrade path).

---
**Next:** Return to [`context.md`](../../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
