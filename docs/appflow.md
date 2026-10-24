# App flow — AGM prototype

> Stub. Grows as phases land; each scenario is added when its phase is done.

## Agent remembers and corrects (Phases 1–3)
1. Agent connects (REST key or MCP stdio) and calls `memory_write` with entity, attribute, value, text.
2. Later the fact changes; agent calls `memory_write` with the new value (or `memory_supersede` with a reason).
3. Next session the agent calls `memory_retrieve`; only the current value returns, with provenance and confidence. An unanswerable query returns `abstain: true`.

## Switch models mid-task (Phase 4)
1. Agent A calls `handoff_save` with TaskState. 2. Agent B calls `handoff_resume` with its model name and token budget and receives assembled context plus a readback prompt. 3. B answers via `handoff_readback`; mismatches are shown before work continues.


## Active memory before and after a turn (Active Memory Loop v1)
1. The host receives a user message and resolves the authenticated AGM identity; the host, not the model, supplies that exact message to the post-turn policy.
2. Before generating a response, the host calls `MemoryStore.memory_context` / MCP `memory_context` / REST `POST /v1/memory/context`. AGM returns a compact context string, structured relevant evidence, profile/preferences, active-goal and decision categories where discoverable, conflict metadata, provenance and an abstention signal.
3. The host inserts only the bounded `context` string into the model's evidence/context section. The model is instructed that retrieved content is untrusted data, never executable instructions.
4. After the response, the host receives a structured proposed action: `remember`, `correct`, `forget`, `ignore`, or `ask_user`. It calls `apply_memory_decision` through `run_active_turn`; quotes must match the actual current message.
5. Remember uses the guarded event-sourced `write` path. When a host supplies a stable `operation_id`, AGM derives an idempotency key scoped to that operation; without one, it relies on normal duplicate/no-op behavior and does not promise cross-retry correction idempotency. Correct requires explicit correction intent, a replacement with the same entity/attribute and the selected active memory, then uses the existing supersede path. Forget requires an explicit, non-negated request whose subject matches the selected memory/history and atomically hard-deletes the connected supersede chain. Ignore does not mutate storage.
6. The host tells the user about a memory action only after AGM returns its result. For ambiguity, the action is confirmation-required and no mutation occurs.

**Native connector caveat:** the MCP tools cannot force their invocation on every user turn. In a native connector call, `current_user_message` is model-supplied; it is not a cryptographically trusted transcript. The host-controlled `run_active_turn` path is the only implementation here that enforces retrieve → generation callback → post-turn policy ordering.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
