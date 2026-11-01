# Status — 2026-11-02 (v0.7.0)

**Current:** v0.6.0 cleanup merged (PR #61, CI green on all six jobs). R1 client/CLI work on branch `feat/r1-client`: 274 tests pass in the Linux sandbox; real CLI end-to-end run (bootstrap, connect, serve, write, retrieve, quarantine) verified. Windows not yet run for R1.

Before R1: cleanup and MCP removal. Full suite: 264 passed (Python 3.12, Linux sandbox). Repo hygiene and wheel inspection pass. `agm demo` passes. REST smoke client passes (inside the suite).

**Not verified:** Windows and Python 3.11/3.13 (CI matrix will cover it once pushed); everything under external gates.

**Open external gates:** held-out real-history evaluation NOT RUN; independent security/privacy review NOT PERFORMED; real third-party-host integration NOT VERIFIED; independent acceptance-matrix sign-off OPEN. M2 NOT ACCEPTED. Not production-ready.

**Next:** R1.4 (active memory exposure decision), then R2 (real evidence) and R3 (security) from `ROADMAP.md`.

**History:** earlier phase reports, audit logs, benchmark logs and the Phase-8 harness are in git tag `archive/pre-cleanup-main`.
