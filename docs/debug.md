# Debug log — AGM prototype

> Append-only. Newest entries at top. Log every defect found or fixed, with what was tested. Add a new entry to correct an old one; never edit past entries. IDs run DBG-001 onward. Decisions made while fixing go in `decisions.md`.
> Entries DBG-001 to DBG-008 were reconstructed on 2026-11-17 from `status.md`, `ROADMAP.md`, `decisions.md` and the benchmark reports. Earlier history is in git tag `archive/pre-cleanup-main`.

## DBG-009 — Identify the two xfail instances — 2026-11-19
**Task:** Investigate DBG-008 before Batch 1.
**Tested:** Source inspection of `tests/test_relation_wording.py`; tests were not executed in this session.
**Found:** The two reported xfails are not two independent defects. They are the two `hint` parameter variants (`None` and `"alpha"`) of `test_two_hop_reaches_the_second_dependency_owner`, both marked `xfail(strict=True)` with reason R2.6c because low lexical similarity triggers abstention before relation expansion.
**Fixed:** Not yet. Batch 1 must make both variants pass and remove the strict xfail marker; run the test on Windows and Linux.

## DBG-008 — Two tests report xfail — 2026-11-17
**Task:** Local full run after the D-048 patch and the docs tidy.
**Tested:** `python -m pytest -q` on Windows, Python 3.14: 308 passed, 2 xfailed.
**Found:** two expected-failure tests that were not present in the previous run (294 passed, 0 xfailed). Which tests and why: not recorded (open — confirm).
**Fixed:** nothing yet. Batch 1 item X1: fix each, or record why it is expected to fail and which roadmap item removes the marker.

## DBG-007 — Answer-slot ranking, abstention and sibling-entity leaks still open — 2026-11-05
**Task:** Follow-up to the v3 benchmark (`benchmarks/r2_labelled_v3.md`).
**Tested:** v3 labelled benchmark, synthetic data, hash and spaCy embedders.
**Found:** (1) answer-slot priority depends on attribute wording (`owner/owns/owned`); "who is in charge of…" gets none (R2.6f). (2) abstention rarely fires for unknown entities or missing attributes (R2.6c). (3) near-duplicate names such as `x` and `x-staging` leak into each other's results without a hint (R2.6d).
**Fixed:** not yet. Scheduled for Phase 1.

## DBG-006 — Relation-following depended on query wording — 2026-11-05
**Task:** Multi-hop retrieval, v3 benchmark.
**Tested:** v3 plus a frozen held-out paraphrase check (`eval/relation_heldout.py`, `tests/test_relation_wording.py`).
**Found:** the graph followed outgoing relation edges only if the query contained one of five trigger words; "depends on", "relies on", "calls" scored hit@5 0.000–0.093.
**Fixed:** D-048. 1-hop and 2-hop hit@5 reach 1.000 on the held-out set; trigger-word results unchanged within 0.013.

## DBG-005 — An entity hint blocked graph expansion — 2026-11-04
**Task:** Multi-hop retrieval with `entity=` supplied.
**Tested:** v3 benchmark with and without hint; `tests/test_entity_hint_expansion.py`.
**Found:** multi-hop accuracy was 0.000 whenever a hint was passed, because the hint removed all other entities before expansion ran.
**Fixed:** D-047. The hint now scopes seeds only; neighbours come from the full eligible set under the same tenant, project, time, trust and contested filters.

## DBG-004 — Flat and graph retrieval disagreed on contested candidates — 2026-11-03
**Task:** v3 benchmark, poison family.
**Tested:** strict and unflagged-leak scoring across flat, graph and hinted modes.
**Found:** flat withheld contested candidates; graph returned them with `contested_with`. Strict scoring showed 26–40% graph leaks on poison.
**Fixed:** D-046. Both modes withhold contested candidates by default and flag the current fact; `include_contested` opts in.

## DBG-003 — Windows REST benchmark returned zero requests — 2026-11-04
**Task:** Local Windows run of `test_rest_benchmark_supports_duration_mode_and_rss_metadata`.
**Tested:** reproduced on Windows; fix verified with a regression test that simulates a slow probe; full suite 308 passed.
**Found:** RSS sampling spawned PowerShell synchronously inside the asyncio loop, freezing the load workers (0 requests in the 0.5 s window) and distorting the benchmark's own latencies.
**Fixed:** commit `90ccd23`. Sampling now runs in a thread and each worker makes at least one request. Not confirmed to be the same failure as DBG-002.

## DBG-002 — CI run #641 failed once on Windows, Python 3.13 — date not recorded
**Task:** CI after D-046.
**Tested:** next run (#642, commit `7e3f571`) passed on all six jobs.
**Found:** one failure whose log was never read; it did not recur.
**Fixed:** nothing. Treated as possibly flaky (roadmap R0.1). If a Windows job goes red again, capture the `FAILED` lines first.

## DBG-001 — Four core defects found by the v3 benchmark — 2026-11-03
**Task:** Pre-registered v3 labelled benchmark (R2).
**Tested:** hash and spaCy embedders, synthetic data, decision rule written before the run.
**Found:** graph is not justified on synthetic data (best other: iterative flat; graph wins only multi-hop). Four core issues came out of it: the contested mismatch (DBG-004), the hint blocking expansion (DBG-005), abstention rarely firing and sibling-entity leaks (DBG-007).
**Fixed:** see DBG-004 to DBG-006; the rest is open.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
