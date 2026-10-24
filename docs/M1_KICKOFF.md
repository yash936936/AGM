# AGM M1 kickoff: active memory turn lifecycle

## Objective

Move AGM from a durable memory store to an explicit memory lifecycle that an assistant can invoke consistently before, during, and after a turn.

## M1 workstreams

1. **Pre-turn context assembly** — retrieve tenant/project-scoped profile, active goals, preferences, and facts relevant to the current request; carry provenance and trust metadata; avoid stale/current ambiguity.
2. **In-turn evidence contract** — provide a bounded, clearly marked memory context with source IDs, current/history distinctions, and abstention when evidence is insufficient. Retrieved content remains untrusted data, never instructions.
3. **Post-turn write planning** — extract candidate memories from a completed turn, classify fact/preference/goal/episode, identify corrections and expiry, and require policy checks before persistence. The host remains responsible for candidate extraction, user intent/consent, and executing mutations through authenticated tools.
4. **Lifecycle policies** — handle correction, supersession, deletion, retention/expiry, and writer revocation consistently across the lifecycle. The evaluation harness supports actual correction, deletion and writer-revocation operations followed by close/reopen, rebuild_views(), and a final retrieval query. Separate store acceptance tests remain required for other lifecycle invariants.
5. **Evaluation and observability** — run the JSONL benchmark harness (scripts/evaluate_real_history.py) on a consented, de-identified held-out set; report aggregate recall, stale/forbidden-value leaks, abstention, and latency without exposing raw cases. Evaluator thresholds must be reviewed and frozen before looking at held-out results.
6. **Integration contract** — expose the lifecycle API (src/agm/lifecycle.py) for before_turn and after_turn, as well as the active-memory context builder (prepare_turn_context) and controlled turn loop; keep provider-specific model adapters optional.

## Initial implementation boundary

The evaluation harness and lifecycle helpers do not automatically extract memories with an LLM, grant authorization, or decide consent. Real writes in benchmark cases are explicitly described JSONL operations and always pass through MemoryStore's guarded methods. No eligible real-history dataset has been supplied, so no real-history result is claimed.

## Definition of done for M1

- [x] Public lifecycle and active-memory APIs with typed request/response contracts are present on the completion branch.
- [x] Pre-turn retrieval is tenant/project scoped and provenance preserving through the existing MemoryStore retrieval API.
- [x] Retrieved text is marked untrusted; context is bounded and explicit conflict notices are surfaced.
- [x] Post-turn proposal policy is conservative; eligible proposals do not themselves authorize a write/delete.
- [x] Evaluator can execute and test correction, hard deletion, and writer revocation through actual store operations, then reopen, replay, and query to verify current/stale and forbidden-value behavior.
- [ ] Expiry/retention policy has an explicit implemented operation and acceptance test (current decay lifecycle remains read-only dry-run).
- [ ] Unit and integration tests pass on Python 3.11, 3.12, 3.13 for the final branch tree and full debug.md procedure passes on Windows.
- [ ] Consented de-identified held-out benchmark meets thresholds preregistered before evaluation.
- [ ] Security/privacy review signs off on retention, deletion, and export boundaries.

## Required real-history dataset protocol

- Keep the dataset outside Git and CI artifacts.
- Freeze a train/tune split separately from the held-out evaluation set.
- Use opaque case IDs and de-identify entity names and unique details.
- Each JSONL row contains memories, a query, expected_values, optional forbidden_values, optional expect_abstain, optional scenario, and optional operations.
- Supported operation forms are correction (target memory index, replacement fact and reason), delete (target memory index), and revoke_writer (writer ID). Operation contexts must use the same authenticated tenant/project scope relevant to the test.
- Establish and record thresholds before examining held-out results. Tenant-isolation, deletion, and revocation cases have zero-tolerance forbidden-value requirements.
- Save only aggregate reports, dataset hash/version, evaluator version, commit SHA, environment, and reviewer sign-off.
