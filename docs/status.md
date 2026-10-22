# Status — AGM prototype

> Updated every run. Newest entry at top.

## 2026-10-23 — Phase 2 implementation built; awaiting local verification
**Current phase:** Phase 2 — graph layer, ranking, abstention.
**Last debug:** DBG-002, Phase 2 graph retrieval, conflict handling, alias replay and ranking tests.
**Last decisions:** D-011 to D-013 (event-stable entity identity, evidence-based abstention gate, provisional age factor).
**Validation:** `PYTHONPATH=src python -m pytest -q` passed 31 tests in 0.57s on Python 3.13.5 in the builder environment. `compileall`, the demo, and the rebuild CLI also exited successfully. The user has not yet rerun the Phase 2 suite on Windows.
**Next up:** extract `dist/agm-phase2-overlay.zip` over the local AGM checkout, run `python -m pytest -q`, `python -m agm demo`, `python -m agm rebuild --db ./demo.db`, and `python scripts/pack.py`; review the output before marking Phase 2 done.

## 2026-10-22 — Phase 1 implementation verified by user
**Validation:** the user reported `10 passed in 5.06s` on Windows Python 3.14.7, and the demo and rebuild commands exited successfully. The first package listing exposed `.git` content, so the packer excludes `.git` and other generated directories.

## 2026-10-22 — Docs scaffolded from Draft v5
**Current phase:** Phase 1 — Core store and event log.
**Last debug:** DBG-001, docs consistency check.
**Last decisions:** D-001 to D-008 logged.
**Next up:** code, test, and review one phase at a time.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task — it routes you to the right file for what you are about to do.
