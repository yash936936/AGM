# Debug log — AGM prototype

> Append-only. Every completed coding task gets an entry here, even "no
> issues found." Newest entries at top.

## DBG-008 — Supervisor review: guard in core, delete durability, repo hygiene, connection smoke tests — 2026-10-23
**Task:** Independent review of the pushed Phase 5 repo (cloned, installed, run), then fix what it found.
**Tested (supervisor environment, Linux, Python 3.12, MCP SDK installed):** baseline `62 passed`. Probes: direct-library write of key-shaped strings (7 formats) and an injection string; REST write of the same; cross-tenant read; scope checks; unanswerable query; delete then raw-byte scan of `.db`/`-wal`; revoke then view and event scan. After fixes: `97 passed`. Mutation check: with the WAL checkpoint removed, `test_deleted_marker_is_gone_from_disk_while_store_is_open` fails. `python examples/mcp_smoke_client.py` 12/12 and `python examples/rest_smoke_client.py` 11/11 against freshly launched server processes.
**Found:** (1) Guard ran only in REST/MCP; the library stored secrets raw and did not quarantine (redactions 0, status added). (2) `supersede` `reason` and `handoff_save` task state were stored unredacted on every surface. (3) Deleted text remained readable in the `-wal` file until a checkpoint. (4) `agm.db-wal`, `agm.db-shm`, `demo.db`, `__pycache__`, `*.egg-info` and `dist/*.zip` were tracked; `.gitignore` `*.db` did not match `-wal`/`-shm`; `pack.py` would have zipped them. (5) `examples/claude_code_mcp.md` still said handoff tools were not implemented. (6) Not a bug, corrected assumption: revocation keeps event payloads for audit by design; my first revoke test wrongly expected a purge.
**Fixed:** D-021, D-022, D-023; new `tests/test_guard_core.py` (library-direct, 7 secret formats across episode, fact value, relation target, supersede reason, task state; quarantine; replay; REST parity), `tests/test_delete_ondisk.py`, `tests/test_smoke_clients.py`; `.gitignore` and `pack.py` exclusions; tracked artifacts untracked with `git rm --cached`; example doc corrected.
**Not verified:** the smoke clients use the official MCP Python client, not Claude Code, Claude Desktop or ChatGPT themselves. Windows was not re-run. Whether hosted Claude or ChatGPT plans accept a custom connector is unchecked. The Phase 5 synthetic eval remains a smoke test (D-007, D-020).

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
