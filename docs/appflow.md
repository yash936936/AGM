# App flow — AGM prototype

> Stub. Grows as phases land; each scenario is added when its phase is done.

## Agent remembers and corrects (Phases 1–3)
1. Agent connects (REST key or MCP stdio) and calls `memory_write` with entity, attribute, value, text.
2. Later the fact changes; agent calls `memory_write` with the new value (or `memory_supersede` with a reason).
3. Next session the agent calls `memory_retrieve`; only the current value returns, with provenance and confidence. An unanswerable query returns `abstain: true`.

## Switch models mid-task (Phase 4)
1. Agent A calls `handoff_save` with TaskState. 2. Agent B calls `handoff_resume` with its model name and token budget and receives assembled context plus a readback prompt. 3. B answers via `handoff_readback`; mismatches are shown before work continues.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
