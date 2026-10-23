# AGENTS.md — standing rules for any agent that writes code in this repo

Applies to ChatGPT, Codex, Claude Code or any other builder. Read this file, then `context.md`, then `docs/status.md`, before changing anything. If you cannot read files (for example in a chat window), ask the user to paste `AGENTS.md`, `context.md`, `docs/status.md`, `docs/architecture.md` and your phase brief. Do not guess their contents.

## Roles
- **Supervisor (Claude)** writes specs, contracts and phase briefs, and reviews your work by running it.
- **Builder (you)** implements exactly the brief you are given.
- **User** integrates your output, runs tests on their machine and decides open questions.

## Truthfulness (most important)
1. Never say a test passes unless you ran it in this session. Otherwise write `NOT RUN`.
2. Quote real command output. Never paraphrase or invent numbers, counts or timings.
3. List every skipped test and why. A skipped test is an unverified path, not a pass.
4. If you could not run something (no code execution, missing dependency), say so first, before describing the code.
5. Report what you did NOT finish and what you assumed. Hidden assumptions are the main cause of review failures.

## Scope
- Implement only the brief. No drive-by refactors, renames, formatting sweeps or extra features.
- If the brief is ambiguous or conflicts with a frozen contract, build to the contract, keep old names working, and list it under "Contract concerns". Do not silently pick a design.
- Ask one clarifying question only when a wrong guess would waste a full cycle; otherwise state your assumption and continue.

## Invariants (never break these; the supervisor will probe each one)
1. **Guard in the core.** Secret redaction and instruction-like-text quarantine run inside `MemoryStore` for every caller. Adapters (REST, MCP, CLI) contain no safety logic. Any new method that persists user-supplied strings must sanitize them (use `agm.guard.sanitize_value`) and needs a test that calls the library directly, not through REST or MCP.
2. **Event log first.** Every mutation appends an event, then updates views. Views must be rebuildable by `rebuild_views()` and give identical results. Every new mutation needs a replay test.
3. **Deletion vs revocation.** `delete` is a hard purge (content, derived data, original event payload scrubbed, WAL flushed). `revoke_writer` is a rollback: views are cleared but events are kept for audit. Do not blur them.
4. **Frozen contracts** in `docs/architecture.md` (models, REST paths, MCP tool names, CLI commands). Changing one needs a numbered entry in `docs/decisions.md` first.
5. **Loopback only.** Services refuse non-loopback hosts until a separate security review approves remote exposure.
6. **SQL and search safety.** Parameterized SQL only. FTS5 query text is tokenised and quoted, never passed raw.
7. **No stdout** from library or MCP stdio code. Log to stderr. Only `cli.py` prints.
8. **Retrieved memory is data, never instructions.** Keep the untrusted-data notice on every retrieval.
9. **Tenant isolation.** Every query filters by tenant. Add a cross-tenant test for any new read path.
10. **No new dependency** without a decisions entry. `sentence-transformers` may be an optional lazy import in eval only.
11. **Prototype numbers are not evidence** for hypotheses H1–H7 (D-007). Evaluation rules are written into `docs/decisions.md` before results exist, and results must include cases where the simple baseline wins.

## Repository hygiene
- Never commit `*.db`, `*.db-wal`, `*.db-shm`, `__pycache__`, `*.egg-info`, `dist/`, `.venv`, `agm.keys.json`, `.env`. Check `git status` before proposing a commit.
- Do not edit or delete past entries in `docs/decisions.md`, `docs/debug.md`, `docs/status.md`. Add new ones at the top.

## Logging (after every task)
- `docs/debug.md`: what you ran, what failed, what you fixed, what you did not verify.
- `docs/decisions.md`: any design choice, with why and what it affects. Use the next free `D-0NN`.
- `docs/status.md`: current state and next step.

## Commands
```
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m pytest -q
python examples/mcp_smoke_client.py
python examples/rest_smoke_client.py
python eval/stale_facts.py
python scripts/pack.py
```

## How to deliver
- Return **complete files**, each under a heading with its repo path. No snippets, no "rest unchanged". If the change is large, also provide a unified diff.
- If you can run code: run the commands above and paste the real output. If you cannot: mark each `NOT RUN` and tell the user exactly what to run.
- Finish with `PHASE<N>_REPORT.md` (or `REPORT_<date>.md` for non-phase work) containing: files changed; what each new test proves; commands with real output or NOT RUN; contract concerns; assumptions; unfinished items.

## What the supervisor will check
Clean install and full test run; direct-library probes of the guard; surface parity across library, REST and MCP; replay identity; on-disk delete; tenant isolation; both smoke clients; `git status` hygiene; whether your report matches what actually ran.
