# Cloud deployment plan: shared AGM memory across devices

## Goal

Allow trusted applications and cloud-hosted agents to read and write one persistent AGM memory over HTTPS. A remote client must never need access to a developer's local SQLite file or local API key file.

## Current boundary

The checked-in service is a local prototype. The REST CLI rejects non-loopback binds, and streamable HTTP MCP is a single environment-configured identity with no independent remote-client authentication. Do not deploy either endpoint publicly by merely removing the loopback guard.

## Recommended implementation sequence

### 1. Cloud-safe identity and authorization

- Replace the local JSON key registry as the production identity source with hashed, revocable credentials stored in a secret/identity store.
- Issue one credential per user, workspace, or agent. Store tenant, project, writer ID, allowed scopes, expiry, and revocation state server-side.
- Enforce tenant and project isolation on every route and in every query. A client must not be able to supply or override its tenant identity in request bodies.
- Add rotation/revocation, rate limits, request size limits, audit metadata, and safe error responses.
- Never log raw credentials. Store only a cryptographic hash of bearer tokens and show each token only once at creation.

### 2. Durable hosted storage

The current MemoryStore uses SQLite-specific SQL, FTS5, WAL mode, and local file paths. It is not a drop-in PostgreSQL adapter. Do not simply point the current database-path argument at a PostgreSQL URL.

For a limited first deployment, a single application instance with a provider-managed persistent disk can host SQLite, provided the disk is durable, backups are tested, the service runs one writer process, and the provider's disk semantics are understood. This is a controlled MVP, not a horizontally scalable database architecture.

For multi-instance scale and stronger operational isolation, implement and test a PostgreSQL-backed store as a separate migration. Preserve event replay and retrieval parity, and test concurrent writes, idempotency, supersede conflicts, deletion, revocation, and recovery before cutover.

### 3. HTTPS API service

- Keep FastAPI as the API layer and add production configuration that fails closed if TLS termination, allowed origins, credential configuration, or storage settings are missing.
- Deploy behind a managed HTTPS ingress/load balancer. Only trust forwarded headers from the ingress.
- Add readiness checks that validate the database, migrations, and key service, not only that the process is alive.
- Apply request timeouts, body limits, rate limits, structured redacted logs, metrics, and alerting.
- Run database migrations as a controlled release step. Test restore from backups before storing important memories.

### 4. Remote MCP

Expose a separate authenticated Streamable HTTP MCP endpoint only after the same per-client authentication and tenant middleware protects every tool. The current environment-configured MCP identity is appropriate for local stdio, not a public multi-tenant endpoint.

Use per-client identity and scopes for remote MCP. Test unauthorized requests, cross-tenant reads, tool-level scope checks, revoked credentials, and prompt-injection handling. Keep stdio available for local clients.

### 5. Clients and sample memory

- Publish a small Python client and a dependency-free JavaScript client that take a base HTTPS URL and per-agent token from environment variables or a secret manager.
- Seed sample data through an authenticated admin/bootstrap path, never by shipping a database containing real user memory.
- Make tenant/workspace explicit in credential provisioning, not a user-controlled field on every memory request.
- Keep the retrieval notice: memory content is untrusted data, not instructions.

## Acceptance checklist

- Two separately authenticated clients can write and read the same workspace's sample memory.
- A client in workspace A cannot read, change, enumerate, or delete workspace B data, even with guessed IDs.
- Revoked and expired credentials fail immediately.
- All public traffic uses HTTPS; no direct public access to SQLite files, admin credentials, debug routes, or the MCP endpoint without auth.
- Restart and redeploy preserve memory.
- Backup restore and event-log replay are tested.
- Concurrent writes preserve idempotency and conflict semantics.
- REST and MCP return the same tenant-scoped data and enforce equivalent scopes.
- CI runs unit, integration, auth-isolation, migration, and restore tests.
- Synthetic retrieval results remain labelled as smoke tests; they are not presented as evidence of calibrated ranking or production reliability.

## Decision

Implement cloud identity and tenancy before enabling remote binds. Keep the current loopback restriction until every acceptance item required for the selected deployment is tested. A working HTTPS URL alone is not proof of a safe shared-memory service.
