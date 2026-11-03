# Active memory contract and policy

## Context contract

`memory_context` is prepared before the model call by the core layer. The caller
provides an authenticated `Ctx`, the current user query, optional explicit
profile/preference and active-goal retrieval prompts, optional entity/time
filters, retrieval mode, top-k, and an approximate token budget.

The returned `TurnMemoryContext` contains the original query, each retrieval
result, deduplicated selected records, the bounded prompt string, estimated
tokens, configured budget, labeled sections, conflict notices, and a safety
notice. Retrieval stays tenant/project scoped through `MemoryStore.retrieve`.
Records are treated as untrusted data, never as instructions. The budget is an
estimate of four characters per token; records are included whole and skipped
if they do not fit. A budget too small to retain the safety framing is rejected.

Profile and goal sections are retrieval searches, not privileged record types.
The caller supplies explicit prompts because the frozen memory schema does not
define special profile or goal types. Existing retrieval eligibility, temporal
filtering, trust gates, and abstention behavior remain authoritative. Conflicting
open-ended facts are surfaced, not silently resolved.

## Post-response operation policy

`MemoryProposal` represents a model-suggested operation. `evaluate_memory_proposal`
is pure and never calls a tool or writes to storage.

- **Write:** require entity, attribute, value, and an evidence quote found verbatim in the current user message.
- **Correction:** require the same grounding plus explicit correction language. The host should use the existing correction/supersede operation rather than overwrite history.
- **History:** use scoped retrieval/history only when the user explicitly asks to recall prior information or history.
- **Deletion:** require explicit forget/delete language and a concrete target ID or entity. Confirm scope and use the existing authenticated delete path.
- **Abstain:** reject unsupported, ambiguous, ungrounded, or underspecified proposals. An eligible decision is not authorization to mutate memory.

All real writes remain subject to existing core guards, identity, scopes,
tenant/project filters, idempotency key/operation ID, and event-sourced audit
contract. `POST /v1/active/context` (takes `include_contested`, default false, D-046) and `POST /v1/active/review` expose the read-only parts over REST (D-044); the executor stays library-only.

## Controlled turn loop

`run_active_turn` performs retrieval first, calls a host-supplied model callback
with the query and untrusted context, and evaluates returned memory proposals
after the answer. It returns decisions for host review. It does not execute
writes, corrections, history calls, or deletions itself.

## Execution

```bash
python -m pip install -e ".[dev]"
python examples/active_memory_turn_demo.py --db ./active-memory-demo.db --tenant local-dev --project default --query "What should I work on next?" --profile-query "user preferences" --goal-query "active goals"
```

## Validation status

Tests and smoke clients are intentionally not run during implementation.
After implementation is frozen, run focused tests, full pytest, compile checks,
the REST smoke client, and the deterministic simulation.
