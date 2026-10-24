# Phase 9 Report: Active Memory Context and Turn Control

## Scope

Implement the active-memory foundation in five ordered slices: define the memory-context contract; implement bounded context assembly over existing MemoryStore retrieval; define policy for writes/corrections/history/deletion; implement a controlled retrieve-before-model and evaluate-after-response loop; and add deterministic simulated-conversation scenarios.

## Delivered

- Context pack has current-query, profile/preference, and active-goal retrieval lanes, deduplication, approximate token-budget enforcement, and untrusted-data framing.
- Retrieved open-ended facts with different values for the same entity/attribute are surfaced as explicit conflicts. The system does not silently resolve them.
- Policy decisions require verbatim user-message evidence for write/correction proposals, explicit correction language for corrections, explicit history intent for history reads, and explicit forget/delete intent plus a target for deletion.
- Controlled turn loop calls retrieval before the model callback and evaluates proposals after the response. It never directly executes a memory mutation.
- Existing REST and MCP adapters and all nine MCP tool names remain unchanged.
- Focused tests and a deterministic simulation harness have been added.
- Documentation, project status, decision log, debug log, and package exports have been updated.

## Validation

**Not run by instruction.** No tests, compilation, REST/MCP smoke checks, or simulation results are claimed. Run the validation sequence in PHASE9_STEP1_REPORT.md after implementation is frozen.

## Limitations

- Profile and goal retrieval are explicit query prompts because the frozen schema has no dedicated profile or goal record types.
- Token use is estimated at four characters per token.
- Conflict detection is conservative and only flags multiple retrieved open-ended facts with the same entity and attribute.
- Eligible proposals are not authorization. A host must still use existing authenticated tools and core guards.
