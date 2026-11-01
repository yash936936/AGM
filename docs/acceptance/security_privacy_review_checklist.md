# Independent security and privacy review checklist

Status: **Review NOT performed.** This is a reviewer worksheet, not a security certification. A reviewer independent of implementation and release decisions must complete it against a pinned commit.

## Review record

- Reviewed AGM commit SHA:
- Reviewer name / organization:
- Independence and relevant experience:
- Review date and scope:
- Environment / configuration:
- Findings report location:
- Overall disposition: NOT STARTED / IN PROGRESS / PASS / FAIL / CONDITIONAL

Do not publish secrets, exploit payloads containing real user data, or sensitive logs in this repository. Keep detailed findings in an access-controlled location and link only an approved sanitized summary.

## Threat model and deployment boundary

- [ ] Identify assets, trust boundaries, data flows, actors, and abuse cases.
- [ ] Confirm services remain loopback-only by default and remote exposure is disabled pending review.
- [ ] Verify authentication bootstrap, key storage/rotation, authorization defaults, and fail-closed behavior.
- [ ] Test tenant, project, writer, session, and connection isolation at API and storage layers.
- [ ] Review local filesystem permissions, SQLite/WAL/journal files, backups, exports, diagnostics, and temporary files.
- [ ] Review dependency and supply-chain risks, packaging contents, and supported runtime assumptions.

## Memory lifecycle and privacy

- [ ] Verify consent/provenance requirements and source attribution.
- [ ] Test correction, hard deletion, revocation, expiry, pinning, and replay/rebuild semantics.
- [ ] Confirm deleted/revoked data does not resurface through retrieval, graph edges/snapshots, exports, logs, caches, or reopen/rebuild.
- [ ] Verify audit records retain only the minimum metadata needed and do not retain deleted content unintentionally.
- [ ] Review retention defaults, explicit pinned-data handling, backup retention, and deletion guarantees.
- [ ] Verify quarantine and untrusted retrieved text cannot become instructions or forge record boundaries.
- [ ] Review redaction behavior, including false negatives/positives and unsupported sensitive-data classes.
- [ ] Review data minimization, export controls, user visibility, and incident response.

## API and operational checks

- [ ] Exercise invalid, oversized, malformed, and adversarial inputs.
- [ ] Verify authorization for every read/write/admin endpoint, including error and diagnostic paths.
- [ ] Check secret leakage in exceptions, logs, metrics, traces, smoke output, and package artifacts.
- [ ] Check resource exhaustion, concurrency, transaction rollback, and failure recovery.
- [ ] Confirm REST adapter behavior against the documented contract.
- [ ] Confirm default bind address and demonstrate that an accidental remote bind is blocked or clearly guarded.
- [ ] Review install/build provenance, reproducibility where supported, and dependency vulnerability results.

## Finding severity and closure

For every finding, record a unique ID, affected component/commit, reproducible steps in a sanitized environment, impact, severity, remediation owner, target date, and retest evidence. Critical/high findings must be resolved and independently retested before release. Document any accepted residual risk with an accountable owner and explicit approval.

The reviewer should inspect implementation and test evidence directly. Passing repository CI is useful input, not a substitute for this review.

## Sign-off

- [ ] Findings have been triaged and assigned.
- [ ] Critical/high findings are closed and retested, or release is blocked.
- [ ] Residual risks and accepted limitations are explicit.
- [ ] Reviewer provides written disposition and date.

**Gate remains OPEN until a qualified independent reviewer completes and signs off this checklist.**
