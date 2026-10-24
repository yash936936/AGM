# Phase 9 Report: Active Memory Context and Turn Control

## Delivered

- Current-query, profile/preference, and active-goal retrieval lanes.
- Deduplication, approximate token-budget enforcement, and untrusted-data framing.
- Explicit conflict notices for different open-ended values of the same entity/attribute.
- Conservative policy for write, correction, history, and deletion proposals.
- Controlled retrieval-before-model and policy-after-response loop, without automatic mutation.
- M1 lifecycle API with typed before-turn request/response and bounded guarded after-turn write contract.
- Hardened JSONL retrieval evaluator with named scenario coverage, configurable thresholds, zero-tolerance leak scenarios, and aggregate-only reports.
- Negative evaluator regression tests for missing required values, forbidden-value leaks, wrong abstention, invalid fixtures, duplicates, and tenant isolation.
- Existing REST/MCP adapters and all nine MCP tool names remain unchanged.

## Validation

**GitHub Actions:** Run [40124411342](https://github.com/yash936936/AGM/actions/runs/40124411342), commit `768fec32dd10e7a21ff5c055384ebea5a1b44fae`, passed the test suite, repository hygiene scan, and patch whitespace check on Python 3.11, 3.12, and 3.13. Logs: Python 3.11 — `168 passed, 1 warning in 11.60s`; Python 3.12 — `168 passed, 1 warning in 11.73s`; Python 3.13 — `168 passed, 1 warning in 17.60s`. The warning is the Starlette/httpx TestClient deprecation.

The public workflow tests on this branch are the available automated CI evidence. Local Windows full-suite verification, both smoke clients, the deterministic active-memory simulation, compile checks and packaging are **NOT RUN in this execution environment** and remain required by the repository workflow.

## Limitations and open gates

- Profile and goal retrieval use caller-supplied prompts because the frozen schema has no dedicated profile/goal types.
- Token use is estimated at four characters per token.
- Conflict detection is conservative.
- Eligible proposals are recommendations only; they do not authorize mutations.
- The real-history evaluator checks retrieval results. Scenario labels do not themselves execute correction, deletion, or writer-revocation operations. Dedicated end-to-end lifecycle tests for those paths remain open.
- The default evaluator thresholds are provisional operational defaults and must be reviewed/frozen before any held-out run.
- No consented, de-identified held-out real-history dataset was supplied; real-history evaluation is **NOT RUN**.
- Production security/privacy review is **NOT ESTABLISHED**.
- No ZIP is being produced until these open implementation and target-environment regression gates are completed.
