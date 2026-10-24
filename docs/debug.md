# Debug log — AGM prototype

> Append-only. Every completed coding task gets an entry here, even "no
> issues found." Newest entries at top.

## DBG-010 — Phase 7 retrieval diagnostic and baseline comparison — 2026-10-23
**Task:** Diagnose multi-hop accuracy 0%, poor abstention on unknown numeric service IDs, and high graph latency without generator/threshold tuning.
**Evidence before changes:** Phase 6 result `eval/results/20261023T155826.716282Z.json` had graph multi-hop accuracy 0%, unanswerable abstention correctness 0%, graph overall p50 about 781 ms and p95 about 1,354 ms in the builder snapshot. The user’s Windows run had graph p50 1,370 ms and p95 2,302 ms. A cProfile run on a 200-entity / 2,000-episode seeded store reported about 0.96 seconds for one representative directed graph query, 789 `sqlite3.Connection.execute` calls and 214 `independent_corroborations` calls; corroboration calls accounted for about 0.72 seconds cumulatively.
**Root causes:** Multi-hop wording did not specify exact path distance and the evaluation invoked default one-hop graph traversal for two-hop cases. Directed expansion could seed from an unrelated highly-ranked neighbouring service and the global top-hit pool could reintroduce unrelated candidates. Unknown identifiers such as `svc-012` or `svc-200` shared high-overlap words with existing facts, making ordinary fuzzy ranking unsuitable for identity checks. Graph candidate scoring repeated independent-corroboration SQL per row. Also, the graph expansion SQL limited rows before filtering ineligible/superseded relation support, allowing historical rows to crowd out the current target row.
**Changed:** Phase 7 adds explicit query-distance wording, graph depth=2 only for the multi-hop evaluation family, exact-entity anchoring and directed supported-relation traversal, a catalogue-backed unknown numeric-ID guard and a missing-filter abstention path, eligible-support filtering before fan-out limits, and batched corroboration lookup with semantic equivalence tests. The evaluation generator’s fact histories, relation chains, seeds, sizes and threshold are unchanged; D-024’s verdict rule is unchanged.
**After results:** 5 seeds, 200 entities, 2,000 episodes/seed, `k=8`, hash embedder; graph multi-hop 100% (95% CI 100–100%), all three modes correctly abstained on generated unknown service IDs, and graph unanswerable abstention correctness rose to 100%. Overall graph accuracy 94.2% (95% CI 91.39–96.8%), stale error 0%, abstention correctness 99.17% (95% CI 97.5–100%), p50 94.43 ms (95% CI 90.97–97.44), p95 124.88 ms (95% CI 112.18–137.67), mean graph expansion 7.075 nodes. See `PHASE7_REPORT.md` and `eval/results/20261023T184404.879694Z.json`.
**Validation in available builder snapshot:** full suite 72 passed, 1 skipped; compileall passed; the skip is the MCP stdio integration test because the MCP SDK is unavailable in this environment. The available builder code is derived from an older Phase 5 snapshot plus the Phase 6 overlay, not the complete Windows v0.5.1 checkout, so these figures are provisional until the patch is applied and the same full suite and evaluation are rerun on Windows. The user’s baseline run before Phase 7 recorded 104 passed and the REST smoke client 11/11 after its cleanup fix.
**Important:** User’s Windows graph performance targets (p50 improvement >=50% from 1,370 ms and p95 <1,000 ms) appear met numerically in the builder measurements but are **not yet confirmed on the same Windows environment**. D-021 through D-024 remain unchanged; D-007 synthetic benchmark caveat remains active.

---


## DBG-009 — Phase 6 synthetic evaluation v2 — 2026-10-23
**Task:** Replace the four-scenario smoke test as the main evaluation with a seeded multi-family comparison of `flat`, `flat_filter`, and `graph`, keeping `eval/stale_facts.py` and its test intact.
**Changed:** Added `eval/synthetic_v2.py`, `tests/test_eval_v2.py`, timestamped `eval/results/20261023T155826.716282Z.json`, Phase 6 README instructions, D-024, this report, and Phase 6-aware selective packaging. The generator covers `single_fact`, `stale`, `entity_centric`, `multi_hop`, `temporal`, and `unanswerable`; it records store and evaluation abstention separately and uses a fixed-seed 1,000-resample bootstrap CI.
**Tested in available builder snapshot:** `PYTHONPATH=src python -m pytest -q tests/test_eval_v2.py` — `5 passed in 6.20s`; `PYTHONPATH=src python -m pytest -q tests/test_eval.py tests/test_eval_v2.py` — `6 passed in 9.76s`; full snapshot suite — `66 passed, 1 skipped in 10.93s`; `PYTHONPATH=src python -m compileall -q src tests eval` — exit 0. The skipped test is `tests/test_mcp_stdio.py`, because the `mcp` dependency was not available in the builder runtime.
**Default evaluation:** `PYTHONPATH=src python eval/synthetic_v2.py --entities 200 --episodes 2000 --seeds 5 --k 8 --embedder hash --results-dir eval/results` completed with exit code 0 and saved the 300,469-byte JSON artifact above. Overall accuracy@k: flat 67.6%, flat_filter 80.0%, graph 74.0%; stale-error 0.0% for all; graph mean expanded count 18.85. Family verdicts: `single_fact` NOT SHOWN; `stale` NOT SHOWN; `entity_centric` FLAT BETTER; `multi_hop` NOT SHOWN; `temporal` FLAT BETTER; `unanswerable` NOT SHOWN. Exact metrics and confidence intervals are in `PHASE6_REPORT.md` and the JSON. The rule summary is `graph not shown to help in this smoke test`.
**Found/fixed:** The first report implementation could label graph-versus-flat `PROMISING` on a family where graph lost to `flat_filter`. Updated the label logic so `PROMISING` is shown only when the family meets the pre-declared BOTH-baselines rule. Added `test_graph_is_not_labelled_promising_if_flat_filter_wins`; D-024 and generator settings were not changed after observing results.
**Not run / blockers:** Both `python -m pip install -e ".[dev]"` and the no-build-isolation retry could not complete because DNS/network access was unavailable for setuptools/MCP packages. The smoke-client scripts are absent from the Phase 5 snapshot in this builder filesystem, so those commands returned `No such file or directory`; v0.5.1 smoke clients must be rerun in the owner's current checkout. `--embedder st` was not run because the optional package/model was unavailable.
**Scope preserved:** `D-021`, `D-022`, and `D-023` were not edited. The Windows `rest_smoke_client.py` temp-directory cleanup PermissionError shown in the owner's supplied baseline output remains out of this Phase 6 evaluation-only scope. Full regression verification must run on the actual v0.5.1 checkout; the builder workspace is an older Phase 5 package snapshot.


## DBG-007 — Phase 5 Windows verification and demo label cleanup — 2026-10-23
**Task:** Record the user's final Phase 5 Windows run and remove the stale Phase 3 label from the demo.
**Tested by user:** `python -m pip install -e ".[dev]"` succeeded; `python -m pytest -q` reported `61 passed` in 20.24s with one Starlette/httpx deprecation warning; `python eval/stale_facts.py` reported 100% accuracy for both modes, 0% stale error, 0% flat abstention, 25% graph abstention and 3 expanded items; demo handoff readback passed; lifecycle dry run reported zero candidates and no mutation; rebuild of separate empty `demo.db` returned zero nodes; `python scripts/pack.py` created both Phase 5 archives.
**Found:** The demo wrote and displayed `Phase 3` even though the current package is Phase 5.
**Fixed:** Demo now writes `Phase 5`; `tests/test_cli.py` asserts the correct phase label, that the stale label is absent, and that handoff readback succeeds. `scripts/pack.py` includes the new regression test.
**Caveat:** The synthetic evaluation remains a smoke test only, not evidence for or against H1–H7 (D-007). The final label patch needs its own test and package run.

## DBG-006 — Phase 5 evaluation and shadow lifecycle — 2026-10-23
**Task:** Add a reproducible synthetic flat-versus-graph evaluation, lazy decay scoring, a read-only lifecycle dry run, and handoff/readback coverage in the CLI demo.
**Tested:** `PYTHONPATH=src python -m pytest -q` — 60 passed, 1 skipped in 2.10s. The skip is `tests/test_mcp_stdio.py` because the official MCP SDK was unavailable in this builder runtime. `PYTHONPATH=src python eval/stale_facts.py --k 5` ran successfully and reported flat/graph accuracy 100%, stale-fact error 0%, flat abstention 0%, graph abstention 25%, and 3 graph-expanded candidate items. `PYTHONPATH=src python -m agm demo` completed write → correction → retrieve → delete → handoff → readback; the readback passed. `PYTHONPATH=src python -m agm lifecycle --db /tmp/agm-empty-phase5b.db --dry-run` exited 0 and made no view changes. `PYTHONPATH=src python -m compileall -q src tests eval` passed.
**Found:** The graph rank used persisted `decay_weight=1.0`, so recency/use had no effect; the CLI demo stopped before exercising handoff.
**Fixed:** Decay is computed lazily from idle time, usage, `derived_from` citations, corroboration, and pin state; lifecycle only reports candidates below the default 0.30 threshold; demo now saves/resumes a handoff and validates readback. D-019 and D-020 record the provisional formula and evaluation definition.
**Caveat:** The synthetic metrics are not evidence for or against H1–H7 (D-007). Windows Phase 5 verification is pending.

---


> Append-only. Every completed coding task gets an entry here, even "no issues found." Newest entries at top.

## DBG-005 — Phase 4 probation, revocation, handoff and readback — 2026-10-23
**Task:** Implement the high-stakes corroboration gate, replayable writer revocation/rollback, and cross-model handoff save/resume/readback.
**Tested:** `PYTHONPATH=src python -m pytest -q` — 55 passed, 1 skipped in 1.19s. Phase 4 tests assert low-trust facts and episodes are excluded from high-stakes expanded and flat retrieval until independently corroborated; revoking corroboration withdraws that evidence; revocation removes writer-authored items plus recursive `derived_from` descendants and remains stable after rebuild; `since` filters writes; handoff context fits its token budget; readback reports missing decisions/open items and wrong goals; packets are tenant-scoped and reconstructed by replay; REST handoff and admin-revoke routes work.
**Found:** The graph sufficiency gate can abstain on a long task summary with the default hash embedder, even where exact keywords are present; a loose readback overlap could confuse staging with production; the frozen `ResumeResult` could not return actual context.
**Fixed:** Handoff assembly falls back to the flat baseline when graph retrieval abstains; readback matching requires exact normalized containment or at least 0.60 token-set Jaccard similarity; D-016 logs the additive high-stakes parameter and handoff response fields. D-017 records replayable event semantics. `source_span` now creates a `derived_from` edge when its episode node exists.
**Open:** One MCP stdio test is skipped in this builder runtime because its official SDK is not installed, while the user previously ran the Phase 3 MCP test on Windows. Apply the overlay and rerun the full Phase 4 suite on Windows; inspect the package and review revocation's event-log retention behavior.

## DBG-004 — Phase 3 REST/MCP interfaces and guardrails — 2026-10-23
**Task:** Add scoped API-key authentication, REST routes, nine MCP tool names, secret redaction, instruction-like quarantine, examples, and package overlays.
**Tested:** `PYTHONPATH=src python -m pytest -q` — 42 passed, 1 skipped in 0.87s; `PYTHONPATH=src python -m compileall -q src tests` — exit code 0. The skipped test is the official MCP stdio client round-trip because the `mcp` package was not preinstalled.
**Found:** Initial REST tests injected a SQLite connection created in the main thread into TestClient's worker thread, triggering SQLite's thread guard. Attempting `pip install 'mcp>=2,<3'` failed because DNS/network access was unavailable in the builder environment.
**Fixed:** API tests now construct the store inside the FastAPI lifespan on the request thread. The package pins the FastMCP-compatible official `mcp>=1.26,<2` API and includes a conditional stdio integration test to run after installation. Quarantined nodes are filtered from both default retrieve and history surfaces. The packer creates both a workspace ZIP and a root-relative overlay, excludes `.git`, databases, caches, and local key files.
**Open:** Owner must install the Phase 3 dependencies on Windows, run all tests including the MCP stdio test, inspect the overlay archive, and obtain review before considering remote exposure.

## DBG-003 — Phase 2 package and final smoke checks — 2026-10-23
**Task:** Make the packer phase-aware, exclude `.git`, and assemble a local-overlay archive for applying Phase 2 to the complete Windows checkout.
**Tested:** `PYTHONPATH=src python -m pytest -q` — 31 passed in 0.55s; `PYTHONPATH=src python -m compileall -q src tests` — exit code 0; `PYTHONPATH=src python -m agm demo` — exit code 0; `PYTHONPATH=src python -m agm rebuild --db ./demo.db` — exit code 0 and 0 nodes in the separate empty database.
**Found:** The runtime export available to the builder does not contain every existing design document from the owner's repository, so a full-repository snapshot would not be safe as the only handoff artifact.
**Fixed:** `scripts/pack.py` now excludes `.git` and generated files and selects the Phase 2 archive when `PHASE2_REPORT.md` exists. A separate overlay archive includes implementation files and tests without replacing unrelated design files.
**Open:** Owner must run the tests on Windows and have the Phase 2 changes reviewed before `docs/phases.md` is marked complete.

## DBG-002 — Phase 2 graph retrieval and conflict handling — 2026-10-23
**Task:** Implement Phase 2 graph expansion, alias-aware entity identity, provisional trust/ranking, sufficiency and abstention, plus compare-and-swap contested writes.
**Tested:** `PYTHONPATH=src python -m pytest -q` — 31 passed in 0.48s on Python 3.13.5. Regression tests cover flat-baseline parity, one-hop/two-hop bounds, related entity expansion, alias-based writes, ambiguous aliases, stale base versions, trust-gap conflicts, D-008 weights, and deterministic replay of edges, aliases, FTS rows and embeddings after hard deletion.
**Found:** A replay test initially found that entity `created_event` and supersedes edges could differ after the original fact was scrubbed. Further tests found that writes and relation edges through an alias could lose their canonical identity during replay if the alias declaration was deleted.
**Fixed:** Skip edges to absent nodes; recompute alias mappings and FTS entity terms after hard delete; persist resolved canonical identity and relation target IDs in write-event payloads; calculate accepted version chains from active/superseded facts rather than letting contested candidates advance the accepted version.
**Open concerns:** The frozen `RetrieveResult` has no general warnings field, so retrieved conflicts are flagged through `Node.contested_with`; the originating contested `WriteResult` carries the explicit warning. D-008 scoring weights and the 10-year age factor are placeholders and need evaluation/calibration.

## DBG-001 — Docs scaffold consistency check — 2026-10-22
**Task:** Generate context.md and docs/ from Draft v5 (no code written yet).
**Tested:** Script checked that every docs/ file ends with the Next line, no TBD or template placeholders remain, the REST/MCP parity table lists 9 tools matching the Phase 3 brief, and all open items are marked "(open — confirm with user)".
**Found:** Nothing failing. Three open items remain by design: root folder path (context.md, workflow.md) and which hosted clients support custom connectors (trd.md). Contracts themselves are unreviewed by running code, so they may need adjustment once Phase 1 is built.
**Fixed:** None needed.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task — it routes you to the right file for what you are about to do.
