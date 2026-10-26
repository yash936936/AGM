# Synthetic retrieval smoke benchmark

**Status:** Runnable smoke diagnostic; not a production benchmark and not evidence for or against AGM hypotheses H1–H7.

## Run it

From the repository root in an environment with AGM's development dependencies installed:

```bash
python eval/stale_facts.py --k 5 --repeats 25
python eval/stale_facts.py --k 5 --repeats 25 --format json > synthetic-retrieval-smoke.json
# Compare the same synthetic scenarios at different archive sizes:
python eval/stale_facts.py --archive-size 0 --repeats 25 --format json > smoke-0.json
python eval/stale_facts.py --archive-size 1000 --repeats 25 --format json > smoke-1000.json
```

The JSON output is intended for reproducible archiving and lightweight automation. It records Python/platform, top-k, repetition count, scenario count, synthetic archive size per mode, timing scope, per-mode quality/performance metrics, and explicit caveats. The --archive-size N option changes the count of unrelated synthetic archive memories seeded for each mode (default 60; zero is valid). This enables a simple size-sensitivity sweep, but does not make the workload representative or measure concurrent throughput. Do not commit reports containing real user data; this fixture currently uses synthetic content only.

## Metrics and interpretation

| Metric | Meaning | Limitation |
|---|---|---|
| Accuracy | Expected answer appears in returned items for answerable authored scenarios | Four hand-authored scenarios are not a representative dataset |
| Stale error | Old value appears for the corrected-fact scenario | One stale-fact case only |
| Abstention | Retrieval abstains divided by all authored scenarios | Mixes answerable and unanswerable cases |
| p50 / p95 / p99 | Nearest-rank retrieval-call latency in milliseconds | Small local sample; hardware, OS, SQLite/cache state, and load affect results |
| Throughput (q/s) | Successful calls divided by the sum of measured retrieval-call durations | Sequential retrieval-only rate, not concurrent server throughput or end-to-end assistant latency |
| Errors | Retrieval exceptions during timed samples | Counts only; exception details are intentionally not emitted |

Each scenario is warmed once before timing. Seeding, database creation, and process startup are excluded from latency. Quality metrics are computed from a separate pass, not the repeated timing loop. Flat and graph modes are run in separate temporary databases.

## What this does not measure

- Retrieval behavior on held-out, consented real-user histories.
- Cross-session lifecycle, privacy leakage, deletion/revocation safety, or third-party host compatibility as a benchmark suite.
- End-to-end response latency including model inference, network, or host orchestration.
- Concurrent request throughput, sustained load, memory use, or cold-start latency.
- Statistical confidence intervals or pass/fail release thresholds.

Do not compare numbers across machines or commits as if controlled unless the environment, commit SHA, dependency set, configuration, and run protocol are recorded and controlled. For release acceptance, follow the [held-out real-history evaluation protocol](../acceptance/real_history_evaluation_protocol.md), freeze thresholds before testing, and have an independent evaluator review the aggregate results. Any forbidden-value disclosure, cross-scope leakage, or deleted/revoked content resurfacing is a stop-and-triage failure, not something average latency or accuracy can offset.
