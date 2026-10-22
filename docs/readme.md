# AGM — Adaptive Graph Memory (prototype)

AGM is a local-first memory layer for AI agents. It stores memories in an event-sourced SQLite core, supports supersession and bounded graph retrieval, ranks with provisional trust/confidence/decay signals, and exposes authenticated REST and MCP interfaces. Handoff packets let one model pass task context to another.

## Current status

Phases 1–5 are implemented and the user has verified the integrated Phase 5 suite on Windows: 61 tests passed in 20.24 seconds. The project includes a synthetic flat-versus-graph smoke evaluation, lazy decay scoring, a read-only lifecycle dry run, and a demo with handoff/readback. The evaluation is not evidence for or against H1–H7 (D-007). The evaluation is not evidence for or against H1–H7 (D-007). Confidence, ranking, and decay coefficients are provisional and uncalibrated.

## Setup

Python 3.11+, SQLite with FTS5, and pip are required. See the root [`README.md`](../README.md) for installation, API, MCP, demo, evaluation, and lifecycle commands.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task — it routes you to the right file for what you are about to do.
