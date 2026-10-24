# Active memory contract and policy

## Context contract

memory_context is prepared before the model call by the core layer. The caller
provides an authenticated Ctx, the current user query, optional explicit
profile/preference and active-goal retrieval prompts, optional entity/time
filters, retrieval mode, top-k, and an approximate token budget.

The returned TurnMemoryContext contains the original query, each retrieval
result, deduplicated selected records, the bounded prompt string, estimated
tokens, configured budget, and a safety notice. Retrieval stays tenant/project
scoped through MemoryStore.retrieve. Records are treated as untrusted data,
never as instructions. The budget is an estimate of four characters per token;
records are included whole and skipped if they do not fit. A budget too small
to retain the safety framing is rejected.

Profile and goal sections are retrieval searches, not privileged record types.
The caller must supply explicit prompts because the frozen memory schema does
not define special profile or goal types. Current retrieval's eligibility,
temporal filtering, trust gates, and abstention behavior remain authoritative.
This layer does not silently resolve contradictory facts; callers should preserve
provenance and report conflict/uncertainty rather than choosing by recency alone.

## Post-response operation policy

MemoryProposal represents a model-suggested operation. evaluate_memory_proposal
is deliberately pure and never calls a tool or writes to storage.

- Write: require entity, attribute, value, and an evidence quote found verbatim
  in the current user message.
- Correction: require the same grounding plus explicit correction language.
  The host must look up relevant history and use the existing correction/supersede
  operation rather than overwriting history.
- History: use the existing scoped retrieval/history operation only when the
  user explicitly asks to recall prior information or history.
- Deletion: require explicit forget/delete language and a concrete target ID
  or entity. Confirm target scope and use the existing authenticated delete path.
- Abstain: reject unsupported, ambiguous, ungrounded, or underspecified
  proposals. An eligible decision is not authorization to mutate memory.

All real writes remain subject to the existing core guards, identity, scopes,
tenant/project filters, idempotency key/operation ID, and event-sourced audit
contract. The existing nine MCP tools are unchanged.

## Controlled turn loop

run_active_turn performs retrieval first, calls a host-supplied model callback
with the query and untrusted context, and evaluates returned memory proposals
after the answer. It returns the decisions for host review. It does not execute
writes, corrections, history calls, or deletions itself. This makes the order
testable without depending on a provider or granting model output direct storage
authority.

## Implementation validation status

Tests and smoke clients are intentionally not run during this implementation
pass. After the implementation is frozen, run the focused tests, full test
suite, compile check, MCP and REST smoke clients, and deterministic simulation.
