# AGM M1 Increment 1 — Turn Lifecycle API

Extract this ZIP into the root of your existing AGM repository and merge its directories.

Files:
- `src/agm/lifecycle.py`
- `tests/test_lifecycle.py`
- `docs/M1_INCREMENT_1_TURN_LIFECYCLE.md`

Run:

```bash
python -m pytest -q tests/test_lifecycle.py
python -m pytest -q
python scripts/check_repo_hygiene.py
git diff --check
```

This is an overlay for the existing `main` baseline, not a replacement repository. It does not modify the public API exports in `src/agm/__init__.py`; import with `from agm.lifecycle import ...` for this increment.
