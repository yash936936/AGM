# AGM Phase 1 Report

## 1. Files created
- `pyproject.toml` - package metadata, runtime dependencies, and CLI entry point.
- `README.md` - install, test, demo, and rebuild instructions.
- `scripts/pack.py` - stdlib-only source archive builder.
- `src/agm/__init__.py` - public exports.
- `src/agm/__main__.py` - `python -m agm` entry point.
- `src/agm/models.py` - Pydantic v2 contracts and result models.
- `src/agm/db.py` - SQLite schema, WAL, foreign keys, and FTS5 check.
- `src/agm/events.py` - HLC, append-only events, idempotency lookup, payload decoding.
- `src/agm/embed.py` - deterministic 256-dimensional BLAKE2b feature-hash embedder.
- `src/agm/store.py` - writes, supersession, flat retrieval, history, delete, and replay.
- `src/agm/cli.py` - `demo` and `rebuild` commands.
- `tests/test_store.py` - nine behavior tests.
- `tests/test_replay.py` - deterministic replay test.

## 2. What the 10 tests prove
1. **Write/retrieve:** a fact can be written and returned by a related natural-language query.
2. **Correction/supersession:** a corrected single-valued fact replaces the current version, both are available in superseded mode, and history is chronological.
3. **Idempotency:** repeating a key returns the original result and creates one node.
4. **No-op:** writing the currently active identical single-valued fact creates no duplicate.
5. **Multi-valued facts:** multiple values for the same attribute remain active.
6. **Hard delete/scrub:** node, FTS row, embedding, and connected edges are removed; retrieval cannot return the item; its source event payload no longer holds deleted text.
7. **Replay:** after writes, correction, and deletion, node rows and embedding blobs match before and after rebuild.
8. **As-of retrieval:** a query timestamp before a correction returns the prior value.
9. **FTS sanitization:** hostile FTS-looking query text is tokenized instead of being interpreted as FTS syntax.
10. **Required entity:** a fact without an entity raises `ValueError`.

## 3. Commands run
Environment observed: Python 3.13.5, SQLite 3.46.1 with FTS5, pydantic 2.13.5, NumPy 2.3.5, pytest 9.0.2.

- `PYTHONPATH=src python -m pytest -q` - **PASS**
  ```
  10 passed in 0.25s
  ```
- `python -m venv .venv` - **NOT RUN** (existing managed Python environment was used).
- `source .venv/bin/activate` - **NOT RUN** (no project-local virtual environment created).
- `pip install -e ".[dev]"` - **NOT RUN** (the required dependencies were already installed; install isolation was not checked).
- `PYTHONPATH=src python -m pytest -q` - **PASS**
  ```
  10 passed in 0.25s
  ```
- `python -m agm demo` - **PASS**, exit 0
  ```
  Current memories:
    agm.phase = Phase 1 [generated node id]
  Including superseded memories:
    Phase 1 [generated node id]
    draft [generated node id]
  Delete old draft: True; replacement: [generated node id]
  ```
- `python -m agm rebuild --db ./demo.db` - **PASS**, exit 0
  ```
  Rebuilt views: 0 nodes
  ```
  (The database was newly created and empty, so zero nodes is expected.)
- `python scripts/pack.py` - **PASS**, exit 0
  ```
  Created /mnt/data/agm/dist/agm-phase1.zip (18638 bytes)
  ```
- `python -m venv .venv` - **NOT RUN** (the execution environment already provides a managed Python environment).
- `source .venv/bin/activate` - **NOT RUN** (no project-local virtual environment was created).
- `pip install -e ".[dev]"` - **NOT RUN** (dependencies were preinstalled; editable installation was not independently verified).
- `agm rebuild --db ./demo.db` as a direct shell command - **NOT RUN** (the `agm` console script was not installed; the equivalent `python -m agm rebuild --db ./demo.db` passed).

## 4. Contract concerns
- The frozen schema declares `UNIQUE(tenant, writer_id, idem_key)`. SQLite allows multiple rows where `idem_key` is `NULL`, which matches the requirement that missing keys do not deduplicate.
- The frozen public `RetrieveResult.items` shape is expressed structurally rather than as a named contract class. `Node` is provided as a Pydantic model with the stated fields.
- The schema includes `entity_aliases` and `packets`, but Phase 1 does not implement alias or handoff behavior as specified.

## 5. Assumptions
- A temporal `as_of` retrieval includes superseded nodes so that prior values can be returned for timestamps before their `valid_to`.
- Entity canonical form is `strip()`, lowercase, and collapsed whitespace.
- Entity row IDs are deterministic per tenant and canonical entity, which enables replay to rebuild identical entity references. Node IDs are stored in event payloads.
- `usage_count` and `last_used` are mutable retrieval telemetry and reset to replay defaults because the append-only event log only records memory mutations, not read telemetry.
- Delete events store only an item ID; deleted content is scrubbed from the originating mutation payload before the delete event is appended.
- FTS candidates and embedding candidates are each capped at 50; result scores use min-max normalization over the union candidate set.

## 6. Scope not finished
- The phase-N methods are stubs raising `NotImplementedError("Phase N")`.
- Graph expansion, widening, contested writes, trust-gap rules, base-version enforcement, redaction, quarantine logic, aliases, and relation edges are intentionally not implemented.
- The current implementation has only the tests listed in the brief; additional concurrency and long-running storage tests are not included.
