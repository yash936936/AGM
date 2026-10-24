# Phase 9 Active Memory Implementation Report

## Implementation delivered

- `src/agm/active_memory.py`: bounded context pack with current-query, profile/preference, and active-goal retrieval lanes; deduplication; tenant/project-safe use of existing retrieval; explicit conflict warnings for multiple open-ended values; untrusted-data framing; approximate token-budget enforcement.
- `src/agm/active_memory_policy.py`: conservative eligibility policy for write, correction, history, and deletion proposals. Evidence quotes must be present verbatim in the current user message for writes/corrections; corrections need explicit correction language; history and deletion need explicit user intent; deletion needs a concrete target.
- `src/agm/turn_loop.py`: host-independent turn controller that retrieves before the model callback and evaluates candidate memory operations after the response. It does not automatically call mutation tools.
- `tests/test_active_memory.py`, `tests/test_active_memory_policy.py`, and `tests/test_turn_loop.py`: focused regression coverage authored but not run.
- `eval/active_memory_simulation.py`: deterministic multi-turn policy scenarios authored but not run.
- `docs/active_memory.md`, `README.md`, decision/debug/status logs, and package exports updated.
- Existing REST/MCP adapters and the nine MCP tool names are unchanged. No pull request was created as part of this implementation pass.

## Contract notes

- Profile and goal retrieval use caller-supplied prompts because the frozen memory schema does not define dedicated profile/goal record types.
- Token usage is estimated as four characters per token, and whole records are included only when the rendered context fits.
- Conflicting open-ended facts with the same entity/attribute are explicitly surfaced. This is a conservative signal, not an automatic conflict-resolution policy.
- The policy only returns recommendations. Host code must still use existing authenticated tools, scope checks, core guards, operation IDs/idempotency, and event-sourced writes.

## Validation status

**NOT RUN, by instruction.** No unit tests, full pytest suite, compile checks, MCP smoke tests, REST smoke tests, or simulation results are claimed.

When implementation is frozen, run:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q tests/test_active_memory.py tests/test_active_memory_policy.py tests/test_turn_loop.py
python -m compileall -q src tests eval
python examples/mcp_smoke_client.py
python examples/rest_smoke_client.py
python eval/active_memory_simulation.py
python -m pytest -q
```
