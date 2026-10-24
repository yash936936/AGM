# AGM Phase 7 Report — Evaluation Diagnosis and Retrieval Optimization

> Status: changes implemented and validated in the available builder snapshot. Reapplication and same-platform validation on the full Windows v0.5.1 checkout are still required.

## Executive summary

Phase 7 investigated three failures from the saved Phase 6 run: zero graph multi-hop accuracy, poor abstention on near-miss service IDs, and expensive graph queries. The changes address each separately. The generated fact histories, relation-chain generator, seed set, corpus size, `k`, common abstention threshold (0.25), bootstrap method, and D-024 verdict rule were preserved. Query wording was made explicit about hop distance; graph mode uses depth two only for the `multi_hop` family. No numerical score threshold was tuned.

- **Multi-hop:** graph answers 20/20 test questions (100%; bootstrap 95% CI 100–100%), compared with 0% for flat and entity-filtered flat. The two flat results are expected limits of non-expanding retrieval with a filter fixed to the source entity; the previous graph failure was due to ambiguous hop phrasing, default one-hop traversal, unrelated seeds, and unsupported/historical edges entering the candidate set.
- **Unknown numeric service IDs:** all three modes abstain correctly on all 20 generated unknown-ID questions each (60 mode/query observations across five seeds). The store now uses exact catalogue identity for known numeric-ID namespaces instead of trusting fuzzy text similarity for entity identity.
- **Graph performance:** in the builder environment, graph overall p50 improved from 781.12 ms to 94.43 ms (87.9% lower) and p95 from 1,354.24 ms to 124.88 ms (90.8% lower) when comparing the saved Phase 6 and Phase 7 runs from that environment. Mean expanded nodes fell from 18.85 to 7.075 (62.5% lower). These timings are not a same-platform verification of the user’s Windows baseline; rerun on that machine before calling D-025’s Windows latency target accepted.
- **Overall accuracy:** graph rose from 74.0% [71.39, 76.40] to 94.2% [91.39, 96.80] on this synthetic evaluation, with stale-error still 0%. D-024’s overall verdict remains `graph not shown to help in this smoke test`: the preregistered rule also requires improvement on the stale family, which is already at a 100% ceiling and is labelled NOT SHOWN.

## 1. Investigation and fixes

### 1.1 Multi-hop accuracy: evaluator/request mismatch plus graph traversal issues

**Observed failure.** Phase 6 generated 1- and 2-edge questions with wording that did not say which distance was intended; the evaluation called graph retrieval with its default one-hop depth. A directed query also relied on broad retrieval seeds, so a predecessor/dependent service could be introduced before expansion, and a global top-hit seed pool could reintroduce unrelated candidates. Finally, the SQL fan-out limit was applied before eligibility filtering, which meant superseded relation-support rows could occupy the limit and crowd out the current target row.

**Fix.** Query text now says “exactly 1 dependency hop” or “exactly 2 dependency hops”. The graph evaluation requests `graph_hops=2` for multi-hop questions only; the graph implementation’s default remains one hop for all other families. Directed downstream questions anchor traversal to the exact entity mentioned in the query, follow outgoing relation edges only when backed by eligible relation facts, and prioritize the requested answer attribute at the intended path depth. Candidate eligibility is checked before applying the result cap. Flat and `flat_filter` remain unchanged as baselines.

**Result.** Multi-hop graph accuracy improved from 0/20 (0%, 95% CI 0–0) to 20/20 (100%, CI 100–100). One-hop and two-hop synthetic regressions exercise exact depth and ensure superseded edges are not followed.

### 1.2 Abstention: unknown IDs need identity checks, not a tuned similarity cutoff

**Observed failure.** Queries for catalogue-like unknown service IDs (for example `svc-012`, `svc-200`, `svc-201`, `svc-202`) contained common terms such as `runtime`, `owner`, and `svc`, so the fuzzy retriever returned plausible-looking but unrelated memories. The Phase 6 `flat` and `graph` results consequently failed the unanswerable family even though `flat_filter` happened to return no eligible candidates.

**Fix.** Before retrieval, if the tenant/project catalogue contains a numeric-ID namespace such as `svc-`, a query naming an exact unknown/near-miss identifier in that known namespace abstains instead of being treated as fuzzy text. The exact identifier must match a canonical entity or alias. Flat entity-filtered retrieval also abstains when its explicit entity filter yields no eligible candidate rows. The common evaluation threshold remains **0.25**; no threshold was adjusted.

**Result.** All 20 unknown-ID cases per mode are correctly abstained upon (all three modes 100% abstention correctness, 60/60 observations across modes). All three modes have 100% abstention correctness for the `unanswerable` family. This is limited to catalogue-backed numeric-ID namespaces; it is not a general calibrated confidence model.

### 1.3 Graph latency: batch corroboration lookups and bound candidate traversal

**Profile before changes.** On a representative directed graph query against the 200-entity/2,000-episode store, cProfile reported about 0.96 s and 789 calls to `sqlite3.Connection.execute`; `independent_corroborations()` was called 214 times and took about 0.72 s cumulatively. Corroboration was therefore a measurable repeated-SQL bottleneck, not merely a visually suspicious graph loop.

**Fix.** Graph retrieval now batches independent corroboration counts and reuses those values in confidence and decay calculations. Directed searches avoid the global top-50 seed pool, begin at the explicitly named source entity, and traverse eligible relation support. Fan-out is capped after eligibility filtering. Exact metadata/attribute intent is used for directed answer-slot ordering; the shared abstention threshold is unchanged.

**After profile.** A representative query with the same seeded corpus measured about 239 ms in the builder profile; the per-row corroboration helper no longer appears as a leading cumulative-time hotspot. This single-query profile is diagnostic and distinct from the five-seed latency summary below.

## 2. Phase 6 versus Phase 7 — overall metrics

Phase 6 and Phase 7 below are the two saved five-seed runs in the same builder environment. The 95% intervals are deterministic bootstraps over seed-level means. They are not cross-machine comparisons.

| Mode | Accuracy@k, Phase 6 → 7 | Stale error, Phase 6 → 7 | Abstention correctness, Phase 6 → 7 | p50 ms, Phase 6 → 7 | p95 ms, Phase 6 → 7 | Mean expanded, Phase 6 → 7 |
|---|---:|---:|---:|---:|---:|---:|
| `flat` | 67.6% [67.2, 68.0] → 67.6% [67.2, 68.0] | 0.0% [0.0, 0.0] → 0.0% [0.0, 0.0] | 83.3% [83.3, 83.3] → 100.0% [100.0, 100.0] | 53.03 [47.64, 61.42] → 43.60 [42.72, 44.53] | 76.34 [61.74, 91.18] → 52.24 [49.51, 54.92] | 0.00 → 0.000 |
| `flat_filter` | 80.0% [80.0, 80.0] → 80.0% [80.0, 80.0] | 0.0% [0.0, 0.0] → 0.0% [0.0, 0.0] | 100.0% [100.0, 100.0] → 100.0% [100.0, 100.0] | 22.55 [19.58, 25.94] → 20.98 [20.12, 21.84] | 31.94 [26.39, 37.21] → 27.44 [25.17, 30.06] | 0.00 → 0.000 |
| `graph` | 74.0% [71.4, 76.4] → 94.2% [91.4, 96.8] | 0.0% [0.0, 0.0] → 0.0% [0.0, 0.0] | 82.5% [80.8, 83.3] → 99.2% [97.5, 100.0] | 781.12 [735.28, 817.36] → 94.43 [90.97, 97.44] | 1354.24 [1035.67, 1827.68] → 124.88 [112.18, 137.67] | 18.85 → 7.075 |

Overall graph p50 fell by 87.9% and p95 by 90.8% relative to the Phase 6 builder result. Its accuracy gain is +20.2 percentage points. The flat modes also became faster in this builder run, so report the saved figures rather than attributing every timing change to graph-only code.

## 3. Phase 7 metrics by family and mode

Accuracy is not defined (`n/a`) for unanswerable questions. Stale-error is only defined for the stale family. Intervals shown are bootstrap 95% CIs over five seed-level means. `store abst.` is the store’s own abstain flag; `harness abst.` is D-024’s shared evaluation rule.

| Family | Mode | Accuracy@k (95% CI) | Stale-error | Abstention correctness (95% CI) | Store abst. | Harness abst. | p50 ms | p95 ms | Mean expanded |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `single_fact` | `flat` | 100.0% [100.0, 100.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 44.54 | 58.89 | 0.00 |
| `single_fact` | `flat_filter` | 100.0% [100.0, 100.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 21.06 | 23.99 | 0.00 |
| `single_fact` | `graph` | 100.0% [100.0, 100.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 97.84 | 104.23 | 10.00 |
| `stale` | `flat` | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 43.87 | 57.18 | 0.00 |
| `stale` | `flat_filter` | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 21.97 | 32.34 | 0.00 |
| `stale` | `graph` | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 102.35 | 137.40 | 10.00 |
| `entity_centric` | `flat` | 38.0% [36.0, 40.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 42.99 | 46.80 | 0.00 |
| `entity_centric` | `flat_filter` | 100.0% [100.0, 100.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 21.73 | 24.22 | 0.00 |
| `entity_centric` | `graph` | 91.0% [88.0, 94.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 95.08 | 109.15 | 10.00 |
| `multi_hop` | `flat` | 0.0% [0.0, 0.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 43.81 | 46.35 | 0.00 |
| `multi_hop` | `flat_filter` | 0.0% [0.0, 0.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 23.16 | 25.31 | 0.00 |
| `multi_hop` | `graph` | 100.0% [100.0, 100.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 101.64 | 122.15 | 10.00 |
| `temporal` | `flat` | 100.0% [100.0, 100.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 47.43 | 53.09 | 0.00 |
| `temporal` | `flat_filter` | 100.0% [100.0, 100.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 21.47 | 27.05 | 0.00 |
| `temporal` | `graph` | 80.0% [65.0, 95.0] | n/a | 95.0% [85.0, 100.0] | 5.0% [0.0, 15.0] | 5.0% [0.0, 15.0] | 70.25 | 82.47 | 2.45 |
| `unanswerable` | `flat` | n/a | n/a | 100.0% [100.0, 100.0] | 100.0% [100.0, 100.0] | 100.0% [100.0, 100.0] | 1.93 | 3.03 | 0.00 |
| `unanswerable` | `flat_filter` | n/a | n/a | 100.0% [100.0, 100.0] | 100.0% [100.0, 100.0] | 100.0% [100.0, 100.0] | 1.78 | 2.47 | 0.00 |
| `unanswerable` | `graph` | n/a | n/a | 100.0% [100.0, 100.0] | 100.0% [100.0, 100.0] | 100.0% [100.0, 100.0] | 1.90 | 2.65 | 0.00 |

### Interpretation

- `single_fact` and `stale` remain at the ceiling; these families cannot show positive accuracy lift. Stale-error remains 0% in all modes.
- `entity_centric` graph recall is 91.0% [88.0, 94.0], but `flat_filter` is 100%; D-024 properly keeps the family verdict **FLAT BETTER**.
- `multi_hop` graph accuracy is 100% [100, 100] and is labelled **PROMISING** in the pairwise family rule because it beats both baselines by at least 5 percentage points with the paired bootstrap CIs above zero. Flat modes score 0% on this downstream question because they do not expand to the target entity.
- `temporal` graph accuracy remains 80.0% [65.0, 95.0] versus 100% for flat and filtered-flat, and is labelled **FLAT BETTER**. Graph correctly abstains on 5% of temporal cases where the baselines return an answer; this remains a trade-off to investigate, not a reason to alter the threshold.
- `unanswerable` accuracy is n/a; the correct metric is abstention correctness, now 100% for all modes.
- The official overall decision summary is still `graph not shown to help in this smoke test`, because D-024 requires the preregistered paired improvement on both `multi_hop` and `stale`; the stale family is at ceiling and NOT SHOWN.

## 4. D-025 target status

| Pre-registered target | Outcome | Status |
|---|---|---|
| Graph multi-hop accuracy ≥90% | 100% (20/20) in the builder run | **Met in builder snapshot** |
| Correct abstention on generated unknown numeric service IDs in every mode | 60/60 mode/query observations correct across five seeds | **Met in builder snapshot** |
| Graph p50 at least 50% below the saved Windows Phase 6 1,370 ms baseline, and p95 below 1,000 ms on same configuration/platform | Builder p50 94.43 ms [90.97, 97.44], p95 124.88 ms [112.18, 137.67]; not run on the same Windows environment yet | **Pending same-platform verification** |

Do not claim the Windows latency target is fully accepted until the Phase 7 patch is applied to the actual Windows v0.5.1 checkout and the five-seed run is repeated there. The builder figures are evidence of improvement in that environment only.

## 5. Decision integrity and scope

- `eval/synthetic_v2.py` retains the generated fact histories, relation chains, seeds 0–4, 200 entities, 2,000 episodes per seed, `k=8`, hash embedder, 1,000 bootstrap resamples, and the shared 0.25 abstention threshold. The only query-generation change is making generated hop distance explicit; graph evaluation requests depth two only for `multi_hop`.
- D-024’s predeclared decision rule and saved Phase 6 JSON remain unchanged. The Phase 7 run is saved as a new timestamped result.
- D-021, D-022, and D-023 have not been modified. D-025 records the diagnostic corrections and pre-rerun targets.
- The original `eval/stale_facts.py` remains intact. The REST smoke cleanup fix from the user’s Windows verification is outside this diagnostic patch.
- **D-007 caveat:** a seeded synthetic smoke evaluation is not evidence for or against AGM hypotheses H1–H7; the hash embedder and hand-authored synthetic workload are limited.

## 6. Validation and reproduction

Run from the actual v0.5.1 checkout after applying `PHASE7_PATCH.diff`:

```bash
git diff --check
python -m compileall -q src tests eval
python -m pytest -q
python eval/stale_facts.py
python eval/synthetic_v2.py --entities 200 --episodes 2000 --seeds 5 --k 8 --embedder hash
python examples/mcp_smoke_client.py
python examples/rest_smoke_client.py
python scripts/pack.py
```

**Builder validation:** `PYTHONPATH=src python -m pytest -q` passed 72 tests with 1 skipped. The skip was `tests/test_mcp_stdio.py` because the MCP SDK is unavailable in the builder environment. `compileall` passed. This builder workspace came from an older Phase 5 snapshot plus the Phase 6 overlay, not the actual complete v0.5.1 checkout, so this is not a substitute for the user’s Windows full-suite rerun. The user’s last pre-Phase-7 Windows run passed 104 tests, and the REST client reported 11/11 after its shutdown fix.

## Artifacts

- Phase 6 baseline: `eval/results/20261023T155826.716282Z.json`
- Phase 7 results and query-level traces: `eval/results/20261023T184404.879694Z.json`
- Pre-registered diagnostic targets and scope: `docs/decisions.md` (D-025)
- Focused regression tests: `tests/test_retrieve.py`, `tests/test_eval_v2.py`
