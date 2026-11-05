# AGM — Adaptive Graph Memory

A Python memory layer for AI agents. Event-sourced SQLite core; graph, keyword and vector retrieval; provenance, trust tiers, lifecycle (supersede, delete, expire, revoke) and task handoff. Model-agnostic: the caller supplies structured memories, AGM never calls an LLM.

**Status:** research prototype, v0.7.0, local-only (loopback). Not production-ready; see [`docs/ROADMAP.md`](docs/ROADMAP.md) and [`docs/status.md`](docs/status.md).

## Interfaces

- **Python library:** `agm.MemoryStore`
- **REST API:** FastAPI, `X-API-Key` auth, OpenAPI at `/docs` (works with any HTTP-capable agent, ChatGPT Actions, curl)
- **Python client:** `from agm import AgmClient` (standard library only)
- **CLI:** `python -m agm …`, including `mem` / `handoff` wrappers for shell-based agents (Claude Code, Codex) `connect` to issue a scoped agent key, and `active` read-only context helpers

MCP was removed in v0.6.0 (decision D-042). See [`docs/QUICKSTART.md`](docs/QUICKSTART.md) to connect an agent in 5 minutes.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m agm demo                                  # offline write/retrieve/correct/delete/handoff demo
python -m pytest -q
```

Run the API:

```bash
python -m agm bootstrap-owner --tenant my-tenant    # creates agm.keys.json (keep secret, never commit)
python -m agm serve-api --keys ./agm.keys.json --db ./agm.db
python examples/rest_smoke_client.py
```

Other commands: `rebuild`, `lifecycle --dry-run`, `doctor`. Examples: `examples/python_client.py`, `examples/curl.md`, `examples/chatgpt_actions.md`.

## How it works

The event log is the source of truth; node, edge, FTS5 and embedding tables are views rebuildable by replay. Retrieval = keyword + vector seeds → bounded graph expansion → scope/validity filters → ranking → abstain when evidence is insufficient. Guarding (secret redaction, instruction-like-text quarantine) runs inside the core for every caller. Retrieved memory is data, never instructions.

## Layout

```
src/agm/     core library, REST adapter, CLI
tests/       pytest suite
eval/        synthetic benchmarks and stale-fact evaluation
scripts/     repo hygiene, package check, real-history evaluator
examples/    clients and sample data
docs/        ROADMAP, status, architecture, decisions, spec, acceptance protocols
```

Start with `context.md` if you are an agent or contributor.

## Limits

Synthetic benchmark numbers are smoke tests, not evidence for the design hypotheses (D-007). Real-history evaluation, independent security review and third-party host integration are open. Services refuse non-loopback binds until that review is done.

## License

Apache License 2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
