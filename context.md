# AGM context (router)

AGM = Adaptive Graph Memory: event-sourced, model-agnostic memory layer for agents. Spec: `docs/SPEC_v5.md`. Version 0.7.0, local-only prototype. Interfaces: Python library, REST, stdlib client (`agm.client`), CLI incl. `agm mem|handoff|connect` (MCP removed, D-042). New to the project? `docs/QUICKSTART.md`.

Read order for any contributor or agent: `AGENTS.md` (rules, invariants) → this file → `docs/status.md` → `docs/ROADMAP.md`. Batch work: `docs/BUILD_PLAN.md` and `docs/PROMPTS.md`.

| If you are about to… | Read |
|---|---|
| change a contract, model, route or CLI command | `docs/architecture.md`, then add a `D-0NN` entry to `docs/decisions.md` first |
| understand why something is the way it is | `docs/decisions.md` |
| change retrieval, trust or lifecycle | `docs/code_logic.md`, `docs/trd.md` |
| work on active memory / turn loop | `docs/active_memory.md` |
| start or review a build batch | `docs/BUILD_PLAN.md` (plan, gates, review checklist), `docs/PROMPTS.md` (paste into the builder) |
| add or run benchmarks | `docs/core_benchmarking.md`, `docs/benchmarks/` |
| prepare a release or review | `docs/acceptance/` |
| plan remote deployment | `docs/cloud-deployment.md` |
| check a connection works | `examples/rest_smoke_client.py` |

Commands: `python -m pip install -e ".[dev]"`, `python -m pytest -q`, `python scripts/check_repo_hygiene.py`, `python scripts/check_package.py`.

Truthfulness rule: never claim a test passes unless you ran it; write NOT RUN otherwise. Synthetic results are not evidence for H1–H7 (D-007).
