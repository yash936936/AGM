# Status — AGM prototype

> Updated every run. Newest entry at top.

## 2026-10-23 — Supervisor review and hardening (v0.5.1)
**Current phase:** Phase 5 complete; hardening patch 0.5.1 applied by the supervisor.
**Last debug:** DBG-008, review findings and fixes.
**Last decisions:** D-021 (guard in core), D-022 (WAL checkpoint and secure_delete), D-023 (standing builder guidelines).
**Validation:** supervisor environment `97 passed` (Linux, Python 3.12); both smoke clients pass. Windows rerun pending.
**Next up:** (1) user applies the patch, runs `python -m pytest -q` and both smoke clients on Windows; (2) connect the real host (Claude Code over stdio) using `examples/claude_code_mcp.md`; (3) Phase 6 builder prompt, package B only (evaluation v2 with the pre-declared decision rule).

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
