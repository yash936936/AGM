# Dev workflow — AGM prototype

Root folder (identical across all tools): (open — confirm with user)

## The loop (Claude supervises, ChatGPT builds)
1. **Brief.** Claude (this project's supervisor) confirms the phase in `phases.md`. The user copies the **builder prompt** below plus that phase's section and `architecture.md` into ChatGPT.
2. **Build.** ChatGPT returns complete files with paths and a self-report (below).
3. **Land.** User saves files into the repo, runs `pytest` and any phase commands, copies full output.
4. **Review.** User gives Claude the diff or files plus test output. Claude checks the review list, then either approves or returns a numbered fix list for ChatGPT.
5. **Log.** After approval: append `debug.md`, add any decisions, update `status.md`, mark the phase in `phases.md`.
Claude's review list: matches frozen contracts exactly; tests cover each "done when" line; parameterized SQL; no secrets in logs; no scope beyond the phase; no new dependency; D-006 flat-equals-baseline holds; stdout untouched in MCP stdio mode.

## Builder prompt (paste into ChatGPT, then add the phase section and architecture.md)
> You are the builder for the AGM prototype. A supervisor (Claude) wrote the specs; you write the code.
> Rules:
> 1. Build ONLY the phase pasted below. Do not start later phases or add features.
> 2. The contracts in architecture.md are frozen. Match names, fields and types exactly. If a contract looks wrong, do not change it: list it under "Contract concerns" and build to the contract.
> 3. Allowed dependencies are in trd.md. Do not add others.
> 4. Use parameterized SQL only. Never print to stdout in MCP stdio code; log to stderr.
> 5. Write tests for every "Done when" line.
> 6. Return complete files, each under a heading with its repo path. No partial snippets, no "rest unchanged".
> 7. End with a self-report: files created, what each test proves, commands I should run, what you did NOT run or verify, contract concerns, any assumption you made.
> Do not claim tests pass unless you actually ran them; say "not run" if you could not.

## After each coding task
Append `docs/debug.md`, update `docs/status.md`. On finishing a phase: update `docs/phases.md` and `docs/readme.md`.

## Supervisor review checklist (updated 2026-10-23, D-023)
Run these yourself; never accept a builder's claim as verified.
1. Install clean, run `python -m pytest -q`, and note skipped tests. A skipped MCP test means the MCP path is unverified.
2. **Surface parity:** every behaviour that protects data (redaction, quarantine, tenant scoping, scopes) must hold for the library, REST and MCP. Probe the library directly with a key-shaped string and an instruction-like string.
3. **Persistence:** a new mutation must append an event first, replay identically (`rebuild_views`), and have a replay test. Hard delete must leave nothing readable in the `.db` or `-wal` file.
4. Contracts in `docs/architecture.md` unchanged unless a decision says so; no new dependency without a decision.
5. Run `python examples/mcp_smoke_client.py` and `python examples/rest_smoke_client.py`.
6. `git status` clean of `*.db`, `*.db-wal`, `*.db-shm`, `__pycache__`, `*.egg-info`, `dist/`.
7. Evals: the decision rule was written before the run; results include cases where flat wins.
8. Docs updated (`debug.md`, `decisions.md`, `status.md`) and accurate to what was actually run.
Standing builder rules: `AGENTS.md`. Prompt for ChatGPT: `prompts/builder_system_prompt.md`. Brief template: `prompts/phase_brief_template.md`.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
