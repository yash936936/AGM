# AGM build plan: batches and review gates

Basis: `docs/ROADMAP.md` (v0.7 → v1.0). Current state: v0.7.x, 308 passed / 2 xfailed, local-only prototype.
Rule that shapes the order: **evidence before features.** The graph has not beaten a flat baseline on any data yet, so no batch builds graph-specific features before gate G1.

## Overview

| Batch | Theme | Calendar | Ends with | Gate |
|---|---|---|---|---|
| 0 | Cleanup (this PR) | 2–3 days | one working copy, tidy repo | none |
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

1. You open a branch `batch-N` and paste the master prompt plus that batch's scope block from `docs/PROMPTS.md` into ChatGPT.
2. ChatGPT works item by item and returns complete files per roadmap item (it cannot commit; you commit each item separately after running pytest).
3. Mid-batch checkpoint (about one week in): you send me the commit list and test output; I flag drift early.
4. End of batch: you send me `git diff main...batch-N --stat`, the full diff of `src/` and `tests/`, the benchmark reports and the final pytest output. I review against the checklist below and return a numbered fix list or approval.
5. After approval: decisions logged, `status.md` updated, ROADMAP items ticked, merge, tag.

Two-week batches are large for AI-generated code: errors compound and review gets harder. The per-item commits and the mid-batch checkpoint are what keep that manageable; skip them and I would shrink the batches.

## Claude review checklist (per batch)

1. Matches frozen contracts; every "done when" line has a test that fails without the change.
2. Benchmarks: tuned set and held-out set kept separate; before/after numbers present and reproducible from the commands given.
3. No leaks added (forbidden-value leak count is zero on every family).
4. Parameterised SQL, no secrets or memory text in logs, loopback guard intact.
5. No scope creep, no unexplained new dependency, direct-library and REST behaviour still agree.
6. Windows and Linux both green; the xfail count has not grown without a decision entry.
7. Docs and `status.md` say only what was actually run.


Prompts for each batch: `docs/PROMPTS.md`. Standing rules for any builder: `AGENTS.md`. Process details: `docs/workflow.md`.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task.
