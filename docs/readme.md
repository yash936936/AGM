# AGM — Adaptive Graph Memory prototype

AGM is a local-first memory layer for AI agents. The current implementation includes an event-sourced SQLite core, graph-aware retrieval, explicit conflicts, provisional trust ranking, authenticated REST routes, nine MCP tools, pre-storage input guardrails, high-stakes probation checks, writer revocation and model handoff.

## Current state

- Phase 1 and Phase 2 passed the user's Windows test runs (10/10 and 31/31 respectively).
- Phase 3 passed the user's Windows suite (43 passed in 15.15s); authenticated REST write/retrieve, health check and invalid-key rejection were also verified.
- Phase 4 is implemented in the current builder workspace. The builder suite reports 54 passed and 1 skipped because the MCP SDK is unavailable in that environment; the Windows Phase 4 test run remains pending.
- Mini evaluation and lifecycle management remain Phase 5 work.

## Setup

Python 3.11+, SQLite with FTS5, and `python -m pip install -e ".[dev]"`. For REST, copy `examples/agm.keys.example.json` to `agm.keys.json` and replace sample keys. Run `python -m agm serve-api --db ./agm.db --keys ./agm.keys.json`. For local MCP stdio, set `AGM_TENANT`, `AGM_WRITER`, `AGM_TIER`, `AGM_DB_PATH`, and `AGM_SCOPES`, then run `python -m agm serve-mcp --transport stdio`.

Services bind to loopback only. Guard rules are pattern-based; they do not guarantee detection of every secret or injection attempt. Scores remain uncalibrated placeholders.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task — it routes you to the right file for what you are about to do.
