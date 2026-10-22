# ChatGPT Actions setup notes

The local API publishes OpenAPI at `http://127.0.0.1:8765/openapi.json` while running. A hosted Action cannot reach a developer's localhost address; a remote deployment requires HTTPS, secret management, and a security review before exposure.

The current prototype accepts `X-API-Key` or `Authorization: Bearer <key>`. The included OpenAPI describes routes but does not embed actual keys. Never put a real API key in this file or commit it.

Recommended read/write endpoints for a first Action:

- `POST /v1/memory`: structured memory write; guard redacts secrets and quarantines instruction-like text.
- `POST /v1/memory/retrieve`: retrieve relevant memory and return the untrusted-data notice.
- `GET /v1/memory/history`: inspect previous values for an entity.

The handoff and revoke endpoints are declared for interface parity but remain unimplemented until Phase 4.
