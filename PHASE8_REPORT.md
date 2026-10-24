# AGM Phase 8 — Temporal and Entity-Centric Retrieval, Benchmark Matrix, and Memory Doctor

**Date:** 2026-10-24  
**Baseline:** Phase 7 source and D-024 decision rule  
**Status:** Implemented and exercised in the reconstructed builder snapshot; Phase 8 still requires a full rerun on the owner's Windows v0.5.1 checkout and a live-model run before phase closure.

## Executive summary

Phase 8 addresses the two remaining retrieval correctness gaps (temporal and entity-centric ranking), creates an ingestible mixed-context memory corpus, compares only flat and graph retrieval across controlled sizes/context densities, and adds a Memory Doctor CLI plus an agent-loop harness with JSONL telemetry.

The full-scale synthetic run using the same Phase 7 configuration (200 entities, 2,000 episodes per seed, five seeds, `k=8`, hash embedder, threshold 0.25) reports graph accuracy of 100.0%, 0.0% stale-error, 100.0% abstention correctness, p50 64.76 ms and p95 74.67 ms in the builder environment. Graph temporal and entity-centric families both reached 100.0% in this run. The pre-declared D-024 summary **remains** `graph not shown to help in this smoke test`: graph ties the flat baselines on `stale` at their 100% ceiling, so the strict rule requiring improvement on both `multi_hop` and `stale` is not met. No threshold or D-024 rule was changed.

**Evidence limits:** these scores come from generated data and query templates. D-007 remains active: they are diagnostic smoke results, not evidence for or against hypotheses H1–H7. The large graph-versus-flat improvement should be validated against hand-labelled and adversarial queries before it is treated as a production-quality result.

## 1. Scope and safeguards

- Preserved `eval/stale_facts.py` and the Phase 6/7 synthetic evaluation.
- Kept D-024's shared harness abstention threshold at **0.25**, the 1,000-resample bootstrap methodology, and its verdict rule unchanged.
- Added no hard runtime dependencies. The optional OpenAI SDK is imported lazily only when `--provider openai` is chosen.
- Kept D-021 through D-025 append-only and unchanged. D-026 records the Phase 8 decisions.
- Flat and graph modes see the same corpus and query in the Phase 8 size/context matrix. The matrix deliberately excludes `flat_filter`; the full-scale D-024 regression still records `flat`, `flat_filter`, and `graph`.

## 2. Retrieval changes

1. **Entity-centric ranking:** entity-summary queries such as `What is known about billing-api?` prioritize current facts attached to the exact named entity. This protects the target entity's fact set from globally similar facts owned by unrelated entities.
2. **Answer-slot ranking:** when the question names an entity and an attribute intent (for example, `Who owns billing-api?`), the matching entity/attribute fact is prioritized in the ordered evidence.
3. **Temporal retrieval:** with an explicit `as_of`, an exact named entity plus requested attribute can pass the language-only low-similarity gate only if an eligible row for that exact entity/attribute exists **after the time filter has been applied**. This does not globally weaken the threshold or allow absent history to answer.
4. **Scores vs ordering:** `Node.score` is the original rank score; intent priorities are deterministic sort keys, not calibrated probability or numeric score boosts. A returned list can therefore have non-monotonic raw `score` values when an exact answer-slot priority takes precedence. Logs capture rank and raw score separately.

The tests cover entity-summary recall under distractor pressure, exact owner-slot ranking, historical owner selection before a correction, low lexical-overlap exact entity anchoring, and multi-hop regression tests from Phase 7.

## 3. Sample memory corpus

`examples/phase8_sample_memory.jsonl` contains **44 records** covering:

- direct service facts: owner, runtime, region, environment;
- a corrected owner with a historical value, so `as_of` queries can be checked;
- directed dependencies (gateway → billing → ledger → identity);
- similar/nearby service names to stress entity separation;
- free-form architecture and incident episodes;
- rollout/rollback procedures;
- project-level AGM facts;
- one deliberate instruction-like memory item that should be quarantined by the core guard.

Fresh-database ingestion result:

| Ingest outcome | Count |
|---|---:|
| Added | 42 |
| Superseded | 1 |
| Quarantined | 1 |
| Input records / resulting scoped nodes / tenant events | 44 / 44 / 44 |

The ingester uses the existing core guarded write path, supports `--dry-run`, emits hashed/redacted metadata to JSONL, and uses idempotency keys so rerunning against the same database does not append duplicate events.

## 4. Size and context-density matrix

**Fixed configuration:** sizes = 12, 25, 50 entities; context = `sparse` (0 free-text episodes/entity), `balanced` (1), `dense` (4); seeds = 0, 1, 2; `k=8`; `hash-256-v1`; flat and graph; shared 0.25 abstention threshold. There are 27 size/context cells and six question families per cell. Accuracy confidence intervals are deterministic bootstrap intervals over seed-level summaries. Latency is measured in the builder environment, not Windows.

| Entities | Context | Mean nodes | Flat accuracy (95% CI) | Graph accuracy (95% CI) | Flat p50 / p95 ms | Graph p50 / p95 ms | Abstention correctness flat / graph |
|---:|---|---:|---:|---:|---:|---:|---:|
| 12 | sparse | 99 | 79.3% (79.0–80.0) | 100% (100–100) | 1.87 / 2.31 | 3.19 / 3.74 | 100% / 100% |
| 12 | balanced | 111 | 79.3% (79.0–80.0) | 100% (100–100) | 1.94 / 2.52 | 3.29 / 3.82 | 100% / 100% |
| 12 | dense | 147 | 79.0% (79.0–79.0) | 100% (100–100) | 2.29 / 2.95 | 4.19 / 4.92 | 100% / 100% |
| 25 | sparse | 233 | 74.6% (72.8–76.0) | 100% (100–100) | 2.63 / 4.37 | 4.82 / 5.71 | 100% / 100% |
| 25 | balanced | 258 | 74.6% (72.8–76.0) | 100% (100–100) | 2.94 / 4.59 | 5.11 / 6.22 | 100% / 100% |
| 25 | dense | 333 | 74.6% (72.8–76.0) | 100% (100–100) | 3.43 / 3.97 | 6.39 / 7.37 | 100% / 100% |
| 50 | sparse | 518 | 67.9% (67.2–68.5) | 100% (100–100) | 4.11 / 5.55 | 7.90 / 8.74 | 100% / 100% |
| 50 | balanced | 568 | 67.9% (67.2–68.5) | 100% (100–100) | 4.51 / 6.49 | 8.47 / 9.19 | 100% / 100% |
| 50 | dense | 718 | 67.9% (67.2–68.5) | 100% (100–100) | 6.26 / 8.33 | 12.22 / 14.40 | 100% / 100% |

Across the nine cells, graph was 100% on the generated cases for every answerable family; graph abstention correctness was 100% on unanswerables. Flat accuracy averaged across cells/families was 100% on single-fact, 100% on stale, 69.5% on entity-centric, 0% on multi-hop, and 100% on temporal. Graph averaged 100% on those answerable families. Both modes correctly abstained on all generated unanswerable examples.

**Interpretation:** graph latency grows with both entity count and episode density, as expected. At the same time, the test patterns encode explicit entity and relationship clues that graph retrieval is designed to exploit. Perfect graph scores should be considered a hypothesis for external validation, not a generalized guarantee. The raw per-query evidence, scores, gold labels, and latency traces are stored in `eval/results/phase8-benchmark-20261024T110135.355459Z.json` (about 4.3 MB).

## 5. Same-configuration full-scale regression

The full-scale Phase 8 run uses the Phase 7 settings: 200 entities, 2,000 episodes per seed, seeds 0–4, `k=8`, hash embedder, graph depth one by default and depth two only for the multi-hop family. The command was run as five separate one-seed jobs and the existing aggregator merged their results, because one continuous job was interrupted by the environment time limit. The seed set and benchmark configuration match the five-seed protocol; the merged provenance is recorded in the JSON.

| Overall metric | Flat | Flat-filter | Graph |
|---|---:|---:|---:|
| Accuracy@k (95% CI) | 67.6% (67.2–68.0) | 80.0% (80.0–80.0) | 100.0% (100–100) |
| Stale-error | 0.0% | 0.0% | 0.0% |
| Abstention correctness | 100.0% | 100.0% | 100.0% |
| Store / harness abstention rate | 16.7% / 16.7% | 16.7% / 16.7% | 16.7% / 16.7% |
| p50 / p95 latency | 28.82 / 32.53 ms | 14.16 / 16.12 ms | 64.76 / 74.67 ms |
| Mean items returned | 6.67 | 3.70 | 6.67 |
| Mean graph expansion | 0.00 | 0.00 | 7.08 |

| Family | Flat accuracy | Flat-filter accuracy | Graph accuracy | Interpretation under D-024 |
|---|---:|---:|---:|---|
| Single fact | 100% | 100% | 100% | Not shown; baselines tie graph |
| Stale | 100% | 100% | 100% | Not shown; no accuracy gain and stale error ties at 0% |
| Entity-centric | 38% | 100% | 100% | Not shown; graph ties flat-filter |
| Multi-hop | 0% | 0% | 100% | Promising versus both baselines on this family |
| Temporal | 100% | 100% | 100% | Not shown; baselines tie graph |
| Unanswerable | N/A | N/A | N/A | Abstention correctness 100% in every mode |

The pre-declared summary remains `graph not shown to help in this smoke test`, because D-024 requires a strict improvement on both `multi_hop` and `stale`; the stale family is saturated and graph ties both baselines. Do not alter D-024 after observing results.

Full-scale JSON: `eval/results/phase8-synthetic-200x2000-5seeds-20261024T110557.327133Z.json` (about 353 KB). Phase 7's original Windows result remains untouched as the baseline artifact.

## 6. Memory Doctor and logs

`python -m agm doctor --db ./phase8-memory.db --tenant phase8-demo --project phase8` runs a read-only integrity audit and diagnostic retrieval probes. It checks:

- `PRAGMA integrity_check`;
- node-to-embedding and node-to-FTS coverage, orphan embedding/FTS records;
- orphan graph edge endpoints;
- active rows with `valid_to`, superseded rows without `valid_to`, duplicate active entity/attribute fact keys, ambiguous aliases, and overlapping temporal intervals;
- counts by node status/kind and event type, recent event metadata/hashes;
- entity-centric recall, direct owner query, historical owner at an `as_of`, unknown-ID abstention;
- per-query latency, raw rank score, item rank/IDs, valid-time, trust tier, route/expansion metadata, abstain reason, SQL statement count/operations/top normalized SQL templates, and exceptions.

Logs are append-only JSONL. Default logs omit raw query/item text and record hashes/lengths plus identifiers and metadata; `--include-content` is an explicit local-only opt-in to include snippets after the existing guard redactor. SQL trace logs normalize literals and numbers to avoid writing bound values. Logs can still expose entity names, IDs and operational patterns; do not upload production traces to public issues. The sample traces in this package use synthetic content only.

Example:

```bash
python -m agm doctor --db ./phase8-memory.db --tenant phase8-demo --project phase8 --log logs/memory-doctor.jsonl
```

To diagnose only a specific time-sensitive question, repeat `--query` options and provide `--as-of`:

```bash
python -m agm doctor --db ./phase8-memory.db --tenant phase8-demo --project phase8 --query "Who owned billing-api?" --as-of 2024-12-31T23:59:59Z --log logs/temporal-doctor.jsonl
```

The current sample doctor found sound SQLite/index/edge structure and 100% correctness across eight probes (entity summary, direct owner, historical owner, and unknown ID in both modes). One quarantined item was reported at INFO level, which is expected for the deliberately unsafe sample.

## 7. Agent integration status

`examples/phase8_agent_demo.py` runs retrieval through the real `MemoryStore`, collects the same trace used by Memory Doctor, then either presents retrieved evidence with the offline provider or sends that evidence to the optional OpenAI Responses API provider. The prompt explicitly treats retrieved memory as untrusted evidence and asks the model to distinguish current from historical facts. Model logs record model/provider, latency, response/request identifiers when available, token usage when provided, response hash/length, retrieved item IDs and retrieval trace ID. The OpenAI Responses API call sets `store=False` for the response. Secrets are not logged; raw content requires `--include-content` and is guard-redacted.

The sample flat and graph offline demos have both run. **No live LLM request was made** during this work because no model credentials were provided. Offline execution validates the retrieval-to-agent handoff and logging, but not model reasoning or resistance to prompt injection. Before a live run, install the optional SDK, set local environment variables `OPENAI_API_KEY` and `OPENAI_MODEL`, and use only the synthetic sample database. Then manually inspect whether the model answers the owner question correctly, reports historical values only for the requested `as_of`, abstains for `svc-999999`, and ignores the instruction-like quarantined sample.

## 8. Validation and remaining gates

Completed in the reconstructed builder snapshot:

- focused Phase 8/retrieval/Phase 6 evaluation tests: **29 passed**;
- full available snapshot suite: **80 passed, 1 skipped** (the missing MCP SDK caused the skip);
- `compileall`, sample ingestion, Memory Doctor and offline flat/graph agent loops passed;
- size/context matrix completed across 27 cells and the five-seed full-scale regression JSON was generated;
- `eval/stale_facts.py --k 5` passed in the earlier verified Phase 7 Windows run; rerun it again after applying the Phase 8 patch.

Not yet completed: full Phase 8 suite on the actual Windows v0.5.1 tree; repeating the five-seed workload and size/context matrix on the same Windows machine for comparable latency; a real model-connected agent test; and review of logs against real operational privacy requirements. Do not use the reconstructed snapshot's test count as a replacement for the user's full Windows suite.

## 9. Timeline and exit gates before proceeding to the next integration phase

| Workstream | Planned effort | Status / exit gate |
|---|---:|---|
| Sample corpus + guarded ingestion + Memory Doctor | 0.5 day | Implemented in builder; sample ingests 44 records and doctor passes 8 probes |
| Temporal/entity ranking fixes + regression tests | 0.5 day | Implemented in builder; 29 focused tests pass |
| Flat-vs-graph size/context matrix | 0.5 day | Implemented: 27 cells, 3 seeds, six families/cell |
| Apply Phase 8 patch, run full Windows suite and smoke clients | 0.5–1 day | Pending owner run; requires all tests and both MCP/REST clients to pass |
| Live LLM test, injection/temporal/unknown-ID manual QA, log review | 0.5–1 day | Pending an explicitly configured model/API; use synthetic data only |
| Review traces, freeze artifact, commit | 0.25 day | After Windows and live-model gates |

**Time remaining before the next major phase:** approximately **1–2 focused working days**, mainly Windows validation and model-connected QA; if no live model access is available, complete the local validation first and leave model QA as a clearly marked pending gate. Do not move into production data or broader agent integrations until (1) Windows suite plus both smoke clients pass, (2) temporal and entity probes pass, (3) unknown-ID abstention stays correct, (4) raw JSONL contains no keys/secrets, and (5) latency has been compared on the same machine/configuration. These are planning estimates, not a promise of background work.

## Commands to reproduce

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python eval/stale_facts.py --k 5
python scripts/ingest_phase8_sample.py --db ./phase8-memory.db --log logs/phase8-ingest.jsonl
python -m agm doctor --db ./phase8-memory.db --tenant phase8-demo --project phase8 --log logs/memory-doctor.jsonl
python eval/phase8_benchmark.py --sizes 12 25 50 --contexts sparse balanced dense --seeds 0 1 2 --k 8
python eval/synthetic_v2.py --entities 200 --episodes 2000 --seeds 5 --k 8 --embedder hash
python examples/phase8_agent_demo.py --db ./phase8-memory.db --mode graph --query "Who owns billing-api?" --provider offline
python examples/mcp_smoke_client.py
python examples/rest_smoke_client.py
python scripts/pack.py
```
