# Phase 6 report: synthetic retrieval evaluation v2

## Status

Implemented the Phase 6 evaluation work package on the available Phase 5 package snapshot. `eval/stale_facts.py` remains in place with its existing test unchanged. D-024 was added to `docs/decisions.md` before the default five-seed result was generated and was not changed after inspecting outcomes. D-021 through D-023 were preserved unchanged.

**Main result:** graph was **not shown to help in this smoke test**. The `flat_filter` baseline beat graph overall (80.0% vs 74.0% accuracy@k), graph failed to show gains on either `multi_hop` or `stale`, and graph retrieval had substantially higher latency in this run. These synthetic outputs are not evidence for or against H1–H7.

## Files changed

- `eval/synthetic_v2.py` — deterministic multi-family generator, mode comparison, common harness abstention, bootstrap CIs, verdicts, timestamped JSON output, optional lazy `sentence-transformers` embedder.
- `tests/test_eval_v2.py` — tiny end-to-end config, same-seed stable outcomes/gold manifest, coverage of all families, near-identical stale text, and the two-baseline verdict requirement.
- `eval/results/20261023T155826.716282Z.json` — full default-run query trace, per-seed outputs, metric CIs, configuration and verdicts.
- `docs/decisions.md` — appended D-024 with metric definitions and the pre-declared verdict rule; D-021 to D-023 are unchanged.
- `docs/debug.md` and `docs/status.md` — phase result and next steps.
- `README.md` — Phase 6 evaluation instructions and caveats.
- `scripts/pack.py` — Phase 6 overlay/JSON packaging while preserving exclusions for databases, WAL/SHM files, keys, caches, and Git metadata.
- `PHASE6_REPORT.md` — this report.

## Evaluation configuration

- Command: `PYTHONPATH=src python eval/synthetic_v2.py --entities 200 --episodes 2000 --seeds 5 --k 8 --embedder hash --results-dir eval/results`.
- Seeds: `[0, 1, 2, 3, 4]`; 200 entities; 2,000 distractor episodes per seed; `k=8`; embedder `hash-256-v1`.
- Questions: 24 per seed, 120 query cases across five seeds, six question families, three retrieval modes.
- Modes use the same seeded store and embedder: `flat` (no entity filter, `expand=False`), `flat_filter` (known-entity filter, `expand=False`), `graph` (no entity filter, `expand=True`). Usage counts are reset before each mode.
- The evaluation harness applies the same abstention rule to all modes: no results or top score `< 0.25` means harness abstention. The store’s own `abstain` field is recorded separately.
- Each metric has a 95% bootstrap CI from 1,000 fixed-seed resamples over seed-level means. Accuracy excludes unanswerable cases; entity-centric accuracy is recall of the full gold fact set. All CIs and query-level traces are in the JSON artifact.

## Full family results

Accuracy and rates are shown as mean percentage with 95% CI. Latencies are milliseconds and item/expansion counts are means with CIs. The JSON includes CIs for every metric.

| Family | Mode | Accuracy@k % [95% CI] | Stale-error % [95% CI] | Abstention correctness % [95% CI] | Store abstain % [95% CI] | Eval abstain % [95% CI] | p50 ms [95% CI] | p95 ms [95% CI] | Mean items [95% CI] | Mean expanded [95% CI] |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| single_fact | flat | 100.0% [100.0, 100.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 56.31 [47.30, 71.07] | 93.24 [54.24, 151.41] | 8.00 [8.00, 8.00] | 0.00 [0.00, 0.00] |
| single_fact | flat_filter | 100.0% [100.0, 100.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 25.01 [19.83, 30.29] | 30.35 [22.22, 39.81] | 5.00 [5.00, 5.00] | 0.00 [0.00, 0.00] |
| single_fact | graph | 100.0% [100.0, 100.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 838.83 [780.79, 896.86] | 972.33 [876.93, 1076.44] | 8.00 [8.00, 8.00] | 21.10 [18.35, 23.85] |
| stale | flat | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 54.35 [48.08, 62.72] | 63.87 [51.92, 75.69] | 8.00 [8.00, 8.00] | 0.00 [0.00, 0.00] |
| stale | flat_filter | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 23.21 [19.85, 25.96] | 25.74 [22.09, 29.25] | 5.00 [5.00, 5.00] | 0.00 [0.00, 0.00] |
| stale | graph | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 850.36 [713.14, 1069.55] | 982.69 [785.97, 1231.08] | 8.00 [8.00, 8.00] | 19.90 [16.75, 23.25] |
| entity_centric | flat | 38.0% [36.0, 40.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 53.20 [47.78, 58.31] | 63.79 [52.69, 75.31] | 8.00 [8.00, 8.00] | 0.00 [0.00, 0.00] |
| entity_centric | flat_filter | 100.0% [100.0, 100.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 22.91 [19.76, 26.27] | 26.65 [22.94, 30.23] | 5.00 [5.00, 5.00] | 0.00 [0.00, 0.00] |
| entity_centric | graph | 90.0% [86.0, 94.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 773.03 [729.35, 813.33] | 885.15 [799.41, 976.07] | 8.00 [8.00, 8.00] | 21.35 [18.69, 23.95] |
| multi_hop | flat | 0.0% [0.0, 0.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 49.74 [43.82, 58.62] | 57.02 [50.11, 65.39] | 8.00 [8.00, 8.00] | 0.00 [0.00, 0.00] |
| multi_hop | flat_filter | 0.0% [0.0, 0.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 23.40 [20.35, 26.50] | 41.02 [24.00, 67.38] | 5.00 [5.00, 5.00] | 0.00 [0.00, 0.00] |
| multi_hop | graph | 0.0% [0.0, 0.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 1102.81 [910.06, 1433.21] | 3645.63 [950.97, 8735.87] | 8.00 [8.00, 8.00] | 21.40 [19.85, 22.90] |
| temporal | flat | 100.0% [100.0, 100.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 53.65 [46.98, 63.71] | 59.46 [52.39, 69.23] | 8.00 [8.00, 8.00] | 0.00 [0.00, 0.00] |
| temporal | flat_filter | 100.0% [100.0, 100.0] | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 23.72 [21.08, 27.94] | 31.61 [24.75, 41.16] | 2.20 [1.75, 2.60] | 0.00 [0.00, 0.00] |
| temporal | graph | 80.0% [65.0, 95.0] | n/a | 95.0% [85.0, 100.0] | 5.0% [0.0, 15.0] | 5.0% [0.0, 15.0] | 473.55 [443.17, 496.38] | 533.14 [468.06, 605.54] | 7.60 [6.80, 8.00] | 8.60 [6.95, 10.20] |
| unanswerable | flat | n/a | n/a | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 58.07 [48.72, 69.21] | 76.01 [54.29, 101.85] | 8.00 [8.00, 8.00] | 0.00 [0.00, 0.00] |
| unanswerable | flat_filter | n/a | n/a | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 100.0% [100.0, 100.0] | 1.96 [1.68, 2.30] | 2.88 [1.90, 4.02] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| unanswerable | graph | n/a | n/a | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 777.48 [726.90, 825.27] | 861.17 [815.09, 920.52] | 8.00 [8.00, 8.00] | 20.75 [17.85, 23.86] |

## Overall results

| Mode | Accuracy@k % [95% CI] | Stale-error % [95% CI] | Abstention correctness % [95% CI] | Store abstain % [95% CI] | Eval abstain % [95% CI] | p50 ms [95% CI] | p95 ms [95% CI] | Mean items [95% CI] | Mean expanded [95% CI] |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| flat | 67.6% [67.2, 68.0] | 0.0% [0.0, 0.0] | 83.3% [83.3, 83.3] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 53.03 [47.64, 61.42] | 76.34 [61.74, 91.18] | 8.00 [8.00, 8.00] | 0.00 [0.00, 0.00] |
| flat_filter | 80.0% [80.0, 80.0] | 0.0% [0.0, 0.0] | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | 16.7% [16.7, 16.7] | 22.55 [19.58, 25.94] | 31.94 [26.39, 37.21] | 3.70 [3.62, 3.77] | 0.00 [0.00, 0.00] |
| graph | 74.0% [71.4, 76.4] | 0.0% [0.0, 0.0] | 82.5% [80.8, 83.3] | 0.8% [0.0, 2.5] | 0.8% [0.0, 2.5] | 781.12 [735.28, 817.36] | 1354.24 [1035.67, 1827.68] | 7.93 [7.80, 8.00] | 18.85 [16.93, 20.34] |

## Pre-declared decision rule outcomes

Rule: graph is `PROMISING` on a family only if accuracy beats BOTH flat and flat_filter by at least 5 percentage points, each paired seed-bootstrap 95% CI excludes zero in the positive direction, and graph stale-error rate is not worse. If a baseline has higher accuracy, report `FLAT BETTER`. A pairwise gain is not labelled `PROMISING` when the family fails the other baseline comparison.

| Family | Graph vs flat (mean delta pp, 95% CI) | Graph vs flat_filter (mean delta pp, 95% CI) | Family verdict |
|---|---|---|---|
| single_fact | NOT SHOWN: +0.0 pp [+0.0, +0.0] | NOT SHOWN: +0.0 pp [+0.0, +0.0] | NOT SHOWN |
| stale | NOT SHOWN: +0.0 pp [+0.0, +0.0] | NOT SHOWN: +0.0 pp [+0.0, +0.0] | NOT SHOWN |
| entity_centric | NOT SHOWN: +52.0 pp [+47.0, +57.0] | FLAT BETTER: -10.0 pp [-14.0, -6.0] | FLAT BETTER |
| multi_hop | NOT SHOWN: +0.0 pp [+0.0, +0.0] | NOT SHOWN: +0.0 pp [+0.0, +0.0] | NOT SHOWN |
| temporal | FLAT BETTER: -20.0 pp [-35.0, -5.0] | FLAT BETTER: -20.0 pp [-35.0, -5.0] | FLAT BETTER |
| unanswerable | NOT SHOWN: n/a | NOT SHOWN: n/a | NOT SHOWN |

**Final rule line:** `graph not shown to help in this smoke test`.

Graph improved entity-centric recall from 38% to 90% relative to flat, but `flat_filter` reached 100%, so the family verdict is `FLAT BETTER`. Both flat baselines scored 0% on multi-hop and graph also scored 0%; the run did not demonstrate a multi-hop gain. On stale questions all modes scored 100% with 0% stale error, so graph did not meet the required 5-point improvement. Overall p50/p95 latency was 781.12/1354.24 ms for graph, 53.03/76.34 ms for flat, and 22.55/31.94 ms for flat_filter. These timings are specific to this build environment, not service-level guarantees.

## Commands run and real results

### Passed

`PYTHONPATH=src python -m pytest -q tests/test_eval_v2.py`:

```text
.....                                                                    [100%]
5 passed in 6.20s
```

`PYTHONPATH=src python -m pytest -q tests/test_eval.py tests/test_eval_v2.py` after the verdict-label regression fix:

```text
......                                                                   [100%]
6 passed in 9.76s
```

`PYTHONPATH=src python -m pytest -q` in the available Phase 5 package snapshot:

```text
...................................s...............................      [100%]
66 passed, 1 skipped in 10.93s
```

`PYTHONPATH=src python -m compileall -q src tests eval`:

```text
COMPILEALL_EXIT=0
```

`PYTHONPATH=src python eval/stale_facts.py --k 5`:

```text
AGM synthetic retrieval smoke evaluation
Scenarios: 4; top-k: 5; embedder: hash-256-v1
mode        accuracy   stale-error   abstention   expanded
flat         100.0%         0.0%        0.0%          0
graph        100.0%         0.0%       25.0%          3
Caveat (D-007): this synthetic smoke test is not evidence for or against hypotheses H1-H7.
```

`PYTHONPATH=src python eval/synthetic_v2.py --entities 200 --episodes 2000 --seeds 5 --k 8 --embedder hash --results-dir eval/results` completed with exit code 0. It generated `eval/results/20261023T155826.716282Z.json`. The tables above come from that real run.

### Not run successfully in this execution environment

- `python -m pip install -e ".[dev]"` — failed during build isolation because network/DNS was unavailable while fetching `setuptools>=68`: `ERROR: No matching distribution found for setuptools>=68`.
- `python -m pip install --no-build-isolation -e ".[dev]"` — also unable to complete because the environment could not fetch `mcp>=1.26,<2`. This is why `tests/test_mcp_stdio.py` was skipped in the local snapshot run.
- `python examples/mcp_smoke_client.py` and `python examples/rest_smoke_client.py` — attempted, but the files are absent from the Phase 5 snapshot available in the builder filesystem, so Python returned `No such file or directory`. Run them on the actual v0.5.1 checkout after applying the overlay.
- The full `pytest` result is against the available Phase 5 package snapshot, not the full v0.5.1 checkout. The v0.5.1 hardening tests for D-021 to D-023 were not present in this workspace. Do not treat 66 passed as a full v0.5.1 regression result.
- `PYTHONPATH=src python eval/synthetic_v2.py --entities 5 --episodes 0 --seeds 1 --embedder st` was run to check the missing-optional-dependency path and exited 2 with: `error: --embedder st requires the optional sentence-transformers package. Install it with `python -m pip install sentence-transformers`, then retry.` The actual sentence-transformer model evaluation was NOT RUN because the package/model was unavailable offline.

## Contract concerns, assumptions and unfinished work

- No public AGM models, REST paths, MCP tool names or CLI commands were changed. `eval/stale_facts.py` and `tests/test_eval.py` remain compatible.
- The current `MemoryStore` graph expansion configuration is unchanged. Two-hop questions are included as required by the brief, but the evaluation does not add a traversal feature. All-modes 0% multi-hop accuracy is reported plainly rather than tuning the generator.
- Wall-clock latency and rank scores that depend on live recency are runtime measurements, not deterministic values. Tests assert identical gold manifests and stable outcome metrics, excluding latency and volatile top scores.
- The builder package is a Phase 5 snapshot rather than the full 0.5.1 working tree. The overlay is selective and should be applied on top of v0.5.1 so D-021 core guard, D-022 delete/WAL durability, and D-023 repo hygiene remain intact.
- The user-supplied v0.5.1 Windows output showed MCP smoke checks `12/12` passed. Its REST smoke client printed all 11 functional checks as PASS, then exited with `PermissionError: [WinError 32]` while `TemporaryDirectory` tried to remove the still-open SQLite database. This package intentionally does not alter that smoke-client teardown issue or D-021 to D-023.
- `PYTHONPATH=src python scripts/pack.py` created `dist/agm-phase6.zip` and `dist/agm-phase6-overlay.zip`. `unzip -t dist/agm-phase6-overlay.zip` reported `No errors detected in compressed data`; the overlay includes the report and one result JSON and excludes `.git`, databases, bytecode, and egg-info. The ZIP intended for v0.5.1 is the selective overlay; the full workspace ZIP comes from the older builder snapshot and should not be used as the v0.5.1 patch.

## Research caveat

D-007 applies: this synthetic seeded smoke test is not evidence for or against H1–H7. The current result says exactly: **graph not shown to help in this smoke test**.
