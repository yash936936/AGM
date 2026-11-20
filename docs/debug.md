# Debug log — AGM prototype

## DBG-012 — Graph location answer-slot mapping diverged from flat retrieval — 2026-11-20
**Task:** Resolve the two historical-location failures in CI run #780.
**Tested:** Run #780 on `77ec098`: all eight Ubuntu/Windows Python 3.11–3.14 jobs failed the same two tests, `test_as_of_filter_applies_to_graph_expansion` and `test_as_of_before_correction_returns_old_value`; each job reported 322 passed and 2 failed. The query's `location` intent was mapped to `region` in graph retrieval, so no matching answer-slot evidence was found. Changed `src/agm/retrieve.py` in `d7816d9` to separate `location` from `region`, matching flat retrieval. Exact-head run #781 passed all eight jobs. The paired benchmark was skipped on the push event and remains outstanding.
**Fixed:** graph/flat answer-slot mapping parity; CI #781 verified the two regression tests and full matrix. Batch 1 remains unaccepted pending final paired benchmark evidence and the unanswerable correctness target.

## DBG-011 — Historical CI #641 failure was a Windows duration-test timing flake — 2026-11-19
**Task:** Resolve DBG-002 by reading the failed job log from workflow run #641.
**Tested:** Retrieved the Windows Python 3.13 job log (job 125237161904). Repository hygiene passed; pytest reported 287 passed and one failure in `tests/test_rest_concurrent_benchmark.py::test_rest_benchmark_supports_duration_mode_and_rss_metadata`. The benchmark process exited normally, but its 0.5-second duration window recorded zero successful requests. The other five matrix jobs passed; run #642 later passed all six jobs.
**Found:** This was a timing-sensitive test failure on the Windows runner, not a demonstrated retrieval or API correctness failure. It is distinct from the earlier synchronous PowerShell RSS sampling issue in DBG-003; RSS sampling was already moved to a worker thread and each duration-mode worker already attempts at least one request.
**Fixed (pending CI):** Increased the test's duration window from 0.5 to 2.0 seconds while retaining the separate slow-RSS-probe regression test. The new test must pass on Windows Python 3.13 and the full matrix before DBG-002 is closed.


> Append-only. Newest entries at top. Log every defect found or fixed, with what was tested. Add a new entry to correct an old one; never edit past entries. IDs run DBG-001 onward. Decisions made while fixing go in `decisions.md`.
> Entries DBG-001 to DBG-008 were reconstructed on 2026-11-17 from `status.md`, `ROADMAP.md`, `decisions.md` and the benchmark reports. Earlier history is in git tag `archive/pre-cleanup-main`.

## DBG-010 — Retrieval answer-slot and entity-scope fixes pending validation — 2026-11-19
**Task:** Batch 1 R2.6f, R2.6c and R2.6d.
**Tested:** Source review only. Regression tests were added for owner paraphrases, hyphenated sibling entities, missing attributes and the two former R2.6c xfail variants. Local test execution NOT RUN.
**Found:** Answer-slot recognition covered only a narrow set of owner words; exact entity matching treated hyphens as token separators; graph abstention used lexical similarity even when a named relation target had a matching answer slot. Flat retrieval also allowed a named sibling to enter through global lexical candidates and did not abstain when the named entity lacked the requested attribute.
**Fixed (implementation, not yet verified):** Added owner/on-call paraphrases, hyphen-aware exact entity boundaries, entity-scoped candidate pools in flat and graph retrieval, and answer-slot evidence checks for direct and relation-target questions. Added a paired base-vs-head synthetic benchmark job and BM25/vector/whole-log comparators. CI and benchmark results are pending; do not mark R2.6f/c/d accepted yet.

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
