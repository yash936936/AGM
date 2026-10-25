# AGM Core Benchmark and Comparison Plan

**Status:** benchmark protocol proposal, not a completed benchmark report  
**Applies to:** the current local SQLite prototype and future retrieval/evaluation changes  
**Last reviewed:** 2026-10-25

This document defines the measurements needed to compare AGM retrieval modes and to report performance honestly. Numeric results are included only when already recorded in repository evidence. Missing measurements remain **NOT RUN** rather than being estimated.

## Existing evidence and limits

The current `eval/stale_facts.py` is a synthetic smoke evaluation with four hand-authored scenarios and 60 unrelated synthetic archive notes. It compares flat retrieval (`expand=False`) with graph retrieval (`expand=True`) using the hash embedder. Its code explicitly warns that the results are not evidence for hypotheses H1–H7.

The Phase 5 record in `docs/phases.md` reports the following historical smoke-test output:

| Metric | Flat | Graph | Interpretation |
|---|---:|---:|---|
| Expected-answer accuracy | 100% | 100% | 3 answerable synthetic scenarios; answer-presence check only |
| Stale-fact error | 0% | 0% | One corrected-fact scenario |
| Abstention rate | 0% | 25% | Four total scenarios, including one unanswerable query |
| Expanded items | 0 | 3 | Diagnostic route count, not a quality score |
| Retrieval latency | NOT RUN | NOT RUN | No latency measurement was recorded |
| Throughput | NOT RUN | NOT RUN | No load test was recorded |
| Memory / storage cost | NOT RUN | NOT RUN | No resource measurement was recorded |

These values are historical, synthetic, and small-sample results. They must not be presented as production performance, statistically reliable quality estimates, or support for H1–H7. Re-run the evaluator on the exact candidate commit before quoting any current result.

The status record also contains test-suite and adapter-smoke counts. Those are correctness checks, not retrieval benchmark results, and must be reported separately.

## Required comparison matrix

Run each applicable mode against the same frozen dataset, query set, memory corpus, top-k, environment, and commit.

| System / mode | Purpose | Status |
|---|---|---|
| Flat AGM retrieval | Baseline; graph expansion disabled | Existing path; fresh benchmark NOT RUN |
| Graph AGM retrieval | Measure graph expansion's quality and cost | Existing path; fresh benchmark NOT RUN |
| Keyword / SQLite FTS baseline | Establish a simple lexical baseline where supported | NOT RUN; implement only if compatible with existing contracts |
| Embedding-only baseline | Separate semantic ranking effects from graph expansion | NOT RUN; only if a comparable implementation exists |
| Cross-session persistent AGM | Verify facts survive close/reopen and are retrieved in a new session | One synthetic recall case was reported; held-out evaluation NOT RUN |

Do not describe an unavailable baseline as tested. If a baseline is added, record its implementation, configuration, and code revision.

## Metrics to publish

### Retrieval quality

| Metric | Definition |
|---|---|
| Recall@k | Fraction of labelled relevant facts found in the top k results |
| Precision@k | Fraction of top-k results labelled relevant |
| MRR | Mean reciprocal rank of the first relevant result |
| nDCG@k | Ranking quality using graded relevance labels, if available |
| Exact-answer accuracy | Queries where the expected answer is present and current |
| Stale-fact leakage | Queries where a superseded or invalid value appears in returned results |
| Forbidden-value leakage | Queries where deleted, revoked, tenant-isolated, or otherwise forbidden content is returned |
| Abstention precision / recall | Whether AGM abstains on unanswerable queries and answers answerable ones correctly |
| Cross-session recall | Recall after closing the writer session/store and querying from a fresh session after reopen/rebuild |
| Conflict handling | Correctly surfaces or abstains on contested facts according to the frozen contract |

Define labels before running the evaluation. Report denominators and counts alongside percentages. For tiny synthetic suites, show raw counts rather than relying on percentages.

### Latency and throughput

Measure each operation independently: write, correction, delete, revocation, retrieval, close/reopen, and full view rebuild/replay. For retrieval, report cold-start and warm-run latency separately.

Publish p50, p95, and p99 latency in milliseconds, throughput in operations/second, total run duration, and timeout/error rate. Record dataset size and query mix for every run. Do not compare a single timing or averages alone.

### Resource and scaling cost

Record peak process RSS, database size before and after indexing/writes, event-log size, rebuild duration, and growth under increasing memory counts. At minimum, use corpus sizes of 100, 1,000, and 10,000 records if the test environment can support them; record any skipped scale point and why. Include graph expansion hop limit and top-k because both affect cost.

### Correctness, lifecycle, and isolation

Report pass/fail counts separately for append/replay determinism, idempotent writes, correction ordering, hard delete, retention/expiry, cutoff revocation, tenant/project isolation, malformed input, and forbidden-value absence after reopen and rebuild. A green test suite does not substitute for latency or quality measurements.

## Reproducible protocol

1. Record the Git commit SHA, Python version, operating system, CPU, RAM, dependency lock/version information, and configuration.
2. Freeze the dataset version/hash, scenario IDs, relevance labels, expected answers, forbidden values, and query split before running.
3. Use synthetic fixtures for routine CI. Use only consented, de-identified, access-controlled histories for held-out evaluation; publish aggregate results only.
4. Warm up the process, then run enough repetitions to report stable latency percentiles. Record repetition count and whether measurements include database startup.
5. Run flat and graph modes against the same corpus and query order. Randomize or alternate mode order when practical to reduce order and cache bias.
6. Save raw per-query/per-operation timings and outcomes as machine-readable JSON or CSV, plus a summary table. Keep private memory text and identifiers out of committed artifacts.
7. Re-run on the exact candidate commit and attach the command, artifact path, commit SHA, and environment to the result record.
8. Report failures and exclusions. Do not silently drop timeouts, abstentions, stale answers, or failed scenarios.

## Suggested result table

Copy this table into a dated report for each benchmark run. Replace every NOT RUN cell only from captured output.

| Category | Metric | Flat | Graph | Difference / notes |
|---|---|---:|---:|---|
| Quality | Recall@5 | NOT RUN | NOT RUN | |
| Quality | MRR | NOT RUN | NOT RUN | |
| Quality | Exact-answer accuracy | NOT RUN | NOT RUN | |
| Safety | Stale-fact leakage | NOT RUN | NOT RUN | |
| Safety | Forbidden-value leakage | NOT RUN | NOT RUN | |
| Behavior | Abstention precision / recall | NOT RUN | NOT RUN | |
| Persistence | Cross-session recall | NOT RUN | NOT RUN | |
| Latency | Retrieval p50 (ms) | NOT RUN | NOT RUN | |
| Latency | Retrieval p95 (ms) | NOT RUN | NOT RUN | |
| Latency | Retrieval p99 (ms) | NOT RUN | NOT RUN | |
| Throughput | Queries/second | NOT RUN | NOT RUN | |
| Resources | Peak RSS (MB) | NOT RUN | NOT RUN | |
| Storage | Database size (MB) | NOT RUN | NOT RUN | |
| Lifecycle | Full replay/rebuild (s) | NOT RUN | NOT RUN | |

## Acceptance and interpretation

- Do not claim AGM is faster or more accurate unless the paired comparison has measured results.
- Treat stale-value and forbidden-value leakage as safety failures, even when aggregate accuracy is high.
- Keep synthetic smoke results, held-out retrieval results, performance measurements, and security review findings in separate sections.
- Record confidence intervals for quality metrics when the held-out sample is large enough; include raw counts and dataset limitations regardless.
- Do not use these results as evidence for H1–H7 unless the relevant hypothesis, protocol, dataset, and analysis were explicitly designed for that test.
- Held-out real-history evaluation and independent security/privacy review remain **NOT RUN / NOT ESTABLISHED** until evidence is available.

## Current next step

The paired benchmark runner is merged. This increment adds aggregate operation-level timing for writes, lifecycle mutations, and rebuild/replay, and removes the source filename from aggregate reports. Peak process RSS, concurrent retrieval load, and a standalone keyword baseline remain future work. Keep the existing smoke evaluator intact as a fast regression check; do not silently turn its four scenarios into the headline benchmark.

## Paired runner usage

Run the new paired flat-vs-graph runner against a frozen, labelled JSONL case set:

```bash
python -m pip install -e ".[dev]"
python -m eval.benchmark_runner path/to/consented-deidentified-cases.jsonl --output benchmark-report.json
```

The default report omits case identifiers, memory text, and the source dataset filename. `--include-case-details` emits ordinal indices, scenario labels, outcomes and timings; protect these details if scenario composition is sensitive.

For each mode the runner reports case pass rate, expected-value recall, forbidden-value leakage, abstention accuracy where labelled, retrieval latency p50/p95/p99, end-to-end case latency p50/p95/p99, operation-level write/correction/delete/revocation/expiry/rebuild-replay timings where present, cases/second, elapsed time and maximum per-case SQLite file size. The aggregate report does not include the dataset filename, since filenames can contain identifying information. Retrieval latency measures only the `MemoryStore.retrieve` call; end-to-end case latency includes fixture setup, lifecycle operations, reopen and replay. Mode order alternates per case to reduce systematic order bias.

The runner is a local measurement harness, not evidence of production performance. Use synthetic cases in CI and only explicitly consented, de-identified histories for held-out evaluation. Record commit SHA, OS, Python version, CPU/RAM, dataset hash, case count, configuration and repetition count with any result.

Process RSS, concurrent-load throughput and a standalone keyword baseline remain NOT RUN. Real-history acceptance still requires an authorized held-out dataset; independent security/privacy review requires an actual reviewer and signed findings. Do not treat synthetic CI as closing either gate.

