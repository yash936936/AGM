# AGM M1 kickoff: active memory turn lifecycle

## Objective

Move AGM from a durable memory store to an explicit memory lifecycle that an assistant can invoke consistently before, during, and after a turn.

## M1 workstreams

1. **Pre-turn context assembly** — retrieve tenant/project-scoped profile, active goals, preferences, and facts relevant to the current request; carry provenance and trust metadata; avoid stale/current ambiguity.
2. **In-turn evidence contract** — provide a bounded, clearly marked memory context with source IDs, current/history distinctions, and abstention when evidence is insufficient. Retrieved content remains untrusted data, never instructions.
3. **Post-turn write planning** — extract candidate memories from a completed turn, classify fact/preference/goal/episode, identify corrections and expiry, and require policy checks before persistence.
4. **Lifecycle policies** — handle correction, supersession, deletion, retention/expiry, and writer revocation consistently across the lifecycle.
5. **Evaluation and observability** — run the JSONL benchmark harness (`scripts/evaluate_real_history.py`) on a consented, de-identified held-out set; report aggregate recall, stale/forbidden-value leaks, abstention, and latency without exposing raw cases.
6. **Integration contract** — expose a stable service API for `before_turn`, `prepare_turn_context`, and `after_turn`; keep provider-specific model adapters optional.

## Initial implementation boundary

This starter overlay implements the evaluation harness and a machine-readable benchmark contract. It does **not** claim to have run a real-history evaluation: no consented dataset was provided. It does not ingest raw personal histories, contact an external model provider, or alter production data.

## Definition of done for M1

- [ ] Public lifecycle API and typed request/response contracts.
- [ ] Pre-turn retrieval is tenant/project scoped and provenance preserving.
- [ ] Corrections do not appear as current facts; historical lookup remains explicit.
- [ ] Post-turn writes are guarded, idempotent, and policy checked.
- [ ] Delete/revoke/expiry policies are tested across restart/replay.
- [ ] Unit and integration tests pass on Python 3.11, 3.12, 3.13.
- [ ] Consented de-identified held-out benchmark meets preregistered thresholds.
- [ ] Security/privacy review signs off on retention, deletion, and export boundaries.

## Required real-history dataset protocol

- Keep the dataset outside Git and CI artifacts.
- Freeze a train/tune split separately from the held-out evaluation set.
- Use opaque case IDs and de-identify entity names and unique details.
- Each JSONL row contains `memories`, a `query`, `expected_values`, optional `forbidden_values`, and optional `expect_abstain`.
- Establish thresholds before examining held-out results. Any forbidden-value leak in tenant-isolation or deletion cases blocks release.
- Save only aggregate reports, dataset hash/version, evaluator version, commit SHA, environment, and reviewer sign-off.
