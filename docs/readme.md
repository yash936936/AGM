# AGM — Adaptive Graph Memory (prototype)

AGM is a model-agnostic memory layer for AI agents. Phase 1 adds an append-only SQLite event log, a temporal fact store, corrections, hard deletion, and flat retrieval. Phase 2 adds entity-aware graph expansion, alias resolution, provisional confidence/trust ranking, contested writes, and query abstention.

## Status

Phase 1 passed 10 tests on the user's Windows environment. Phase 2 currently passes 31 tests in the builder environment (Python 3.13.5); Windows validation and supervisor approval remain pending. D-008 confidence and ranking coefficients remain uncalibrated placeholders.

## Setup

Python 3.11+, SQLite with FTS5, `pydantic>=2`, `numpy`, and `pytest` for tests:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m agm demo
```

`retrieve(expand=False)` preserves the flat baseline. The default graph-enabled path performs bounded expansion, trust-aware ranking, one widening attempt and abstention when evidence remains weak. REST/MCP interfaces, redaction, quarantine, and handoff are not implemented yet.

## Structure

See `docs/architecture.md` for frozen contracts and `docs/phases.md` for scope and status.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task — it routes you to the right file for what you are about to do.
