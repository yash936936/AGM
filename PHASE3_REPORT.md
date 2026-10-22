# AGM Phase 3 Report

**Scope:** Local REST API, MCP tool adapter, API-key scopes, secret redaction, instruction-like quarantine, examples and packaging.

**Review status:** Implemented in the builder workspace. The REST and guard tests pass. The full MCP stdio integration test is included but skipped in this workspace because the official `mcp` SDK is not installed and this environment could not reach the package index. Phase 3 must not be marked complete until that test runs successfully on the user's machine and the resulting patch is reviewed.

## Files created or changed

- `.gitignore` — excludes environments, databases, caches, local `.env`, and `agm.keys.json`.
- `README.md` — Phase 3 install, key setup, REST and MCP use, guard limitations and test commands.
- `PHASE3_REPORT.md` — this test and scope report.
- `context.md` — current project state and next steps.
- `pyproject.toml` — version `0.3.0`; adds FastAPI, Uvicorn, official FastMCP-compatible `mcp>=1.26,<2`, and `httpx` for API tests.
- `scripts/pack.py` — creates a workspace archive and a root-relative overlay, excluding `.git`, `.venv`, caches, database files, local keys and environment secrets.
- `src/agm/__init__.py` — Phase 3 package metadata and version.
- `src/agm/api.py` — FastAPI factory, API-key security scheme, scope checks, OpenAPI and the nine REST parity routes; unimplemented Phase 4 routes return HTTP 501.
- `src/agm/cli.py` — `serve-api` and `serve-mcp`, with loopback bind enforcement and API key-file validation.
- `src/agm/config.py` — local API-key registry, timing-safe comparison, scoped identity and environment identity for MCP.
- `src/agm/guard.py` — credential-pattern redaction before event append/embed and instruction-like content screening.
- `src/agm/mcp_server.py` — nine FastMCP tools; uses environment identity and scopes for local MCP.
- `src/agm/store.py` — `write_quarantined`, quarantine event replay, and Phase 3 event status handling.
- `tests/test_guard.py` — secret redaction, instruction screening, normal-content handling, quarantine replay and default retrieval filtering.
- `tests/test_e2e_rest.py` — API authentication, REST write/retrieve, secret-safe storage and embedding, quarantine filtering, scopes and Phase 4 stub response.
- `tests/test_mcp_stdio.py` — launches a stdio MCP server as a subprocess, checks all nine tools, then writes and retrieves a fact.
- `examples/agm.keys.example.json` — placeholder-only API key configuration example.
- `examples/python_client.py` — authenticated HTTP write/retrieve round trip.
- `examples/curl.md` — REST examples, key setup and local-only warning.
- `examples/claude_code_mcp.md` — local stdio client configuration.
- `examples/chatgpt_actions.md` — OpenAPI and deployment notes.
- `docs/decisions.md` — D-014 guard/loopback policy and D-015 MCP SDK compatibility pin.
- `docs/debug.md` — Phase 3 test, fix and environment record.
- `docs/phases.md` — Phase 3 implementation status and remaining verification criteria.
- `docs/readme.md` — current capabilities and limits.
- `docs/status.md` — Phase 3 status, test outcome and next steps.

Phase 1 and Phase 2 implementation files and regression tests are retained in the overlay.

## Test coverage

### Existing Phase 1 and Phase 2 regression suite

The existing tests verify event-first writes, idempotency, correction/supersession, hard deletion and scrubbing, deterministic replay, alias identity, flat-versus-graph behavior, bounded expansion, temporal filtering, stale-base contested writes, trust-gap conflicts and provisional confidence/ranking calculations.

### Phase 3 tests

- `test_labelled_api_key_is_redacted_before_storage`: labeled secret values are replaced before storage.
- `test_bearer_token_is_redacted_from_other_item_fields`: token values in non-text fields are also sanitized.
- `test_instruction_like_text_is_flagged_for_quarantine`: prompt-injection-like phrases get a quarantine reason.
- `test_normal_instructional_content_is_not_quarantined`: ordinary procedural text remains eligible for writes.
- `test_quarantined_event_replays_but_default_retrieval_hides_it`: replay preserves quarantine status, while default retrieval excludes the item.
- `test_fake_api_key_is_rejected_with_401`: incorrect API keys receive HTTP 401.
- `test_rest_write_and_retrieve_round_trip`: an authenticated REST write can be retrieved through the REST endpoint, with the required untrusted-data notice.
- `test_secret_is_redacted_before_event_and_embedding`: the supplied token is absent from the event payload and embedder input.
- `test_instruction_like_write_is_quarantined_and_not_retrieved`: injection-like text is stored as quarantined and excluded from retrieve and history.
- `test_read_scope_cannot_write`: a read-only identity receives HTTP 403 on a write.
- `test_handoff_endpoint_is_auth_gated_but_still_phase4_stub`: the route is authenticated and transparently reports HTTP 501 while Phase 4 logic is absent.
- `test_stdio_lists_tools_and_roundtrips_write_retrieve`: with the official MCP SDK installed, the test checks all nine tool names and performs a write/retrieve round trip over stdio. **Skipped in this builder environment.**

## Commands executed

Runtime: Python 3.13.5. This differs from the user's Windows Python 3.14.7 environment.

- `PYTHONPATH=src python -m pytest -q`
  ```text
  42 passed, 1 skipped in 0.89s
  ```
  The skipped test is the MCP stdio integration test; `mcp` is not installed in this environment.
- `PYTHONPATH=src python -m compileall -q src tests`
  ```text
  Exit code 0; no output.
  ```
- `PYTHONPATH=src python -m agm demo`
  ```text
  Current memories:
    agm.phase = Phase 3 [n_<generated-id>]
  Including superseded memories:
    Phase 3 [n_<generated-id>]
    draft [n_<generated-id>]
  Delete old draft: True; replacement: n_<generated-id>
  ```
  IDs are generated at runtime and differ between runs.
- `PYTHONPATH=src python -m agm rebuild --db ./phase3-smoke.db`
  ```text
  Rebuilt views: 0 nodes
  ```
  This created/rebuilt a separate empty smoke-test database; the demo uses a temporary database.
- `python scripts/pack.py`
  ```text
  Created dist/agm-phase3.zip (73328 bytes)
  Created dist/agm-phase3-overlay.zip (73008 bytes)
  ```
  Archive inspection found 40 files in each ZIP. Both passed checks for excluding `.git`, databases, bytecode, environments, caches, `.env`, and `agm.keys.json`. The overlay contains the required REST/MCP source, interface tests, sample key file and report.
- `python -m pip install -e ".[dev]"`: **NOT RUN** in the builder workspace because this environment could not access the package index.
- An attempted pip resolution for `mcp>=2,<3` failed with DNS/network errors. The project itself pins `mcp>=1.26,<2` to preserve the frozen FastMCP adapter contract. Its install and stdio tool round trip must be verified in the Windows environment.
- User's Windows/Python 3.14.7 Phase 3 run: **NOT RUN yet**.

## Contract concerns and limitations

1. Frozen `Node` does not expose a `status` field and frozen `RetrieveResult` has no general warnings field. Contracts were not changed. The adapters query stored status to hide quarantined items on retrieval/history surfaces.
2. The nine MCP tool names are registered. Handoff and writer-revocation handlers remain Phase 4 stubs and return/raise the corresponding not-implemented response.
3. Guard patterns are intentionally narrow and are not a complete secret scanner or prompt-injection detector. A value that does not match a configured pattern may pass through; this is not production security certification.
4. The REST and streamable HTTP CLI binds are restricted to loopback. MCP streamable HTTP uses the single environment-configured identity and is not a multi-tenant remote server.
5. The API key configuration is loaded at application creation. Key rotation requires a service restart.
6. The frozen retrieve contract has no `include_quarantined` option; there is no admin retrieval route for quarantined content in this phase.
7. API/MCP auth and guard logic apply at those adapter boundaries. A caller using `MemoryStore.write()` directly bypasses those adapter guardrails.
8. Confidence and ranking weights are still uncalibrated placeholders. Phase 5 evaluation has not been implemented.

## Assumptions

- Public model fields and `MemoryStore` signatures remain frozen.
- API keys map to `tenant_id`, `writer_id`, `trust_tier`, optional project/agent and scopes. Supported scopes are `memory:read`, `memory:write`, `memory:delete`, `admin`, and `*`.
- MCP stdio identity comes from `AGM_TENANT`, `AGM_WRITER`, `AGM_TIER`, optionally `AGM_PROJECT`, `AGM_AGENT`, `AGM_SCOPES`, and `AGM_DB_PATH`.
- Recognized secrets are replaced with `[REDACTED]` before the sanitized `WriteItem` reaches the store.
- Pattern-matched instruction-like input is stored as a quarantined node so the event log can replay it, but ordinary retrieval/history do not expose it.
- `mcp>=1.26,<2` is chosen to maintain the Phase 3 brief's `FastMCP` API; see the official [MCP Python SDK v1 documentation](https://py.sdk.modelcontextprotocol.io/v1/).

## Not finished

- Installation and execution of the MCP stdio client test in the user's Windows environment.
- Owner's Windows Phase 3 test run and archive-content check.
- Supervisor review and approval. Do not expose either service beyond loopback until these are complete.
- Phase 4 trust probation, writer revocation/rollback and handoff logic; Phase 5 evaluation and lifecycle management.
