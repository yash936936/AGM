# M1 increment 1: explicit turn lifecycle API

## Delivered

- `MemoryLifecycle.before_turn()` retrieves tenant/project-scoped evidence via the existing store and renders a bounded, provenance-aware context block.
- `MemoryLifecycle.after_turn()` accepts caller-approved candidate `WriteItem` objects and persists them only through `MemoryStore.write`, retaining existing sanitization, quarantine, idempotency and transaction behavior.
- Typed immutable request/result dataclasses make the lifecycle boundary explicit.
- Tests cover evidence rendering, abstention, guarded/idempotent writes, blank-query validation, and candidate batch limits.

## Deliberate limitations

This increment does not extract memories from free-form conversation, invoke an LLM, authenticate tenant identity, or decide consent/retention policy. The host application must authenticate and construct `Ctx`, obtain any required consent, and approve candidate memories. Never treat retrieved memory text as instructions.

## Apply and verify

Merge `src/agm/lifecycle.py`, `tests/test_lifecycle.py`, and this document into the existing repository, then run:

```bash
python -m pytest -q tests/test_lifecycle.py
python -m pytest -q
python scripts/check_repo_hygiene.py
git diff --check
```

Do not commit until the complete suite and hygiene scan pass.
