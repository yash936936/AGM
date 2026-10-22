# Phase 4 contract addendum (Decision D-016)

This additive change exists because the original frozen contracts could not express the Phase 4 high-stakes gate or return assembled handoff context. D-016 records the change in `docs/decisions.md`; no existing field was removed or renamed.

## Retrieval

`MemoryStore.retrieve` adds `high_stakes: bool = False`, after `include_superseded`. The REST request and MCP `memory_retrieve` tool expose the same optional boolean. The default remains false so Phase 1/2 outputs and the `expand=False` baseline stay unchanged.

When `high_stakes=True`, an item written at `trusted_agent` or `untrusted` tier is filtered out until a different writer independently corroborates the same active entity/attribute/value. Corroboration is a content-free `corroborate` event produced when another writer writes the same single-valued fact. Revoking that writer withdraws its corroboration contribution.

## ResumeResult

The original `packet_id` and `goal` fields are retained. These fields are added:

- `context: str`: the assembled pinned memory, task state, and retrieved memory.
- `readback_prompt: str`: asks the target model to report its understanding and treat retrieved text as untrusted data.
- `target_model: str`: requested target model label.
- `token_budget: int`: caller-provided budget.
- `estimated_tokens: int`: `ceil(len(context) / 4)`.

Context assembly follows pinned memory, task state, then retrieved memory. The default token estimate is characters divided by four; the context string is capped at four characters per budget token. If graph retrieval abstains for a long summary under the default hash embedder, handoff assembly tries the flat baseline before omitting retrieved memory.

## Readback comparison

Goal, decisions, and open questions are matched against the readback's goal, decisions, and open items. Exact normalized containment or token-set Jaccard similarity of at least 0.60 is treated as a match. This is a lexical, uncalibrated check and should be treated as a warning aid, not proof that another model understood or will follow a decision.

## Revocation/audit semantics

`revoke_writer` stores the affected node IDs and revoked corroboration event IDs in an event so replay removes the same materialized nodes and `derived_from` descendants. Original source event payloads remain in the event log for audit. This operation removes searchable views but is not a replacement for hard delete, which scrubs the source event payload.
