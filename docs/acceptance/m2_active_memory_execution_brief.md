# M2 Execution Brief: Active Memory Behavior

**Status:** STARTED / NOT ACCEPTED  
**Date:** 2026-10-26  
**Scope:** Before, during, and after an assistant turn.

## Goal

Make AGM behave as an active memory layer around an assistant turn, rather than only a store that an agent must call manually. Implement a narrow, inspectable orchestration seam over existing core behavior. Do not add an LLM dependency or silently execute model-proposed mutations.

## Existing starting points

- `src/agm/active_memory.py`: `prepare_turn_context()` retrieves query, profile/preferences, and active-goal lanes, deduplicates results, reports conflicts, bounds context, and marks memory as untrusted.
- `src/agm/active_memory_policy.py`: `evaluate_memory_proposal()` checks proposed writes/corrections/history/deletion against the current user message.
- `tests/test_active_memory.py` and `tests/test_active_memory_policy.py`: current focused tests.

These are existing components, not proof that the full turn lifecycle is integrated.

## Lifecycle contract

### 1. Before the model answers

- Retrieve only for the authenticated `Ctx` and current tenant/project.
- Include current-query evidence plus explicitly supplied profile/preferences and active-goal queries.
- Respect temporal validity, trust/high-stakes filtering, abstention, conflicts, and the configured context budget.
- Render retrieved records as untrusted data, never as instructions.
- Do not mutate the event log during preparation.

### 2. During the turn

- Treat model-proposed memory operations as untrusted proposals.
- Ground write/correction proposals in a verbatim quote from the current user message.
- Require explicit correction language for corrections, explicit recall intent for history, and explicit forget/delete intent plus a specific target for deletion.
- A policy decision marked eligible is not authorization to mutate. The host remains responsible for user confirmation when appropriate and for calling the existing authenticated/scoped API.
- Never let retrieved memory itself authorize writes, corrections, or deletion.

### 3. After the turn

- Provide an explicit result object for accepted proposals and rejected proposals, including reasons.
- Persist only after the host executes an authorized operation through existing store methods.
- Ensure each persisted change is represented in the append-only event log and is deterministic after `rebuild_views()`.
- Corrections must preserve history and current-value semantics; hard deletion must not resurface content after replay/reopen.
- Do not add silent background writes or claim an action was persisted when it was only proposed.

## Implementation order

1. Audit current active-memory modules, call sites, models, adapter boundaries, and tests. Record gaps before coding.
2. Add a small orchestration API (or extend the existing API only if it fits the frozen contracts) that returns pre-answer context and evaluates proposals without mutating memory.
3. Add regression tests for before/during/after behavior, including empty/malformed proposals, quote mismatch, ambiguous corrections, unauthorized deletion, cross-tenant isolation, no mutation during preparation/evaluation, and replay behavior for any executed mutation.
4. Verify library/API/MCP behavior remains consistent. Do not change public REST paths or MCP tool names without a numbered decision-log entry first.
5. Run focused tests, full pytest, both smoke clients, hygiene/whitespace checks, and package inspection on the exact PR head. Record real results only.

## Acceptance criteria

- [ ] Context preparation is read-only and tenant/project scoped.
- [ ] Retrieved text is always labeled untrusted and cannot forge context delimiters.
- [ ] Conflicting facts are surfaced, not silently resolved.
- [ ] Proposal evaluation cannot itself mutate storage.
- [ ] Corrections, history reads, and deletion require their respective explicit user intent.
- [ ] Host authorization is distinct from proposal eligibility.
- [ ] Every actual mutation uses existing core APIs, is event logged, and survives replay/reopen correctly.
- [ ] No new dependency and no frozen-contract changes without a decision entry.
- [ ] Focused and full CI pass on the exact head, and `docs/debug.md` records actual evidence.

## Explicitly out of scope

- Automatic LLM invocation or extraction.
- Autonomous/background memory writes.
- Remote service exposure.
- Claiming production readiness from synthetic tests.
- Closing the three external release gates: held-out consented real-history evaluation, independent security/privacy review, and real third-party host integration.

## Current validation

NOT RUN for this kickoff. This brief documents scope and acceptance criteria; implementation remains pending.
