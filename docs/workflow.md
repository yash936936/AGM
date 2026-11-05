# Dev workflow — AGM prototype

## The loop (Claude supervises, ChatGPT builds)
1. **Brief.** Claude (this project's supervisor) confirms the item in `ROADMAP.md`. The user pastes the master prompt and the batch block from `docs/PROMPTS.md` into ChatGPT.
2. **Build.** ChatGPT returns complete files with paths and a self-report (below).
3. **Land.** User saves files into the repo, runs `pytest` and any phase commands, copies full output.
4. **Review.** User gives Claude the diff or files plus test output. Claude checks the review list, then either approves or returns a numbered fix list for ChatGPT.
5. **Log.** After approval: add any decisions, update `status.md`, tick the item in `ROADMAP.md`.
Claude's review list: matches frozen contracts exactly; tests cover each "done when" line; parameterized SQL; no secrets in logs; no scope beyond the phase; no new dependency; D-006 flat-equals-baseline holds; no stdout from library code.

## Builder prompts
Master prompt and per-batch prompts: `docs/PROMPTS.md`. Plan, batches and gates: `docs/BUILD_PLAN.md`. Standing rules for any builder: `AGENTS.md`.

## After each coding task
Update `docs/status.md`. On finishing a roadmap item: update `docs/ROADMAP.md`.

## Supervisor review checklist (updated 2026-10-23, D-023)
Run these yourself; never accept a builder's claim as verified.
1. Install clean, run `python -m pytest -q`, and note skipped tests. A skipped test is an unverified path.
2. **Surface parity:** every behaviour that protects data (redaction, quarantine, tenant scoping, scopes) must hold for the library and REST. Probe the library directly with a key-shaped string and an instruction-like string.
3. **Persistence:** a new mutation must append an event first, replay identically (`rebuild_views`), and have a replay test. Hard delete must leave nothing readable in the `.db` or `-wal` file.
4. Contracts in `docs/architecture.md` unchanged unless a decision says so; no new dependency without a decision.
5. Run `python examples/rest_smoke_client.py`.
6. `git status` clean of `*.db`, `*.db-wal`, `*.db-shm`, `__pycache__`, `*.egg-info`, `dist/`.
7. Evals: the decision rule was written before the run; results include cases where flat wins.
8. Docs updated (`decisions.md`, `status.md`, `ROADMAP.md`) and accurate to what was actually run.
Standing builder rules: `AGENTS.md`. Prompts: `docs/PROMPTS.md`.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
