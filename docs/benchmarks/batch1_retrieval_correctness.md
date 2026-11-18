# Batch 1 retrieval correctness benchmark

**Status:** implementation and test cases added; benchmark execution NOT RUN locally. The pull-request workflow runs the same seeded v3 corpus against the PR base commit and the PR head, then uploads both JSON reports as `retrieval-before-after`.

## Compared systems

- `bm25`: standalone BM25 over the complete write log, without lifecycle or trust filtering.
- `vector`: cosine-only retrieval over the complete write log using the selected embedder.
- `flat`: AGM's FTS5/vector blend without graph expansion.
- `flat_iterative`: post-hoc agent-style repeated flat retrieval.
- `whole_log`: all written text supplied as context when it fits the configured character budget; otherwise it reports that the log does not fit. This is a context-size/coverage comparator, not an LLM answer-quality measurement.
- `graph`: AGM retrieval with bounded graph expansion.

The base-commit run uses the pre-change v3 runner, so only common modes are compared before/after. The updated run additionally reports vector-only and whole-log results. The workflow uses seed 0, one seed, 120 distractor episodes and k=5 to keep CI bounded. This is a diagnostic smoke comparison, not the pre-registered multi-seed result and not evidence for H1–H7 (D-007).

## Targeted regression coverage

- R2.6f: owner answer-slot phrases including “in charge of”, “responsible for”, “accountable for”, “maintains” and “looks after”.
- R2.6c: a named entity with no requested attribute must abstain; relation questions may pass the evidence gate only when a reached entity has the requested answer slot. The two strict xfail parameter variants are now ordinary tests.
- R2.6d: exact hyphen-aware entity boundaries and no sibling-value leakage for names such as `svc-12` and `svc-12-staging`, with and without graph expansion.

## Reported metrics

For the common modes, CI prints before/after graph pass rate and leak rate for single, hard-negative, multi-hop, poison and unanswerable families, plus pooled strict pass. The updated report includes the new baseline scores and estimated whole-log context tokens. Latency is diagnostic at this one-seed scale.

## Reproduction

```bash
python eval/labelled_v3.py --seed 0 --seeds 1 --episodes 120 --k 5 --output before-after.json
python eval/labelled_v3.py --seed 0 --seeds 5 --episodes 1200 --k 5 --embedder st --whole-log-max-chars 50000 --output labelled-v3-st.json
```

Install the optional sentence embedder with:

```bash
python -m pip install -e ".[eval-sentence-transformer]"
```

Do not compare the one-seed CI smoke output with the historical five-seed numbers as if they were the same experiment. The benchmark output must be reviewed alongside the exact source revision and its generated manifest.
