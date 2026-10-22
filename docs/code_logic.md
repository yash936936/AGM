# Code logic — AGM prototype

## Supersession and contested writes
**Where:** `src/agm/store.py` (write path)
**What it does:** For a single-valued fact on the same (tenant, entity, attribute):
1. Same value as current → NOOP. If a *different writer* with an independent source sends it, bump corroboration; same writer repeating never corroborates (v5: no error laundering).
2. Different value and `valid_from` ≥ current's → SUPERSEDE: old node gets `valid_to` and status `superseded`, a `supersedes` edge is added.
3. If `base_version` is given and differs from the current version → CONTESTED: both stay active, linked by a `contests` edge, both returned with a warning.
4. If the existing fact's tier outranks the new writer's by 2+ levels → CONTESTED, not overwritten.
Multi-valued facts (`multi_valued=True`) just ADD.
**Why it's non-obvious:** the trust gap rule and the "same writer never corroborates" rule are
easy to forget and both exist to stop one bad source from rewriting memory or inflating confidence.

## Retrieval: seed, expand, rank, abstain
**Where:** `src/agm/retrieve.py`
**What it does:** Seed = FTS5 BM25 and cosine similarity, normalised and blended 0.5/0.5, with filters (tenant, project, entity, as_of, status). Expansion (only when `expand=True`): for entities in the seed set, add their current facts and 1-hop `relates` neighbours, capped (fan-out 10, hub cap 50, hops ≤ 2). Rank with D-008 weights. If the top score is under 0.25, widen once (k×2, include archived), then abstain.
**Why it's non-obvious:** `expand=False` must equal the flat baseline byte for byte (D-006). Validity filtering applies to expanded items too, or stale facts sneak back in through the graph.

## Redaction and quarantine
**Where:** `src/agm/guard.py`
**What it does:** Regexes replace key-like and token-like strings with `[REDACTED]` before the event is written, so the raw secret is never in the log or an embedding. Instruction-like text ("ignore previous instructions", "you must now…") sets status `quarantined`: stored, not retrievable unless `include_quarantined` is requested by an admin scope.
**Why it's non-obvious:** redaction must happen before the event append, not after, or the secret lives in the log forever.

## Handoff assembly
**Where:** `src/agm/handoff.py`
**What it does:** Builds context in fixed order (pinned → task state → retrieved memory by score) and stops adding sections when the estimated token budget is hit; task state is never truncated before retrieved memory. Readback compares the new model's goal, decisions and open items to the packet by embedding similarity (threshold 0.6, proposed, v5 D10 open) and lists what is missing.
**Why it's non-obvious:** readback measures what the model says it understood, not how it will behave. Report fidelity as "X of Y items matched", never as "seamless".

---
**Next:** Return to [`context.md`](../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
