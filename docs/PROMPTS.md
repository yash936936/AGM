# Prompts for the builder (ChatGPT, Codex or any other)

How to use: open a new chat per batch, paste **Master prompt**, then the **batch block**, then attach or paste the files the prompt asks for. Plan and gates: `docs/BUILD_PLAN.md`. Standing rules (invariants, truthfulness, delivery format) live in `AGENTS.md`; this file does not repeat them, so they cannot drift apart.

## Master prompt (paste first, every batch)

```
You are the builder for AGM (Adaptive Graph Memory), a local-first prototype of an
event-sourced, model-agnostic agent memory layer. A supervisor (Claude) reviews your work
by running it; the user integrates your output.

Read, in this order, before changing anything: AGENTS.md, context.md, docs/status.md,
docs/ROADMAP.md, docs/architecture.md, docs/decisions.md (top 10 entries at least).
If you cannot read files, say so and ask me to paste them. Do not guess their contents.
AGENTS.md is binding, including its invariants and truthfulness rules.

Batch rules:
1. Work only on the items in the batch block below, in the order given. Nothing else.
2. Work item by item. After each item, stop and return: complete files (repo path as
   heading), a new D-0NN entry for any design choice or contract change, and the item's
   self-report. Then wait for me to say "next" unless I told you to continue.
3. Every "done when" line gets a test. Benchmarks are tuned on one set and validated on a
   separate held-out set that you write before tuning and never tune against.
4. No new dependency unless the item names it; optional extras must be lazy-imported and
   need a D-0NN entry first (AGENTS.md invariant 10).
5. Loopback-only stays until I state in writing that gate G2 has passed.
6. Never claim a test passes unless you ran it in this session; otherwise write NOT RUN
   and give me the exact command. Quote real output, never invent numbers.
7. Self-report per item: files changed; what each new test proves; commands and real
   output (or NOT RUN); before/after numbers where the item asks; contract concerns;
   assumptions; what you did not finish.
```

## Batch 1: Retrieval correctness

```
BATCH 1: Retrieval correctness (docs/BUILD_PLAN.md, batch 1).
Order: R2.6f, R2.6c, R2.6d, R2.1, R2.3, R0.3, R0.4, then X1.
Details are in docs/ROADMAP.md under the same ids.
- R2.6f: replace attribute-wording dependence in answer-slot detection with a
  wording-independent rule. Write held-out paraphrases ("in charge of", "responsible for",
  "maintains") first; do not tune to them.
- R2.6c: abstention for unknown entities and for known entities lacking the asked
  attribute. Report v3 unanswerable correctness and single-fact recall before and after;
  recall may drop by at most 0.02. Keep the rule configurable.
- R2.6d: disambiguate near-duplicate names (x vs x-staging) without a hint.
- R2.1: optional sentence-embedder extra (lazy import; D-0NN first). Re-run the v3
  benchmark and list the embedder per run.
- R2.3: add BM25-only, vector-only and whole-log baselines to the benchmark report.
- R0.3: add Python 3.14 to the CI matrix. R0.4: CHANGELOG.md and a release procedure.
- X1: two tests currently xfail. Find out why. Either fix them or record each in a D-0NN
  entry with the reason and the item that will remove the xfail.
Out of scope: anything under R3, R4, R5, R6, R7.
```

## Batch 2: Evidence harness (start only after real cases are frozen)

```
BATCH 2: Evidence harness. Precondition: I have frozen 20-40 real cases under eval/real/
(this folder is gitignored; you will never see raw case text).
Order: E1, E2, E3. Do not change retrieval behaviour in this batch.
- E1: runner that evaluates frozen cases against AGM flat, AGM graph, keyword, BM25,
  vector-only and whole-log baselines, emitting an aggregate-only report (counts, rates,
  latency; no case text, no memory values).
- E2 (R2.5): agent A/B harness: same tasks with and without AGM, recording task success
  and token cost per run, fixed seed, documented sample size, and a table showing where
  the baseline wins.
- E3: G1 report template that states the decision margin and the forbidden-leak rule
  before any run, and leaves the verdict blank for me.
```

## Batch 3: Scale and storage

```
BATCH 3: Scale and storage. Order: R5.1, R5.2, R5.3, R5.4.
- R5.1: first measure p50/p95 retrieval and memory at 10k, 100k and 1M nodes; report the
  numbers; then choose and justify a fix for the full vector scan (cached matrix,
  sqlite-vec or ANN). Target p95 < 100 ms at 100k nodes, to be confirmed by the numbers.
- R5.2: store an embedder id per vector; re-embed migration that cannot mix vectors.
- R5.3: event-log schema versioning; replay tests over old-version fixtures.
- R5.4: redacted structured logs, basic metrics, extended `doctor`.
Gate G1 outcome: <fill in: graph ON / graph OFF>. If OFF, skip graph-specific paths.
```

## Batch 4: Security hardening

```
BATCH 4: Security hardening. Order: R3.1 (remaining), R3.2 (remaining), R3.3, R3.4.
Write the negative tests first, then the code.
- R3.1: key expiry and rotation; managed credential store instead of a JSON file.
- R3.2: rate limits, safe error bodies, audit log (who read/wrote/deleted what; never
  memory text), no secrets in logs.
- R3.3: isolation matrix: every route x cross-tenant, cross-project, ID guessing, wrong
  scope; runs in CI.
- R3.4: threat model and data-flow inventory in docs/acceptance/; fill in
  docs/acceptance/security_privacy_review_checklist.md with findings and owners.
Do not add remote binding or any non-loopback option.
```

## Batch 5: Remote deploy and host acceptance (only after R3.5 review is signed)

```
BATCH 5: Remote deploy and host acceptance. Gate G2 status: <fill in: PASSED on date>.
Order: R3.6, R4.
- R3.6: single instance behind an HTTPS reverse proxy, persistent disk, single writer;
  backup and restore script with a test; key rotation drill.
- R4: checked-in OpenAPI file with a CI drift check; per-host setup guides; run
  docs/acceptance/third_party_host_validation.md against two hosts and mark each line
  PASS, FAIL or NOT RUN. CI smoke tests do not count as host validation.
```

## Batch 6: Release

```
BATCH 6: Release (R7). No new features. Build PyPI and Docker artefacts, prepare the
v1.0.0 tag and changelog, trim docs to README, QUICKSTART, architecture, decisions and
acceptance. Report each release gate in docs/ROADMAP.md section 8 as PASS, FAIL or WAIVED
with a named risk owner.
```

## What to send Claude at the end of a batch

1. `git diff main...batch-N --stat`
2. Full diff of `src/`, `tests/`, `eval/`, `scripts/`
3. New or changed reports in `docs/benchmarks/`
4. Full output of `python -m pytest -q`, `python scripts/check_repo_hygiene.py`, `python scripts/check_package.py`
5. The builder's self-reports and any "Contract concerns"

---
**Next:** Return to [`context.md`](../context.md) before starting a new task.
