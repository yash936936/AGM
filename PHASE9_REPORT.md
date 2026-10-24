# Phase 9 Report: Active Memory Context and Turn Control

## Delivered

- Current-query, profile/preference, and active-goal retrieval lanes.
- Deduplication, approximate token-budget enforcement, and untrusted-data framing.
- Explicit conflict notices for different open-ended values of the same entity/attribute.
- Conservative policy for write, correction, history, and deletion proposals.
- Controlled retrieval-before-model and policy-after-response loop, without automatic mutation.
- M1 lifecycle API with typed before-turn request/response and bounded guarded after-turn write contract.
- Hardened JSONL evaluator with named scenarios, configurable pass-rate/recall/abstention thresholds, zero-tolerance leak rules, and aggregate-only reports.
- Evaluator operations that actually execute fact correction, hard deletion, and writer revocation through MemoryStore; each path then closes/reopens, rebuilds event-sourced views, and checks retrieval results.
- Negative evaluator tests for missing values, forbidden leaks, wrong abstention, malformed fixtures, duplicates, zero-tolerance sentinel requirements, and tenant isolation.
- Existing REST/MCP adapters and all nine MCP tool names remain unchanged.

## Validation

Latest code/test CI run: [40124787565](https://github.com/yash936936/AGM/actions/runs/40124787565), commit `20ea048a887ad9b31a36a7615ac12f841cdfea01`. Python 3.11: `171 passed, 1 warning in 9.46s`; Python 3.12: `171 passed, 1 warning in 13.68s`; Python 3.13: `171 passed, 1 warning in 15.78s`. Repository hygiene and patch whitespace steps also passed in each job. The warning is the Starlette/httpx TestClient deprecation.

This report and subsequent documentation-only updates require one final CI run against the final branch head. Local Windows full-suite verification, both smoke clients, the deterministic active-memory simulation, compile checks and packaging are **NOT RUN in this execution environment** and remain required by the repository workflow.

## Limitations and open gates

- Profile and goal retrieval use caller-supplied prompts because the frozen schema has no dedicated profile/goal types.
- Token use is estimated at four characters per token.
- Conflict detection is conservative.
- Eligible proposals are recommendations only; they do not authorize mutations.
- The implemented decay lifecycle is a read-only dry run; an explicit expiry/retention operation and acceptance policy remain open.
- The default evaluator thresholds are operational defaults, not empirically validated production thresholds. They must be reviewed and preregistered before held-out evaluation.
- No consented, de-identified held-out real-history dataset was supplied; real-history evaluation is **NOT RUN**.
- Production security/privacy review is **NOT ESTABLISHED**.
- No ZIP is being produced until all implementation and target-environment regression gates are complete.
