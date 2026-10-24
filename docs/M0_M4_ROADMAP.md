# AGM roadmap: M0–M4

**Target branch:** `work/m0-m1-completion`  
**Document status:** planning baseline; statuses below reflect evidence available on 2026-10-25, not a release certification.

This roadmap separates implementation scope from release evidence. A milestone is not complete merely because documentation or a synthetic test exists. Mark a requirement **PASS** only when evidence is tied to the exact commit being reviewed. Mark it **BLOCKED** when required external data, infrastructure, or independent review is unavailable.

## Milestone overview

| Milestone | Goal | Required deliverables | Closure gate | Current status |
|---|---|---|---|---|
| M0 — Storage correctness | Trustworthy local persistence and privacy-aware lifecycle | Transaction/concurrency behavior, temporal ordering, validation, idempotency, deletion and retention semantics, secret handling, repository hygiene, CI | Tests for failure/rollback/replay and tenant scope; exact-head CI; package inspection; documented deletion/retention limits | **IN PROGRESS** — local branch reported 182 tests passing; retention code/tests exist, but exact-head CI and release audit must be confirmed |
| M1 — Local-first hub | Usable local control plane for one owner and connected agents | Owner login, agent connections, sessions, connection test, timeline, graph snapshots, Obsidian export | End-to-end tests for auth/session isolation, connection lifecycle, timeline/snapshot correctness, export privacy and round-trip behavior | **PARTIAL / VERIFY** — memory lifecycle and adapters exist; do not infer all hub UI/owner-login requirements are delivered |
| M2 — Live multi-agent memory | Synchronize useful memory between live agents | Live graph patches, decision logs, context packs, handoffs, backpressure, independent retrieval evaluation | Multi-agent integration tests, reconnect/replay, ordering, backpressure/load tests and preregistered independent retrieval evaluation | **NOT ACCEPTED** — Phase 8 synthetic retrieval results are diagnostic only |
| M3 — Teams | Safe collaboration across workspaces | Workspaces, roles, memberships, authorization enforcement | Positive and negative authorization matrix across API/MCP/library, cross-workspace isolation, membership/role-change tests | **NOT ACCEPTED** — team authorization acceptance evidence not established |
| M4 — Hosted deployment | Operate AGM remotely and recover safely | PostgreSQL, pgvector, remote authentication, deployment, backups, metrics, restore drills | Production-like deployment; auth and tenant isolation; migration tests; measured backup restore and recovery objectives; monitoring/alert tests | **NOT ACCEPTED** — local SQLite prototype evidence does not establish hosted readiness |

## M0 — Storage correctness

Required controls:
- Mutations are atomic: event and materialized-view changes commit together or roll back.
- Concurrent writers and idempotency keys have deterministic, tested behavior.
- Temporal order and correction semantics are explicit; historical reads respect validity intervals.
- All public inputs are validated, with safe error responses and bounded resource use.
- Delete, expiry and revocation have distinct documented semantics. Replay/rebuild must not resurrect deleted or expired content.
- Secret detection/redaction tests use synthetic fixtures; real credentials must never be committed.
- Package contents are checked for databases, WAL/SHM files, credentials, `.env`, virtual environments, caches and private histories.
- CI must pass on the exact proposed merge commit, not merely an earlier baseline.

**Expiry policy baseline to review:** expire unpinned items in the authenticated tenant and project whose source-event creation timestamp is at or before an explicit UTC cutoff. Pinned items are retained by default; including them must be an explicit boolean choice. Expiry should scrub eligible aged content-bearing source payloads while retaining compact audit events where required. Verify atomicity, idempotency, replay, tenant/project isolation, and backup/WAL caveats before approving this policy. This baseline is a proposal to validate, not a claim of regulatory compliance.

## M1 — Local-first hub

Scope:
1. Owner authentication and local identity setup.
2. Agent connection registry with least-privilege scopes and secret-safe storage.
3. Session lifecycle and connection test/diagnostics.
4. Timeline view of writes, corrections, deletions, revocations and handoffs without exposing secret payloads.
5. Read-only graph snapshots with stable IDs and explicit tenant/project filters.
6. Obsidian export with safe filenames, frontmatter escaping, provenance and a documented delete/export limitation.

Acceptance:
- unauthenticated and wrong-scope requests fail closed;
- sessions cannot cross tenant/project boundaries;
- connection test reports actionable status without leaking tokens;
- timeline ordering agrees with the event log;
- graph snapshots can be rebuilt and are marked as snapshots rather than authoritative state;
- export is deterministic, secret-scrubbed, and tests confirm the expected behavior when a source memory is deleted after export.

Do not describe a component as implemented until its source path and tests are identified in the status matrix.

## M2 — Live multi-agent memory

Scope:
- Incremental graph patches with version/cursor and replay recovery.
- Append-only decision logs with provenance and redaction.
- Context packs with token/size budgets, trust labels and untrusted-memory warnings.
- Handoff save/resume with conflict and stale-state handling.
- Bounded queues, backpressure, cancellation, retry and reconnect behavior.
- Independent retrieval evaluation with hand-labelled and adversarial cases, not only generated templates.

Acceptance:
- two or more concurrent writers are tested;
- duplicate, delayed and out-of-order updates are handled deterministically;
- reconnect and full replay converge to the same graph snapshot;
- load tests show bounded memory/queue growth and predictable overload responses;
- evaluation protocol, thresholds, dataset version/hash and aggregate results are recorded before results are interpreted.

## M3 — Teams

Scope:
- Workspace and membership model.
- Roles and explicit permission matrix.
- Authorization at every adapter and core boundary; never trust a client-supplied tenant ID alone.
- Audited membership/role changes and revocation.

Acceptance:
- tests cover allow and deny cases for every role/action;
- cross-workspace reads, writes, graph expansion, exports and handoffs are blocked;
- removed members and revoked credentials lose access immediately according to the documented session policy;
- tests include IDOR-style identifier substitution and replay attempts.

## M4 — Hosted deployment

Scope:
- PostgreSQL persistence and pgvector adapter with migrations.
- Remote authentication, credential rotation and secret management.
- Deployment configuration, health/readiness checks and safe shutdown.
- Backup policy, restore drills and retention of backups.
- Metrics/logging/tracing with payload minimization and tenant-safe labels.

Acceptance:
- migration and rollback/forward-recovery tests pass against supported PostgreSQL versions;
- pgvector results are checked against the local baseline on a representative evaluation set;
- tenant isolation and authz tests pass against the hosted adapter;
- backup restore is executed and timed, with recovery point/time objectives documented;
- alerts are tested; logs do not contain memory text, tokens or other sensitive payloads by default;
- deployment, restore and incident-response runbooks are reviewed.

## Cross-cutting release gates

1. **Synthetic tests:** prove expected code paths; never substitute for real-world quality evidence.
2. **Held-out real-history evaluation:** run only on consented, de-identified data with access controls, a frozen protocol and aggregate-only reporting. If no eligible dataset exists, status stays **BLOCKED / NOT RUN**.
3. **Security/privacy review:** threat model, data-flow inventory, authorization matrix, retention/deletion review, backup/export analysis, incident response, findings and reviewer sign-off. Automated tests are evidence, not independent approval.
4. **Exact-head CI and packaging:** test the exact candidate commit; inspect actual archives for private data and unwanted files.
5. **Merge rule:** merge only when all mandatory code gates pass and all external gates are either passed or explicitly accepted as a documented, non-production limitation. Do not label AGM production-ready while mandatory real-history or security review gates are open.

## Status vocabulary

- **PASS:** evidence exists for the exact candidate commit and satisfies the acceptance criterion.
- **IN PROGRESS:** implementation or validation is underway.
- **BLOCKED:** an external prerequisite is missing.
- **NOT ACCEPTED:** acceptance evidence is not established.
- **WAIVED:** only by an explicit, documented decision naming the risk owner and scope; a waiver must not be presented as a pass.

## Next execution order

1. Finish M0 retention/expiry and exact-head regression evidence.
2. Audit and close core store/retrieval correctness gaps.
3. Strengthen Phase 8 temporal/entity tests and adversarial retrieval evaluation.
4. Complete M0 acceptance matrix and M1 evaluator scenario coverage.
5. Verify cross-session and lifecycle integration.
6. Run final local/CI/packaging checks and archive hygiene.
7. Prepare the held-out benchmark and security/privacy review artifacts; record these as blocked until actual data/review is available.
8. Only then evaluate merge readiness; M1–M4 must not be treated as delivered merely because M0 passes.
