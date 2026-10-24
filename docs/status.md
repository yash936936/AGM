# Status — AGM prototype

> Updated every run. Newest entry at top.

## 2026-10-24 — Phase 8 implemented in reconstructed builder snapshot; Windows revalidation pending
**Current phase:** Phase 8 — temporal/entity ranking, size/context benchmark, Memory Doctor and agent instrumentation. Apply as a patch to the actual v0.5.1 checkout; do not replace the owner’s core source tree wholesale.
**Last debug:** DBG-011. **Last decision:** D-026; D-024 verdict rule and D-021 through D-025 are unchanged.
**Changes:** entity-centric queries now prioritize direct facts for an explicitly named entity; explicit entity+attribute queries prioritize the requested answer slot; temporal queries can pass the low lexical-similarity gate only when the exact entity+attribute exists in the already time-filtered eligible rows. Added a 44-record sample corpus, repeatable ingester, read-only Memory Doctor CLI with JSONL SQL/retrieval/event logs, a flat/graph size-context benchmark, and an offline/optional live OpenAI Responses API agent demo. Raw content is excluded from logs by default; `--include-content` explicitly opts into guard-redacted snippets.
**Sample diagnosis:** fresh sample ingestion yielded 42 added, 1 superseded and 1 quarantined item. Doctor checked SQLite/index/edge/temporal consistency and eight retrieval probes; all probe answers/abstentions were correct. The intentionally quarantined example was logged as INFO.
**Matrix result:** 27 cells across size 12/25/50 × context sparse/balanced/dense × seeds 0/1/2. Graph accuracy = 100% in every cell and unknown abstention = 100%; flat accuracy averages 79.2%, 74.6%, and 67.9% at sizes 12, 25, and 50 respectively. Graph p50 increased from about 3.19 ms for 12 entities/sparse context to 12.22 ms for 50 entities/dense context (builder environment; not Windows timing).
**Full-scale Phase 7 configuration regression:** 200 entities, 2,000 episodes per seed, five seeds, `k=8`, hash embedder and the same 0.25 threshold. The five single-seed run outputs were merged via the existing aggregator to preserve exact same five seeds under execution limits. Graph overall accuracy 100%, stale-error 0%, abstention correctness 100%, p50 64.76 ms and p95 74.67 ms in the builder environment. D-024 final summary remains unchanged (`graph not shown to help in this smoke test`) because stale family accuracy remains tied at 100%.
**Agent:** offline flat and graph retrieval loops ran and generated detailed traces; no live LLM was called. The optional OpenAI path awaits an installed SDK, user-configured API key/model and an explicit live run.
**Validation in the available reconstructed builder snapshot:** 80 passed, 1 skipped; 29 focused Phase 8/retrieval/eval tests passed; compileall, sample ingest, Memory Doctor and offline agent run passed. The skip requires the MCP SDK, unavailable in this environment. User has already validated the Phase 7 patch on Windows at 110 passed, MCP 12/12, REST 11/11, but Phase 8 itself has not yet been run on Windows.
**Next:** apply `PHASE8_PATCH.diff` to the actual Windows checkout, run `git apply --check`, `git apply`, `git diff --check`, `python -m compileall -q src tests eval scripts examples`, `python -m pytest -q`, repeat both smoke clients and compare fresh Phase 8 timings on the same Windows machine. Then connect the optional live model using synthetic memory, review redacted logs, and commit only after these gates pass.

## 2026-10-23 — Phase 7 retrieval diagnostics implemented in builder snapshot; Windows verification pending
**Current phase:** Phase 7 retrieval diagnostic patch prepared; do not replace the owner’s v0.5.1 source tree with the builder snapshot.
**Last debug:** DBG-010, multi-hop, abstention and graph-latency diagnostics.
**Last decision:** D-025 adds the diagnostic corrections/targets; D-024 rule and D-021 through D-023 remain unchanged.
**Code outcome:** The multi-hop generator wording now specifies exact dependency-hop distance without changing generated fact histories; the graph evaluator requests depth two only for that family. Directed graph traversal is anchored to the explicitly mentioned source, follows supported eligible relation edges, ranks the requested target attribute at the requested depth, and avoids unrelated global seeds. Catalogue-backed unknown numeric service IDs now abstain before fuzzy retrieval, without changing the 0.25 threshold. Graph corroboration counts are batched, and edge fan-out is capped after eligibility filtering.
**Phase 7 results:** `eval/results/20261023T184404.879694Z.json`; report: `PHASE7_REPORT.md`. Across five seeds, graph multi-hop accuracy is 100% [100, 100], all modes correctly abstain on the generated unknown IDs, graph unanswerable abstention correctness is 100%, overall graph accuracy is 94.2% [91.39, 96.8], stale-error is 0%, abstention correctness is 99.17% [97.5, 100], p50 is 94.43 ms [90.97, 97.44], p95 is 124.88 ms [112.18, 137.67], and mean expansion is 7.075 nodes. These timings are from the available builder environment, not yet a same-platform validation against the Windows baseline.
**Validation in available builder snapshot:** `PYTHONPATH=src python -m pytest -q` — 72 passed, 1 skipped; compileall passed. The skip requires the MCP SDK, missing in this environment. The workspace used an earlier Phase 5 snapshot plus the Phase 6 overlay, so the actual v0.5.1 hardening tests and Windows-specific behavior are not validated here. The user’s latest known Windows baseline was 104 passed with REST smoke cleanup fixed.
**Next:** apply `PHASE7_PATCH.diff` to the actual v0.5.1 checkout, resolve any patch-context conflicts without overwriting D-021 through D-023, run `git diff --check`, `python -m pytest -q`, the same five-seed evaluation, both smoke clients, and `python scripts/pack.py`. Confirm graph p50 is at least 50% below the prior Windows result (1,370 ms) and graph p95 is below 1,000 ms on the same machine. Do not claim those targets are verified until this rerun.


> Updated every run. Newest entry at top.

## 2026-10-23 — Phase 6 evaluation v2 implemented
**Current phase:** Phase 6 evaluation v2 implementation ready for integration onto the v0.5.1 checkout; the default synthetic run does not show graph retrieval helping under D-024.
**Last debug:** DBG-009, seeded evaluation v2.
**Last decisions:** D-024 (pre-declared evaluation definitions and decision rule). D-021 to D-023 were preserved unchanged.
**Validation in available builder snapshot:** `tests/test_eval_v2.py` — 5 passed in 6.20s; legacy plus new eval tests — 6 passed in 9.76s; full snapshot suite — 66 passed, 1 skipped in 10.93s; compileall passed. The skipped test requires the MCP SDK, unavailable because network/DNS access failed during install.
**Default result:** 5 seeds, 200 entities, 2,000 episodes per seed, `k=8`, `hash-256-v1`; 120 queries. Overall accuracy: flat 67.6%, flat_filter 80.0%, graph 74.0%. The verdict summary is exactly `graph not shown to help in this smoke test`; full table, bootstrap confidence intervals and query trace are in `PHASE6_REPORT.md` and `eval/results/20261023T155826.716282Z.json`.
**Next up:** apply the selective Phase 6 overlay to the actual v0.5.1 checkout and rerun the full 0.5.1 suite. The available builder filesystem only contained the earlier Phase 5 snapshot, and both smoke-client scripts were absent there. The user's supplied Windows baseline includes an existing REST smoke-client teardown error (`PermissionError: [WinError 32]`) after its functional checks; that issue remains out of this evaluation-only package. Do not change D-021 to D-023 or present this snapshot suite as full v0.5.1 validation.


## 2026-10-23 — Phase 5 verified on Windows; final demo-label cleanup
**Current phase:** All five planned prototype phases implemented; final review and next-iteration scoping remain.
**Last debug:** DBG-007, Phase 5 Windows verification and demo label fix.
**Last decisions:** D-019 (lazy decay and dry-run threshold), D-020 (synthetic evaluation metric definitions); D-007 caveat remains active.
**Validation:** User ran `python -m pip install -e ".[dev]"`, `python -m pytest -q` — `61 passed` in 20.24s with one Starlette/httpx deprecation warning; `python eval/stale_facts.py` reported flat/graph accuracy 100%, stale-fact error 0%, abstention 0% flat / 25% graph, 3 graph-expanded items; demo handoff readback passed; lifecycle dry run reported zero candidates and explicitly no mutation; rebuild of separate empty `demo.db` reported zero nodes; packer created both Phase 5 ZIPs. A follow-up patch changes the demo fact from the stale “Phase 3” label to “Phase 5” and adds a regression test; the updated builder suite reports 61 passed, 1 skipped in 2.71s. Rerun on Windows to include the added test with the MCP test enabled.
**Next up:** apply the final demo-label patch/overlay, rerun tests and pack, inspect the ZIP, and keep services loopback-only pending security review.

## 2026-10-23 — Phase 5 evaluation and lifecycle implemented; Windows verification pending
**Current phase:** Phase 5 — Mini eval, shadow lifecycle, demo.
**Last debug:** DBG-006, synthetic evaluation, lazy decay and lifecycle dry run.
**Last decisions:** D-019 (lazy decay and dry-run threshold), D-020 (synthetic evaluation metric definitions); D-007 caveat remains active.
**Validation:** Builder environment: `PYTHONPATH=src python -m pytest -q` — 60 passed, 1 skipped in 2.10s. The MCP stdio test was skipped because the official SDK was unavailable in that builder runtime. Evaluation command ran and reported flat/graph accuracy 100%, stale-fact error 0%, abstention 0% flat / 25% graph, with 3 graph-expanded items. Demo printed a successful handoff readback. Lifecycle dry run and compileall succeeded. These synthetic results are smoke-test outputs only.
**Next up:** User applies Phase 5 overlay on Windows, runs the full tests, `python eval/stale_facts.py`, demo, lifecycle dry run against a populated database, rebuild, and pack. Do not close Phase 5 before review.

## 2026-10-23 — Phase 4 trust, rollback and handoff verified on Windows
**Current phase:** Phase 5 — Mini eval, shadow lifecycle, demo.
**Validation:** User reported `56 passed` in 11.93s after installing `agm 0.4.0`; the MCP integration ran, demo completed, rebuild reported zero nodes for the empty `demo.db`, and packaging created Phase 4 archives. Starlette/httpx emitted one deprecation warning only.

## 2026-10-23 — Phase 4 trust, rollback and handoff implemented; Windows verification pending
**Current phase:** Phase 4 — Trust, handoff, rollback.
**Last debug:** DBG-005, Phase 4 trust and handoff tests.
**Last decisions:** D-016 (high-stakes gate and usable handoff result), D-017 (replayable handoff and revocation semantics), D-018 (exact-text corroboration for non-fact items).
**Validation:** `PYTHONPATH=src python -m pytest -q` — 55 passed, 1 skipped in 1.19s. The skip is `tests/test_mcp_stdio.py` because the official MCP SDK is absent in the builder environment. `PYTHONPATH=src python -m compileall -q src tests` passed; the demo exited 0; rebuilding the new, empty `phase4-demo.db` correctly reported zero nodes. Phase 4 coverage checks low-trust fact and episode probation, independent corroboration and revocation, recursive removal of derived items, since filtering, bounded handoff context, readback mismatch reports, tenant isolation and packet replay.
**Contract note:** `high_stakes` and the extended `ResumeResult` are additive, decision-logged changes documented in `docs/phase4_contract_addendum.md`. Revocation removes searchable views but intentionally retains source write payloads in the event log; it is not a hard delete.
**Next up:** Apply `dist/agm-phase4-overlay.zip` to the Windows checkout, install with `python -m pip install -e ".[dev]"`, run `python -m pytest -q`, demo, rebuild and packaging checks. Review the report before marking Phase 4 complete.

## 2026-10-23 — Phase 3 interfaces and guardrails verified on Windows
**Current phase:** Phase 4 — Trust, handoff, rollback.
**Validation:** User reported `43 passed in 15.15s` after installing `agm 0.3.0`, with one Starlette/httpx deprecation warning. The user also verified `/healthz` returns `{"status":"ok","service":"agm"}`, authenticated write returned `status="added"`, retrieval returned the stored SQLite fact and the untrusted-data notice, and an invalid key received HTTP 401.
**Next up:** Phase 4 implementation, tests, review and Windows verification.

## 2026-10-23 — Phase 2 implementation built; awaiting local verification
**Current phase:** Phase 2 — graph layer, ranking, abstention.
**Last debug:** DBG-002, Phase 2 graph retrieval, conflict handling, alias replay and ranking tests.
**Last decisions:** D-011 to D-013 (event-stable entity identity, evidence-based abstention gate, provisional age factor).
**Validation:** The user later reported `31 passed in 7.38s` on Windows Python 3.14.7; the demo, rebuild CLI and package command also completed successfully. The archive should still be reviewed and the phase log formally reviewed before closure.
**Next up:** use Phase 3's overlay and validation steps listed at the top of this file.

## 2026-10-22 — Phase 1 implementation verified by user
**Validation:** the user reported `10 passed in 5.06s` on Windows Python 3.14.7, and the demo and rebuild commands exited successfully. A later Phase 2 Windows run reported `31 passed in 7.38s`, a successful demo, and a successful package build. The first package listing exposed `.git` content, so the packer excludes `.git` and other generated directories.

## 2026-10-22 — Docs scaffolded from Draft v5
**Current phase:** Phase 1 — Core store and event log.
**Last debug:** DBG-001, docs consistency check.
**Last decisions:** D-001 to D-008 logged.
**Next up:** code, test, and review one phase at a time.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task — it routes you to the right file for what you are about to do.
