# AGM Phase 1

A small SQLite-backed adaptive graph memory prototype. Phase 1 supports episodes, facts, procedures, fact correction/supersession, hard deletion, and flat retrieval.

## Install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

SQLite must include FTS5, which AGM checks when opening a store.

## Test

```bash
pytest -q
```

## Demo and rebuild

```bash
python -m agm demo
agm rebuild --db ./demo.db
python scripts/pack.py
```

The append-only event log is the source of truth. Derived tables can be rebuilt using `rebuild_views()`. Phase 1 deliberately does not implement graph expansion, trust rules, aliases, or handoff flows.
