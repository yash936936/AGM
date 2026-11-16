# Interfaces

**Purpose:** the ways callers reach the core. Only `cli.py` prints to stdout; library code logs to stderr.

**REST (`src/agm/api.py`, `create_app`)**: `X-API-Key` auth, OpenAPI at `/docs`. Routes: `/healthz`; `/v1/memory` (write), `/v1/memory/retrieve`, `/v1/memory/{id}/supersede`, `/v1/memory/history`, `DELETE /v1/memory/{id}`; `/v1/active/context`, `/v1/active/review`; `/v1/handoff`, `/v1/handoff/{id}/resume`, `/v1/handoff/{id}/readback`; `/v1/admin/revoke`; `/v1/sessions` (create, list, close); `/v1/connections` (create, list, test, delete). Sessions and connections are backed by `hub_state.py`.

**Keys (`config.py`, `agent_keys.py`, `bootstrap.py`)**: key files store hashes only; `KeyIdentity` carries scopes (`memory:read/write/delete`, `admin`); `ReloadingKeyRegistry` picks up key-file changes on the next request; `ensure_loopback_host` refuses non-loopback binds until gate G2.

**Client and CLI**: `client.py` (`AgmClient`, standard library only, never follows redirects, refuses plain `http://` to non-loopback hosts). `cli.py`: `demo`, `rebuild`, `bootstrap-owner`, `serve-api`, `hash-keys`, `lifecycle`, `doctor`. `cli_client.py`: `mem write|retrieve|history|supersede|delete`, `handoff save|resume|readback`, `active context|review`, `connect`.

**Local hub and diagnostics**: `local_hub.py` (read-only timeline, graph snapshot, privacy-aware Obsidian export); `diagnostics.py` (`doctor`: integrity checks and privacy-aware retrieval tracing).

**Easy to break:** the REST map in `architecture.md` and the OpenAPI schema must agree (R4 adds a CI drift check). A new route needs a cross-tenant test and a library-parity test. Hosts that cannot run a shell use REST directly (`examples/chatgpt_actions.md`, `examples/curl.md`).

**Tests:** `test_e2e_rest.py`, `test_client.py`, `test_cli.py`, `test_smoke_clients.py`, `test_hub_state.py`, `test_local_hub.py`, `test_bootstrap.py`.
**Decisions:** D-042, D-043, D-044, D-045. **Open work:** R3 (rate limits, audit log, isolation matrix), R4 (OpenAPI drift check, host guides).

---
**Next:** Return to [`context.md`](../../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
