# Phase 9 Report: Active Memory Context and Turn Control

## Delivered

- Current-query, profile/preference, and active-goal retrieval lanes.
- Deduplication, approximate token-budget enforcement, and untrusted-data framing.
- Explicit conflict notices for different open-ended values of the same entity/attribute.
- Conservative policy for write, correction, history, and deletion proposals.
- Controlled retrieval-before-model and policy-after-response loop, without automatic mutation.
- Focused tests and deterministic simulated-conversation scenarios authored.
- Existing REST/MCP adapters and all nine MCP tool names remain unchanged.

## Validation

**Not run by instruction.** No test, compile, smoke-check, or simulation results are claimed.

## Limitations

Profile and goal retrieval are caller-supplied prompts because the frozen schema has
no dedicated profile/goal types. Token use is estimated at four characters per token.
Conflict detection is conservative. Eligible proposals are not authorization; hosts
must use existing authenticated tools and core guards.
