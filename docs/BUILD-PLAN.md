# AGM build plan: batches and review gates

Basis: `docs/ROADMAP.md` (v0.7 → v1.0). Current state: v0.7.0, local-only prototype; latest recorded local run: 308 passed / 2 xfailed (Windows, Python 3.14).
Rule that shapes the order: **evidence before features.** The graph has not beaten a flat baseline on any data yet, so no batch builds graph-specific features before gate G1.

## Overview

| Batch | Theme | Calendar | Ends with | Gate |
|---|---|---|---|---|
| 0 | Cleanup  | 2–3 days | one working copy, tidy repo | none |
| 1 | Retrieval correctness | 2–3 wks | v0.7.x tag, new baselines | none |
| 2 | Real-data evidence | 2–3 wks | benchmark reports on your cases, harness for agent A/B | **G1** |
| 3 | Scale and storage | 2–3 wks | **v0.8** | none |
| 4 | Security hardening | 3 wks | threat model, isolation matrix, audit log | external review (R3.5) |
| 5 | Remote deploy + host acceptance | 2–3 wks | **v0.9** | **G2** |
| 6 | Release | 2 wks | **v1.0** | four release gates |
| 7 | Only if demanded | n/a | MCP shim, teams, UI | triggers in ROADMAP R6 |

Total roughly 14–17 weeks at ~10 h/week of your time. Batches 2 and 4/5 depend on things only you can do (cases, a reviewer, a deploy account).

## Batch scopes

**Batch 1: Retrieval correctness.** R2.6f (wording-independent answer-slot), R2.6c (abstention, before/after on v3), R2.6d (near-duplicate names), R2.1 (optional sentence-embedder extra, lazy import), R2.3 (BM25, vector-only, whole-log baselines), R0.3 (add 3.14 to CI), R0.4 (CHANGELOG, release procedure), identify and resolve the 2 xfails.
Done when: each item meets its "done when" in ROADMAP; no new leaks; before/after numbers in `docs/benchmarks/`; one decision entry per contract change.

**Batch 2: Real-data evidence.** You first write 20–40 real cases (R2.2) and freeze them. ChatGPT builds: runner for the frozen cases against all baselines, R2.5 agent A/B harness (same tasks with and without AGM, success and token cost), report generator that emits aggregates only.
Gate G1 (R2.7): you decide using the margin fixed in advance. If graph fails, `expand` defaults off and later batches drop graph work.

**Batch 3: Scale and storage.** R5.1 (measure at 10k/100k/1M, then fix the full vector scan), R5.2 (embedder id per vector, re-embed migration), R5.3 (event-log versioning, replay across versions in CI), R5.4 (redacted logs, metrics, `doctor`).
Done when: p95 retrieval target met at 100k nodes with measurements recorded; old logs replay on new code.

**Batch 4: Security hardening.** R3.1 remainder (key expiry/rotation), R3.2 remainder (rate limits, safe errors, audit log with no memory text), R3.3 (route × tenant/project/ID-guessing matrix in CI), R3.4 (threat model, run `security_privacy_review_checklist.md`).
Between batches 4 and 5: independent review (R3.5). If it does not happen, remote stays off.

**Batch 5: Remote deploy and host acceptance.** R3.6 (HTTPS behind reverse proxy, persistent disk, single writer, tested backup/restore, rotation drill), R4 (two real hosts, e.g. Claude Code via CLI and a ChatGPT Action), checked-in OpenAPI with CI drift check, per-host setup guides.

**Batch 6: Release.** R7 (PyPI, Docker, tags, changelog), docs trimmed, the four release gates in ROADMAP section 8.

## How each batch runs

1. You open a branch `batch-N` and paste the master prompt plus that batch's scope block from `PROMPTS.md` into ChatGPT.
2. ChatGPT works item by item and returns complete files per roadmap item (it cannot commit; you commit each item separately after running pytest).
3. Mid-batch checkpoint (about one week in): you send me the commit list and test output; I flag drift early.
4. End of batch: you send me `git diff main...batch-N --stat`, the full diff of `src/` and `tests/`, the benchmark reports and the final pytest output. I review against the checklist below and return a numbered fix list or approval.
5. After approval: decisions logged, `status.md` updated, ROADMAP items ticked, merge, tag.

Two-week batches are large for AI-generated code: errors compound and review gets harder. The per-item commits and the mid-batch checkpoint are what keep that manageable; skip them and I would shrink the batches.

## Batch status and likely files

Update the **Status** line when a batch closes (after review), together with `STATE.md` and `status.md`. Item ids are defined in `ROADMAP.md`. File lists are likely touch points from the current layout; the builder confirms them and reports any others.

### Phase 0 — Cleanup and docs
**Goal:** one working copy, tidy repo, docs that match the code.
**Files touched:** `docs/benchmarks/history/*`, `.gitignore`, `docs/workflow.md`, `context.md`, `docs/BUILD-PLAN.md`, `docs/PROMPTS.md`, `docs/phases.md` (historical stub), `docs/debug.md`, `docs/appflow.md`, `docs/STATE.md`, `docs/status.md`, `docs/readme.md`, `docs/components/`
**Done when:** tidy changes from `chore/repo-tidy` are represented on `main`, CI green on all eight Ubuntu/Windows Python 3.11–3.14 jobs, old working folder retired (R0.5).
**Status:** In progress. D-050 merged in PR #62 (`6d6732b`). The remaining tidy changes were ported in PR #63 (`88044a1`); exact-head run #685 passed all eight Ubuntu/Windows Python 3.11–3.14 jobs. The old `chore/repo-tidy` branch was not merged directly because it had diverged; its D-049/build-plan/prompt work was already on main. Both formerly uncommitted test files are tracked on main and covered by CI. R0.5 remains open only because retirement of the old local working-folder copy cannot be verified remotely.

### Phase 1 — Retrieval correctness (batch 1)
**Goal:** fix the three remaining core defects found by the v3 benchmark and widen the baselines.
**Items:** R2.6f, R2.6c, R2.6d, R2.1, R2.3, R0.3, R0.4, X1 (explain the 2 xfails).
**Files touched:** `src/agm/retrieve.py`, `src/agm/embed.py`, `eval/labelled_v3.py`, `eval/relation_heldout.py` (or a new held-out file), `eval/benchmark_runner.py`, `tests/test_retrieve.py`, `tests/test_labelled_v3.py`, `.github/workflows/tests.yml`, `pyproject.toml`, `CHANGELOG.md`, `docs/benchmarks/`, `docs/decisions.md`
**Done when:** each item meets its "done when" in `ROADMAP.md`; abstention raises unanswerable correctness to ≥ 0.8 with single-fact recall down by ≤ 0.02; no forbidden-value leaks; every xfail is fixed or has a decision entry; v0.7.x tagged.
**Status:** In progress. Implementation and regression tests are on `batch-1/retrieval-correctness`; local execution is NOT RUN. Exact-head CI and the paired before/after benchmark are required before acceptance.

### Phase 2 — Real-data evidence and gate G1 (batch 2)
**Goal:** find out whether graph retrieval beats the best flat baseline on real usage, and decide.
**Items:** R2.2 (yours), R2.4, R2.5, R2.7. Builder writes the harness only; no retrieval changes.
**Files touched:** `scripts/build_real_history_cases.py`, `scripts/evaluate_real_history.py`, new runner under `eval/`, new A/B harness under `eval/`, `docs/benchmarks/`, `.gitignore` (`eval/real/`)
**Done when:** 20–40 real cases frozen before any run; aggregate-only reports for every baseline; agent A/B results with a stated sample size; G1 verdict recorded as a decision (graph ON by default, or OFF and optional).
**Status:** Not started. Blocked on your frozen cases.

### Phase 3 — Scale and storage (batch 3) → v0.8
**Goal:** usable on large stores, safe across upgrades.
**Items:** R5.1, R5.2, R5.3, R5.4. Graph-specific work only if G1 kept graph on.
**Files touched:** `src/agm/retrieve.py`, `src/agm/embed.py`, `src/agm/db.py`, `src/agm/events.py`, `src/agm/diagnostics.py`, `tests/test_replay.py`, `docs/architecture.md`
**Done when:** p95 retrieval target met at 100k nodes with the measurements recorded; switching embedders cannot mix vectors; old event logs replay on new code in CI.
**Status:** Not started

### Phase 4 — Security hardening (batch 4)
**Goal:** everything needed for an independent review.
**Items:** R3.1 (remaining), R3.2 (remaining), R3.3, R3.4.
**Files touched:** `src/agm/agent_keys.py`, `src/agm/api.py`, `src/agm/trust.py`, `src/agm/guard.py`, `tests/` (isolation matrix), `docs/acceptance/security_privacy_review_checklist.md`, new threat model under `docs/acceptance/`
**Done when:** expired keys fail; rate limits and safe errors tested; audit log never records memory text; isolation matrix runs in CI; threat model written with owners.
**Status:** Not started

### Gate G2 — independent review (R3.5, external)
Remote binding stays off until a reviewer other than the builder signs the checklist. Not a build phase.

### Phase 5 — Remote deploy and host acceptance (batch 5) → v0.9
**Goal:** two real hosts sharing one workspace over HTTPS.
**Items:** R3.6, R4.
**Files touched:** `docs/cloud-deployment.md`, new deployment files, checked-in OpenAPI file plus CI drift check, `examples/chatgpt_actions.md`, `docs/acceptance/third_party_host_validation.md`, `src/agm/api.py` (bind guard change only after G2)
**Done when:** backup and restore tested; key rotation drill done; host validation marked PASS, FAIL or NOT RUN for two real hosts.
**Status:** Not started

### Phase 6 — Release (batch 6) → v1.0
**Goal:** installable, documented, gated.
**Items:** R7.
**Files touched:** `pyproject.toml`, Docker image files, `CHANGELOG.md`, `README.md`, `docs/` (trim to README, QUICKSTART, architecture, decisions, acceptance)
**Done when:** the four release gates in `ROADMAP.md` section 8 are each PASS, FAIL or WAIVED with a named risk owner.
**Status:** Not started

### Phase 7 — Only if demanded
MCP shim as a thin REST client, teams and roles, PostgreSQL, web UI. Triggers are in `ROADMAP.md` R6. Not planned.

## Claude review checklist (per batch)

1. Matches frozen contracts; every "done when" line has a test that fails without the change.
2. Benchmarks: tuned set and held-out set kept separate; before/after numbers present and reproducible from the commands given.
3. No leaks added (forbidden-value leak count is zero on every family).
4. Parameterised SQL, no secrets or memory text in logs, loopback guard intact.
5. No scope creep, no unexplained new dependency, direct-library and REST behaviour still agree.
6. Windows and Linux both green; the xfail count has not grown without a decision entry.
7. Docs (`STATE.md`, `status.md`, `readme.md`, component guides) say only what was actually run, and a changed file list is reflected in `components/`.


Prompts for each batch: `PROMPTS.md`. Standing rules for any builder: `../AGENTS.md`. Process details: `workflow.md`. Component guides: `components/README.md`.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task.
