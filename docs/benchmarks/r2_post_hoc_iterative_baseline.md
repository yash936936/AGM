# R2 post-hoc check: iterative flat retrieval vs graph (synthetic)

**Status:** synthetic smoke result, 2026-11-02, not evidence for H1–H7 (D-007). Hash embedder only (`--embedder st` could not run in the sandbox: no model download). Run on the commit that added `eval/iterative_baseline.py`.

## Why this exists

`eval/synthetic_v2.py` reports one family where graph retrieval beats both of its baselines: **multi_hop** (flat 0.000, flat_filter 0.000, graph 1.000, identical across all 5 seeds). Identical scores on every seed mean the task is solvable only by following stored links, by construction, and that neither baseline is allowed to take a second step. A tool-using agent does take a second step: read the first result, notice the name of the next service, query again. `iterative_baseline.py` adds that baseline. It was added **after** seeing the v2 results (post-hoc); it can only make graph's comparison harder, and `synthetic_v2.py` and its pre-declared decision rule are untouched.

## Reproduce

```bash
python eval/synthetic_v2.py --seeds 5 --entities 200 --episodes 2000
python eval/iterative_baseline.py --seeds 5 --entities 200 --episodes 2000
```

## Result (5 seeds, 200 entities, 2,000 distractor episodes, k = 8)

| Family | flat_filter | flat_iterative | graph | graph − iterative (95% CI) |
|---|---:|---:|---:|---|
| single_fact | 1.000 | 1.000 | 1.000 | +0.000 [0, 0] |
| stale | 1.000 | 1.000 | 1.000 | +0.000 [0, 0] |
| entity_centric | 1.000 | 1.000 | 1.000 | +0.000 [0, 0] |
| **multi_hop** | **0.000** | **1.000** | **1.000** | **+0.000 [0, 0]** |
| temporal | 1.000 | 1.000 | 1.000 | +0.000 [0, 0] |

Cost (median per question, same runs): flat_filter 1 retrieve call, ~11–12 ms; flat_iterative 3 calls (1.35 on temporal), ~34–35 ms; graph 1 call, ~38–57 ms. On the original v2 run, plain `flat` (no entity filter) scored 0.38 on entity_centric against 1.00 for both graph and flat_filter.

## What this does and does not show

- **The multi-hop advantage in v2 disappears once the flat baseline may take a second step.** Graph's remaining edge on this corpus is round trips (1 call vs 3), not accuracy. Whether that matters depends on how costly an extra call is in a real agent loop (network, model turns), which this benchmark does not measure.
- **Latency:** graph is slower per call than a filtered flat call (about 2–5×) in these runs.
- **The baseline is generous in one way:** it scans results for names from a known entity list, which a real agent would need NER or a model to do; and the dependency fact's text names its target here, which real stored text may not. If real facts do not name their linked entities, the graph's explicit relations could matter more than this benchmark suggests. The hit@k metric also ignores extra returned items, which helps any method that returns more.
- **Everything is synthetic and saturated at 1.000**, so these runs cannot separate the methods on the other families. The benchmark has no hard negatives, paraphrased queries or realistic noise.

## What would settle it

Roadmap R2.2–R2.4: a hand-labelled set with paraphrased queries and hard negatives, real embedder, and a consented real-history run. Success criterion to fix **before** running: graph must beat flat_iterative on accuracy by a margin set in advance, or match it with materially fewer calls at acceptable latency. Otherwise simplify (keep event log, trust, lifecycle, handoff; make graph expansion optional).
