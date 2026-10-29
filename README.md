# AGM: Adaptive Graph Memory

AGM is a Python memory layer for AI agents. It stores structured facts, procedures, and episodes, then retrieves relevant memories across turns. Its design combines graph relationships, keyword search, vector similarity, source provenance, and explicit memory lifecycle operations.

AGM is model-agnostic. The calling application supplies structured memory items; AGM does not run an LLM to extract memories. A single core library provides the memory behavior, with REST and Model Context Protocol (MCP) adapters for agent applications.

## What it does

- **Stores persistent memory:** records facts, procedures, and episodes in a local SQLite database.
- **Retrieves relevant context:** combines SQLite FTS5 keyword search with vector similarity, then optionally expands results through bounded graph relationships.
- **Tracks changes over time:** supports superseding facts, viewing entity history, and filtering results by validity time.
- **Preserves provenance and trust:** records source and writer information, supports trust tiers and probation, and retains source-span metadata when supplied.
- **Handles memory lifecycle operations:** supports idempotent writes, contested facts, hard deletion, retention expiry, and writer revocation.
- **Applies input guardrails:** redacts detected secrets and screens instruction-like text before it enters normal memory use.
- **Supports task handoff:** saves task state, assembles bounded context for a target model, and checks readback against the saved goal, decisions, and open items.
- **Exposes agent interfaces:** provides an authenticated local REST API and an MCP server.
- **Includes diagnostics and evaluation tools:** compares flat and graph retrieval, inspects memory consistency, and reports retrieval traces and benchmark measurements.

## How it works

AGM uses an event log as the source of truth. SQLite tables for memory nodes, graph edges, full-text search, and embeddings are materialized views that can be rebuilt by replaying the event log.

A retrieval request starts with keyword and vector search. AGM can then expand the candidate set through bounded graph traversal, apply scope and validity filters, rank the results, and abstain when the available evidence does not meet its sufficiency threshold. Returned memories are data, not instructions.

The core store is shared by the REST and MCP adapters. This keeps memory operations in one library rather than implementing separate memory logic for each interface.

## Technology

- Python 3.11 or newer
- SQLite with FTS5
- NumPy
- Pydantic
- FastAPI and Uvicorn for REST
- MCP Python SDK for MCP integration

The default embedder uses hashing and does not require downloading a model. A Sentence Transformers embedder is available as an optional integration. OpenAI and Google Gemini packages are optional extras for client-side integrations; the core memory store does not require an LLM API.

## Install

Create and activate a virtual environment, then install AGM with its development dependencies:

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

python -m pip install -e ".[dev]"
```

## Run the demo

```bash
python -m agm demo
```

The demo creates a temporary database and shows memory writes, retrieval, superseding and deleting a memory, plus task handoff and readback.

## Command-line interface

AGM provides commands for running the demo, rebuilding SQLite views, creating a local owner key file, starting the REST or MCP interface, inspecting lifecycle candidates, and diagnosing retrieval.

```bash
python -m agm --help
python -m agm demo
python -m agm rebuild --db ./agm.db
python -m agm bootstrap-owner --tenant my-tenant
python -m agm serve-api --keys ./agm.keys.json --db ./agm.db
python -m agm serve-mcp --transport stdio --db ./agm.db
python -m agm lifecycle --db ./agm.db --dry-run
python -m agm doctor --db ./agm.db --tenant my-tenant
```

The REST API binds to loopback by default. Remote host binding is disabled by the current configuration. Protect the owner key file as a secret and do not commit it to version control.

## Interfaces and data

The Python library exposes the `MemoryStore` API for writing, retrieving, superseding, reading history, deleting, expiring, revoking writers, rebuilding views, and managing handoff packets.

The REST API and MCP server expose memory and handoff operations through their respective interfaces. The MCP server supports standard input/output transport and streamable HTTP. The default database is a local SQLite file, so AGM does not require a separate database service.

## Evaluation

The repository includes retrieval diagnostics and synthetic evaluation and benchmark tools. These help inspect behavior and compare retrieval modes under controlled workloads. Synthetic results are prototype measurements and should not be interpreted as evidence of performance on real user histories.

## Development checks

Install development dependencies and run the test suite:

```bash
python -m pytest -q
python examples/rest_smoke_client.py
python examples/mcp_smoke_client.py
python scripts/pack.py
```

## Project status

AGM is a research and development prototype for agent memory. It provides a local memory store, retrieval and lifecycle operations, REST/MCP interfaces, handoff support, and diagnostics. It is not presented as a production-ready hosted service or as a validated replacement for a model's native context handling.
