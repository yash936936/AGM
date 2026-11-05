# R2: noisy, paraphrased, labelled benchmark (v3) — results

**Status:** synthetic smoke result, 2026-11-02. Evidence about this generator only; not evidence for H1–H7 (D-007). Raw numbers: `r2_labelled_v3_results.json`. Reproduce: `python eval/labelled_v3.py --seeds 5 --episodes 1200 [--embedder spacy]` (spaCy needs `pip install spacy` plus the `en_core_web_md` wheel).

## Design

226 queries per seed × 5 seeds. Eight families: single (paraphrased), stale, temporal, multi_hop, hard_neg (near-duplicate `-staging`/`-legacy` siblings), poison (low-trust conflicting claim), injection (instruction-like text), unanswerable (unknown entity, or known entity with the attribute never recorded). 1,200 distractor notes. Stored wording and query wording differ. Four systems: `bm25` (lifecycle- and trust-blind keyword search over everything ever written), `flat`, `flat_iterative` (agent-style repeated flat retrieval, up to 8 calls), `graph` (expansion on, 2 hops). Two regimes: **no-hint** (query text only) and **hint** (entity supplied). k = 5. Scoring is by (entity, attribute, value).

**Pre-registered rule** (written in `eval/labelled_v3.py` before any v3 result was seen): graph is justified only if it beats the best other system by ≥ 0.05 strict pass rate with a paired-bootstrap 95% CI above zero; "efficiency only" if within 0.02 and fewer retrieve calls than the iterative baseline.

**Transparency:** a smoke run (1 seed) showed my first scoring ignored the entity, so values shared by other entities inflated hits and leaks; I fixed scoring to be entity-aware before the registered runs. A secondary "unflagged leak" column was added after I understood the contested-fact behaviour (below). Neither changed the generator or the rule.

## Result (pooled strict pass rate over the six answerable families)

| Embedder | Regime | bm25 | flat | flat_iterative | graph | graph − best other (95% CI) | Verdict |
|---|---|---:|---:|---:|---:|---|---|
| hash | no-hint | 0.238 | 0.595 | 0.697 | 0.648 | −0.050 [−0.072, −0.026] | **NOT JUSTIFIED** |
| hash | hint | 0.238 | 0.838 | 0.939 | 0.776 | −0.163 [−0.175, −0.150] | **NOT JUSTIFIED** |
| spaCy vectors | no-hint | 0.238 | 0.353 | 0.589 | 0.488 | −0.102 [−0.138, −0.062] | **NOT JUSTIFIED** |
| spaCy vectors | hint | 0.238 | 0.838 | 0.955 | 0.776 | −0.178 [−0.191, −0.167] | **NOT JUSTIFIED** |

Cost (no-hint, hash): graph 1 retrieve call, ~34 ms median; flat_iterative ~7 calls, ~38 ms; flat 1 call, ~11 ms.

Where graph wins or loses (no-hint): **multi_hop** graph 0.51 vs iterative 0.37 (hash) / 0.21 (spaCy) vs flat 0.01–0.03 — the one family where graph clearly helps. **hard_neg** graph 0.36/0.31 vs ≤ 0.31/0.17. Graph loses on **poison** (0.54/0.17 vs iterative 0.89) and **single** with spaCy (0.51 vs 0.73).

## What the benchmark found in the core (worth fixing regardless of the graph question)

1. **Graph and flat disagree on contested facts.** A low-trust claim that conflicts with a trusted fact becomes `contested`. Flat retrieval silently omits it; graph expansion returns it with `contested_with` set. `docs/code_logic.md` says both are returned with a warning, so flat is the odd one out. Under strict scoring graph "leaks" 26–40% on poison; counting only *unflagged* leaks, all three AGM modes are within 4–10% and the hint regime is 0%. Decide which behaviour is intended and make both modes match.
2. **An entity hint plus expansion disables expansion.** The hint scopes eligible rows to that entity, so graph cannot reach linked entities (multi_hop 0.000 in the hint regime). Agents and the CLI should not pass `--entity` on relational questions, or the hint should scope only the seeds.
3. **Abstention almost never fires on realistic names.** Unanswerable correctness is 0–1% in every mode without a hint, and a known entity with a never-recorded attribute is answered with that entity's other facts. Words shared between the query and unrelated memories clear the similarity threshold. This is a hallucination risk for agents.
4. **Sibling entities leak into each other.** Without a hint, 30–70% of near-duplicate-name queries (`x` vs `x-staging`) return the sibling's value in the top 5 for every system, which a downstream agent must disambiguate by the entity field.
5 (good news). **Injection-style text never surfaced** (1.000 in every mode), and temporal as-of queries are correct (1.000 with entity-aware scoring).

## Limits

One hand-designed generator; k = 5 and strict scoring (any forbidden item in the top 5 fails the query); the iterative baseline uses a known entity catalogue and up to 8 calls, which a real agent would need NER or a model to emulate; the spaCy vectors are static word vectors, weaker than a sentence-transformer; a single seed batch of 5 runs per embedder.

## What it means for the decision

On this benchmark graph expansion does not justify itself: it matches or trails an agent-style flat baseline, wins only multi-hop, and brings extra behaviours (contested surfacing, hint interaction) that need fixing. The roadmap's stop rule therefore points toward making graph expansion **optional** and spending effort on items 1–4 above. Treat this as a strong prompt to test on real data (`docs/acceptance/real_history_local_runbook.md`) before deciding, not as a final verdict.


## Addendum (2026-11-03): after D-046 (contested handling unified)

Same generator, seeds, rule and queries; only the core changed (flat and graph both withhold contested candidates by default, D-046). Raw numbers: `r2_labelled_v3_after_d046.json`. The first run above is kept as the baseline for this comparison.

| Embedder | Regime | graph before | graph after | best other (iterative) | graph − best (95% CI) | Verdict before → after |
|---|---|---:|---:|---:|---|---|
| hash | no-hint | 0.648 | **0.688** | 0.697 | −0.010 [−0.037, +0.019] | NOT JUSTIFIED → **EFFICIENCY ONLY** |
| hash | hint | 0.776 | 0.838 | 0.939 | −0.102 | NOT JUSTIFIED → NOT JUSTIFIED |
| spaCy | no-hint | 0.488 | **0.528** | 0.589 | −0.062 [−0.094, −0.021] | NOT JUSTIFIED → NOT JUSTIFIED |
| spaCy | hint | 0.776 | 0.838 | 0.955 | −0.117 | NOT JUSTIFIED → NOT JUSTIFIED |

Poison family, graph strict pass: 0.54 → 0.81 (hash) and 0.17 → 0.43 (spaCy); its leak rate is now 0%. In the hint regime graph now equals flat everywhere except multi_hop (0.000, because the hint still blocks expansion: R2.6b).

How to read it: the fix removes a real inconsistency, and it is the only change. Under the hash embedder graph is now statistically level with the best baseline (the CI includes zero) while using 1 retrieve call instead of about 7, which the pre-registered rule labels "efficiency only". That is not a win on accuracy: graph still does not beat the agent-style iterative baseline, and with the spaCy embedder it remains behind (paraphrase handling, not graph, is the limiting factor there). The rule was applied unchanged, but the verdict flip came from a core fix made *after* seeing the first results, so treat it as "the earlier gap was partly a defect", not as confirmation of the graph hypothesis.


## Addendum 2 (2026-11-04): after D-047 (entity hint no longer blocks expansion)

Same generator, seeds, rule and queries; only `graph_retrieve` changed. Raw numbers: `r2_labelled_v3_after_d047.json`. The no-hint regime is unchanged (±0.001, timestamp noise); the hint regime:

| Embedder | graph pooled before → after | multi_hop (graph) before → after | best other (iterative) | graph − best (95% CI) | Verdict |
|---|---:|---:|---:|---|---|
| hash | 0.838 → **0.920** | 0.000 → **0.507** | 0.939 | −0.019 [−0.030, −0.008] | not justified → **efficiency only** |
| spaCy | 0.838 → **0.925** | 0.000 → **0.540** | 0.955 | −0.029 [−0.036, −0.022] | not justified → not justified |

All other families in the hint regime are unchanged (single, stale, temporal, hard_neg, poison at 1.000 with 0% leaks).

**A second finding, found while explaining the remaining multi-hop gap.** With a hint, graph answers 15/15 two-hop questions and 0/15 one-hop questions (seed 0). The hint was never the whole story: graph follows outgoing relation edges only when the query contains words from a fixed list (`dependent`, `dependency`, `dependencies`, `downstream`, `reachable`). The one-hop wording "depends on" does not match, so those questions never follow the relation, with or without a hint. This is roadmap item R2.6e. The fix must be validated on held-out phrasings, not on the wording of this benchmark, or the result would be overfitted.


## Addendum 3 (2026-11-05): after D-048 (relation-following no longer depends on wording)

Raw numbers: `r2_labelled_v3_after_d048.json`; held-out check: `r2_relation_heldout.json` (`eval/relation_heldout.py`, phrasing banks and criteria frozen before the change; all met).

**Held-out check (hash embedder, 5 seeds, hit@5):** plain-wording 1-hop 0.000 → 1.000 (no hint) and 0.093 → 1.000 (hint); plain 2-hop 0.027 → 1.000 and 0.080 → 1.000; trigger-word wording unchanged (within 0.013); a non-relational control question still returns the entity's own answer first (top-1 1.000). The linked entity's answer is in the top 5 but never first for plain wordings (top-1 0.000).

**Regression run on the pre-registered v3 benchmark** (rule unchanged; criterion fixed before the run: graph pooled score may not fall by more than 0.01 and leaks may not rise; both held):

| Embedder | Regime | graph D-047 → D-048 | best other (iterative) | graph − best (95% CI) | Verdict |
|---|---|---:|---:|---|---|
| hash | no-hint | 0.687 → **0.778** | 0.697 | +0.081 [+0.058, +0.104] | efficiency only → **GRAPH_JUSTIFIED** |
| hash | hint | 0.920 → **1.000** | 0.939 | +0.061 [+0.049, +0.074] | efficiency only → **GRAPH_JUSTIFIED** |
| spaCy | no-hint | 0.529 → **0.608** | 0.589 | +0.018 [−0.012, +0.062] | not justified → efficiency only |
| spaCy | hint | 0.925 → **1.000** | 0.955 | +0.045 [+0.040, +0.053] | not justified → efficiency only |

Multi-hop is now 1.000 for graph in every regime (it was 0.507/0.540 with a hint, 0.51/0.53 without).

**How much to believe this.** (1) The v3 one-hop questions say "depends on", the very wording the old code mishandled, so the earlier verdicts understated graph because of a defect, not only because of the idea. (2) The embedders disagree: JUSTIFIED with the hash embedder, only efficiency-level with word vectors, so the synthetic evidence cannot decide gate G1. (3) The pooled score weights multi-hop at roughly 18% of the answerable queries because of how I built the generator; a different mix could change the verdict. (4) Graph still trails the iterative baseline on single-fact and stale questions without a hint (for example single 0.827 vs 0.913 with the hash embedder). (5) hit@5 is lenient: for plain-worded relational questions the answer is not ranked first. Real-data results (roadmap R2.4) remain the deciding evidence.
