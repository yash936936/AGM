# M0/M1 implementation review report — 2026-10-25

## Branch
`feat/m0-m1-completion`

## Changes in this branch
- `src/agm/local_hub.py`: added tenant/project-scoped timeline metadata, deterministic read-only graph snapshots, and guarded Obsidian Markdown export.
- `tests/test_local_hub.py`: added tests for timeline payload minimization and tenant scope, deterministic snapshot scope, secret redaction in export, and the documented snapshot-copy behavior after deletion.

## Review notes
- Timeline output omits raw event payloads and memory text.
- Graph snapshots carry a deterministic SHA-256 snapshot ID and only include edges whose endpoints both exist in the scoped node set.
- Obsidian export filters to the caller's tenant/project, omits quarantined nodes, applies the core secret redactor to exported text/value/attribute fields, uses deterministic filenames, and explicitly documents that exported files are copies rather than live sync.
- This is a partial M1 implementation. Owner bootstrap/login, session lifecycle, connection registry and real connection diagnostics remain unimplemented. The new helpers receive a `Ctx`; they do not substitute for owner authentication or authorization at a service boundary.
- The M0 cutoff-revocation regression must be confirmed against current exact-head CI; this branch does not claim to have fixed it.

## Verification
- Local `pytest`: NOT RUN — this execution environment cannot resolve GitHub to clone the repository.
- CI on this branch: pending after PR creation.
- Windows smoke clients, full evaluation suite, package/archive inspection and real-history benchmark: NOT RUN.

## Release status
M0/M1 are NOT complete or production accepted. This PR is a reviewed implementation increment and must not be merged as proof of full milestone completion.
