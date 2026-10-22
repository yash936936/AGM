# AGM Phase 4 implementation report

**Status:** Implemented in the builder workspace. Windows verification is pending.

## 1. Files created or updated

- `src/agm/handoff.py` — lexical readback comparison helper.
- `src/agm/store.py` — high-stakes retrieval gate, source-span `derived_from` edges, replayable revocation, handoff save/resume/readback.
- `src/agm/trust.py` — independent corroboration rollback tracking and probation predicate.
- `src/agm/retrieve.py` — high-stakes gate applied before both graph seeding and expansion.
- `src/agm/models.py` — additive `ResumeResult` context/budget fields.
- `src/agm/api.py` — `high_stakes` REST input; existing handoff and admin revoke routes now call the implemented core.
- `src/agm/mcp_server.py` — `high_stakes` MCP argument and Phase 4 tool descriptions.
- `src/agm/__init__.py`, `pyproject.toml` — version 0.4.0.
- `tests/test_trust.py` — four probation, corroboration, revocation and `since` tests.
- `tests/test_handoff.py` — six budget, readback, tenant and replay tests.
- `tests/test_e2e_rest.py` — Phase 4 handoff REST round trip and admin revoke route tests.
- `scripts/pack.py` — phase-aware safe source and overlay ZIP packaging.
- `README.md`, `context.md`, `docs/decisions.md`, `docs/debug.md`, `docs/phases.md`, `docs/readme.md`, `docs/status.md` — project docs and logs.
- `docs/phase4_contract_addendum.md` — explicit record of the Phase 4 contract additions.

## 2. What the Phase 4 tests prove

1. Low-trust (`trusted_agent` and `untrusted`) items are absent from high-stakes retrieval until a different writer corroborates the same active fact; this is checked for expanded and flat retrieval.
2. Revoking a writer who supplied corroboration removes that corroboration from the trust calculation.
3. Writer revocation removes its own memory and recursive `derived_from` descendants, including their FTS rows and embeddings, and remains deterministic after view rebuild.
4. The `since` argument filters writer items by their source event's creation timestamp.
5. Handoff context contains pinned memory, task state and relevant retrieved memory in that order when space permits.
6. Handoff resume limits context to the stated rough token budget (`ceil(chars / 4)`).
7. Readback reports an incorrect goal, missing decisions and missing open items.
8. Readback passes when goal, decisions and open items match the saved packet.
9. Handoff packets are restored by replaying `handoff_save` events.
10. A packet is not accessible from a different tenant.
11. The REST API can save/resume/read back a packet, and an API identity with `admin` scope can revoke a writer.
12. Low-trust episodes (which do not have entity/attribute/value tuples) can leave probation after an independent writer stores the exact same text.
13. Existing Phase 1/2/3 regression tests remain green in this environment.

## 3. Commands run and actual output

- `PYTHONPATH=src python -m compileall -q src tests` — `compileall: PASS`, exit code 0.
- `PYTHONPATH=src python -m pytest -q` — `55 passed, 1 skipped in 1.19s`.
  - `tests/test_mcp_stdio.py` was skipped because the official `mcp` dependency is not installed in this builder runtime. The user previously reported that Phase 3's MCP stdio test ran as part of a Windows test run, but Phase 4 MCP behavior must be rerun on the user's checkout.
- `PYTHONPATH=src python -m agm demo` — exit code 0. Printed current Phase 3 demo fact, the superseded draft, and successful deletion of the old draft.
- `PYTHONPATH=src python -m agm rebuild --db ./phase4-demo.db` — `Rebuilt views: 0 nodes`, exit code 0. This was a new, empty database; zero is expected and is not a populated-database replay assertion.
- `python scripts/pack.py` — run after this report is saved; actual package output is recorded by the command and should be checked against the archive listing.

## 4. Contract concerns

- **D-016 is an explicit additive change to the frozen contract.** `retrieve` gains optional `high_stakes: bool = False`; `ResumeResult` gains `context`, `readback_prompt`, `target_model`, `token_budget`, and `estimated_tokens`. Existing fields/default retrieval behavior remain unchanged. See `docs/phase4_contract_addendum.md`.
- Confidence/ranking values remain uncalibrated. High-stakes probation only applies when a caller explicitly passes `high_stakes=True`.
- Readback comparison is lexical: exact normalized containment or token-set Jaccard similarity >= 0.60. It is not proof of semantic understanding.
- Token budget uses the documented rough estimate of four characters per token, not a model tokenizer. `readback_prompt` is returned separately and does not count toward `estimated_tokens`.
- Revocation retains the original source event payloads in the event log for audit while removing searchable views and dependent items. It is not a hard delete; use `delete` when payload scrubbing is required.

## 5. Assumptions

- A `trusted_agent` or `untrusted` fact is considered probationary in high-stakes mode until at least one independent writer confirms the same active fact.
- A source-span ID creates a `derived_from` graph edge only when it resolves to an episode node in the same tenant.
- `since` filters on event creation time, not `valid_from`.
- Readback uses the frozen fields (goal, decisions, open items) and does not compare plan/progress/files/tools.
- The packet is tenant-scoped; the frozen `Packet` contract does not include a project field.

## 6. Not finished / next verification

- Run the overlay on Windows and verify the complete test suite after the user's installed MCP SDK is available. Expect the stdio test to run instead of skip.
- Inspect both archives and ensure `.git`, `.venv`, database files, `agm.keys.json`, and caches are excluded.
- Review the event-log retention choice for revocation before treating it as equivalent to deletion or enabling remote service exposure.
- Phase 5 evaluation and lifecycle features are out of scope.
