# M2 Implementation Report — Active-turn orchestration seam

**Status:** IMPLEMENTED CANDIDATE / NOT ACCEPTED  
**Date:** 2026-10-26

## Files changed
- `src/agm/active_memory_turn.py`: adds `begin_active_memory_turn` for read-only pre-answer context and `review_active_memory_proposals` for policy decisions.
- `tests/test_active_memory_turn.py`: covers read-only preparation, budget enforcement, eligible/rejected proposal separation, and host authorization boundary.
- `docs/decisions.md`: records D-035 for keeping orchestration read-only.
- `docs/status.md`, `docs/debug.md`: record M2 implementation candidate and validation status.

## Test coverage intent
- `test_begin_turn_prepares_context_without_mutating_event_log`: ensures turn preparation returns relevant context and does not append events.
- `test_review_separates_eligible_proposals_from_rejected_ones`: ensures policy outcomes remain inspectable and deletion without explicit intent is rejected.
- `test_review_does_not_need_store_and_cannot_mutate_it`: keeps proposal review independent of persistence and documents that eligibility is not authorization.
- `test_begin_turn_rejects_invalid_context_budget`: preserves input validation at the orchestration boundary.

## Commands and validation
- Focused pytest: NOT RUN in this remote GitHub editing environment.
- Full pytest: NOT RUN.
- REST smoke client: NOT RUN.
- MCP smoke client: NOT RUN.
- Hygiene, whitespace, and package inspection: NOT RUN.
- Exact-head CI: pending.

## Contract concerns
None intended. No frozen REST paths, MCP tool names, persisted schemas, or dependencies changed.

## Assumptions and limitations
- The host supplies the actual user message and any model/host proposals.
- A policy decision marked eligible is not authorization to mutate.
- Mutations must use existing authenticated, tenant/project-scoped APIs.
- No LLM calls or background writes are introduced.
- This candidate does not close held-out real-history evaluation, independent security/privacy review, or third-party host integration.

## Unfinished
Run focused and full tests, both smoke clients, hygiene/whitespace/package checks, inspect CI, and obtain review before accepting M2.
