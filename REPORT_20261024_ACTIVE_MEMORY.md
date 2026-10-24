# Active Memory Loop v1 — Implementation Report

**Date:** 2026-10-24  
**Branch:** `feature/active-memory-loop-v1`  
**Status:** Implementation prepared; testing deliberately deferred at the user's request.

## Goal

Implement the persistent-memory turn lifecycle:

1. Retrieve relevant memory before model generation.
2. Present memory to the model as evidence, never instructions.
3. Apply a conservative post-turn action: remember, correct, forget, ignore, or ask the user.
4. Preserve current AGM contracts and existing MCP tool names.
5. Make the flow reusable across model providers without introducing a new hard dependency.

## Files changed

### Core contracts and behavior

- `src/agm/models.py`
  - Adds `MemoryContextItem`, `MemoryContextPack`, `MemoryDecision`, `MemoryActionResult`, `MemoryHealthReport`, `ActiveTurnGeneration`, and `ActiveMemoryTurnResult`.
  - Context items retain provenance metadata without duplicating their full text; the rendered context contains the memory text.
- `src/agm/active_memory.py` (new)
  - Adds `ACTIVE_MEMORY_SYSTEM_PROMPT`.
  - Builds a token-budgeted context string from query-specific retrieval plus discoverable profile/preferences, goals, decisions, both eligible sides of contested facts, validity and provenance.
  - Adds metadata-only health diagnostics: SQLite integrity is database-wide, while item/index coverage counters are tenant/project-scoped.
  - Applies the post-turn memory policy with quote matching, key-value evidence checks, correction intent and target checks, conservative negated-intent guards, explicit operation-ID retry semantics, input-size limits, and confirmation-required responses.
  - Adds `run_active_turn` to enforce retrieve → provider callback → post-turn policy in an application-controlled host.
- `src/agm/store.py`
  - Adds `MemoryStore.memory_context(...)`.
  - Adds tenant/project-scoped `MemoryStore.forget(...)`, which removes the selected memory and connected supersede-history chain by scrubbing source event payloads, appending delete events, removing materialized/index data, and checkpointing inside one transaction.
- `src/agm/__init__.py`
  - Exports the new active-memory contract and helper APIs.

### Adapters and example

- `src/agm/mcp_server.py`
  - Adds `memory_context`, `memory_remember`, `memory_correct`, `memory_forget`, and `memory_health`.
  - Preserves the original nine MCP tool names and existing scope checks.
- `src/agm/api.py`
  - Adds `POST /v1/memory/context`, `POST /v1/memory/remember`, `POST /v1/memory/correct`, `POST /v1/memory/forget`, and `GET /v1/memory/health`.
  - Uses the existing API-key identity and scopes; legacy routes remain available.
- `examples/active_memory_loop.py` (new)
  - Demonstrates the controller offline; it makes no LLM request.
- `examples/mcp_smoke_client.py`
  - Updates tool expectations and adds checks for context, health, remember, correct and forget.
- `tests/test_mcp_stdio.py`
  - Updates the tool list expectations and adds context/health checks.
- `tests/test_active_memory.py` (new)
  - Covers context building/budgeting/categories, tenant isolation, evidence checks, idempotency, correction history, wrong-target protections, negative intent, health scope, controller ordering, and forgetting/replay.
- `tests/test_active_memory_api.py` (new)
  - Covers REST context, remember/correct/forget lifecycle, health, and read-scope enforcement.

### Documentation and tracking

- `README.md`
- `context.md`
- `docs/architecture.md`
- `docs/appflow.md`
- `docs/debug.md`
- `docs/decisions.md` — D-027 through D-031; newest decisions cover target-safe mutations, contested evidence/health scope, and explicit host-operation-ID semantics.
- `docs/phases.md`
- `docs/status.md`
- `examples/claude_code_mcp.md`
- `examples/curl.md`
- `prompts/active_memory_system_prompt.md` (new)

## New tests: what each group is intended to prove

**These tests are authored/updated but have not been executed.** They are not passing-test claims.

- `tests/test_active_memory.py`: bounded context string; context categories and both sides of contested evidence; no cross-tenant retrieval; source quotes and proposed values must match the current message; optional stable operation IDs make retries idempotent without suppressing later repeated preferences; host IDs override model-proposed keys; corrections require explicit intent and the same entity/attribute; forgetting requires explicit subject-matching intent; unrelated targets and negated requests are blocked; input-size limits are enforced; health returns metadata with scope-aware counters; the controller retrieves before generation; forgetting a connected correction chain remains deleted after view rebuild.
- `tests/test_active_memory_api.py`: new REST endpoints return the intended result shape, enforce existing read/write/delete scopes, and expose a context pack with a bounded rendered string.
- Updated `tests/test_mcp_stdio.py`: the MCP server lists the original nine tools plus five active-memory tools and returns a bounded context pack and metadata-only health response.
- Updated `examples/mcp_smoke_client.py`: local MCP host smoke sequence exercises context, health, remember, correct and forgetting a connected two-version chain, while retaining prior guard and handoff checks.

## Validation commands

**NOT RUN — testing was explicitly deferred until implementation was complete.** No compile, unit test, integration test, smoke test, or benchmark command has been executed for this branch.

After applying/reviewing the implementation on the Windows checkout, run from the repository root:

```bash
python -m compileall -q src tests eval scripts examples
python -m pytest -q
python examples/mcp_smoke_client.py
python examples/rest_smoke_client.py
python eval/stale_facts.py
python examples/active_memory_loop.py --db ./phase8-memory.db --tenant phase8-demo --project phase8 --query "Who owns billing-api?" --token-budget 1000
git diff --check
git status --short
```

Run the MCP smoke client in an environment where the official MCP SDK is installed. If any command fails, fix the implementation and rerun the relevant checks before calling this work complete. Do not proceed to native Claude/ChatGPT connection or remote deployment before these checks and review are finished.

## Design decisions and assumptions

- The existing nine MCP tool names and existing low-level REST routes remain intact; five higher-level tools are additive.
- The context-string budget uses `ceil(characters / 4)`, not a model-specific tokenizer. The structured response includes compact metadata for memories actually rendered, but the estimate is not a hard model-token guarantee.
- Profile/preferences, goals and decisions are detected using existing entity/attribute/text values; no database migration or new dependency was added. Reliable categorization works best when writers use the documented attribute conventions (for example, `communication_preference`, `active_goal`, `decision`).
- The host-controlled `run_active_turn` is the path that enforces retrieval before generation and the post-turn policy after generation. The included example uses an offline callback; a model-provider callback has not been implemented in this work package.
- Native MCP tools cannot force every consumer ChatGPT or Claude message to call memory. On a native MCP call, `current_user_message` is model-supplied and therefore the quote check is a policy guard, not an authentication boundary.
- Local/loopback-only deployment posture is unchanged. This work does not add remote hosting, OAuth, or production multi-tenant authentication.
- Trust and rank values remain uncalibrated; this work does not alter Phase 6/7/8 evaluation thresholds or make claims about the H1–H7 hypotheses.

## Unfinished items / review concerns

1. All authored tests and smoke clients need to be run on the actual Windows checkout; results are **NOT RUN**.
2. Review context category recall and retrieval overhead, since context assembly makes supplementary retrievals for profile, goals and decisions.
3. Validate the tenant/project-filtered recursive SQLite CTE, atomic event scrubbing, WAL checkpoint and rebuild behavior on the user's installed SQLite/Python version.
4. Decide whether the native model tool should receive only the rendered context string or more compact metadata; the current response intentionally keeps full text in the context string and IDs/trust/validity/provenance in structured fields.
5. Build a provider-specific callback only after core testing if an LLM-backed controlled turn loop is needed. The current offline example intentionally makes no LLM request.
6. Confirm the native MCP/REST adapters pass an optional `operation_id` through on remember/correct, and that controlled `run_active_turn(operation_id=...)` overrides any model-proposed operation ID.
7. Confirm contested counterparty text is included only when tenant/project, temporal and high-stakes eligibility allow it; database-wide SQLite integrity and scoped item/index counts are documented separately.
6. Native ChatGPT/Claude integration remains a later milestone; this branch does not guarantee tool invocation on every message.

## Completion rule

The implementation is ready for the separate test phase, not yet certified complete. Do not mark Active Memory Loop v1 done until the code review, full suite, both smoke clients, the offline controller example, and follow-up fixes (if any) are complete.
