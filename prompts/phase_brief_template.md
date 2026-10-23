# Phase brief template (supervisor fills this in; the user pastes it to the builder together with `prompts/builder_system_prompt.md` rules or AGENTS.md)

## Phase <N> — <name>
**Goal:** <one sentence, outcome not activity>

**Context to read first:** `AGENTS.md`, `context.md`, `docs/status.md`, `docs/architecture.md`, <other files>

**Problem or motivation:** <what is wrong or missing today, with evidence such as a failing probe or a review finding>

### Scope (in)
- <file or behaviour>: <exact required behaviour, including edge cases>

### Scope (out — do not build)
- <explicitly deferred items>

### Contracts touched
- <names and signatures that change, or "none". New fields must be backwards compatible.>

### Invariants that this change must preserve
- Guard in core, event log first and replayable, delete vs revoke semantics, tenant isolation, loopback only (see `AGENTS.md`).

### Tests required (one per line; every "done when" must be covered)
1. <behaviour> — library-direct and, where relevant, through REST and MCP
2. <failure path>
3. Replay identity if anything mutates state
4. Cross-tenant test if anything reads state

### Pre-declared acceptance rule (for evaluations only)
<thresholds and verdict wording, written into `docs/decisions.md` BEFORE any result is produced>

### Commands the user will run
```
python -m pip install -e ".[dev]"
python -m pytest -q
<phase-specific commands>
```

### Report must include
Files changed; what each new test proves; real command output or NOT RUN; skipped tests; contract concerns; assumptions; unfinished items.

### Supervisor's review plan (so the builder can self-check)
<the probes the supervisor will run, e.g. direct-library secret write, raw-byte scan after delete, smoke clients>
