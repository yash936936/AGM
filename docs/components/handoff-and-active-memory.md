# Handoff and active memory

**Handoff**
- `src/agm/handoff.py`: `compare_readback`. Save, resume and readback are `MemoryStore` methods.
- Flow: save `TaskState` → resume with a model name and token budget → bounded context packet plus a readback prompt → readback comparison reports mismatches before work continues.
- Packets are tenant-scoped rows in `packets`. Task state is sanitized before storage.

**Active memory (read-only for adapters)**
- `src/agm/active_memory.py`: `prepare_turn_context` builds a bounded, labelled, conflict-aware context pack (selected records, conflict notices, token estimate, untrusted-data notice).
- `src/agm/active_memory_policy.py`: `evaluate_memory_proposal`, a conservative check that a model-proposed write, correction or delete is grounded in the user's message. Advisory only, not a security boundary.
- `src/agm/active_memory_turn.py`, `turn_loop.py`, `reference_host.py`: turn orchestration and a reference host showing explicit authorization before any proposal is executed.
- REST exposes only the read-only pair (`/v1/active/context`, `/v1/active/review`, D-044).

**Easy to break:** retrieved memory is data, never instructions; keep the notice on every pack. Do not add a REST route that executes proposals without a decision entry.

**Tests:** `test_handoff.py`, `test_active_memory.py`, `test_active_memory_policy.py`, `test_active_memory_turn.py`, `test_turn_loop.py`, `test_reference_host.py`.
**Docs:** `../active_memory.md`. **Decisions:** D-044.

---
**Next:** Return to [`context.md`](../../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
