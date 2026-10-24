# Phase 9 Step 1 Report: Pre-answer active memory context

## Files changed
- `src/agm/active_memory.py`: read-only retrieval across the current query and optional profile/preference and goal queries; ID deduplication; bounded context rendering; untrusted-memory notice.
- `src/agm/__init__.py`: exports `TurnMemoryContext` and `prepare_turn_context`.
- `tests/test_active_memory.py`: coverage for multi-query retrieval, no-write behavior, tenant isolation, deduplication, safety framing, budget bounds, and invalid inputs.
- `docs/decisions.md`: D-027.
- `docs/status.md`: records this as an incomplete Phase 9 step.
- `docs/debug.md`: records changes and verification limits.

## Tests
- `python -m pytest -q tests/test_active_memory.py`: NOT RUN.
- `python -m pytest -q`: NOT RUN.
- `python -m compileall -q src tests`: NOT RUN.
- `python examples/mcp_smoke_client.py`: NOT RUN.
- `python examples/rest_smoke_client.py`: NOT RUN.

No test results are claimed. Changes were written to branch `phase9-active-memory-before-answer`.

## Contract concerns and assumptions
- Existing contracts remain unchanged. Profile and goal records have no dedicated schema type, so callers must provide explicit retrieval prompts.
- Token usage is estimated as four characters per token, consistent with the existing handoff convention.
- Retrieved memory remains untrusted data; the helper does not make a model call or execute retrieved text.

## Not finished
This is only the first Phase 9 step. It is not integrated into the REST/MCP agent workflow, does not resolve conflicting goals/facts beyond existing retrieval behavior, and does not implement during-turn updates or post-answer learning. Run the listed tests and review the output before proceeding.
