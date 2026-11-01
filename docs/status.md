# Status — 2026-11-02 (v0.6.0)

**Current:** cleanup and MCP removal done on branch `cleanup/lean-v0.6`. Full suite: 264 passed (Python 3.12, Linux sandbox). Repo hygiene and wheel inspection pass. `agm demo` passes. REST smoke client passes (inside the suite).

**Not verified:** Windows and Python 3.11/3.13 (CI matrix will cover it once pushed); everything under external gates.

**Open external gates:** held-out real-history evaluation NOT RUN; independent security/privacy review NOT PERFORMED; real third-party-host integration NOT VERIFIED; independent acceptance-matrix sign-off OPEN. M2 NOT ACCEPTED. Not production-ready.

**Next:** R1 (agent-connectable client and CLI) and R2 (real evidence) from `ROADMAP.md`.

**History:** earlier phase reports, audit logs, benchmark logs and the Phase-8 harness are in git tag `archive/pre-cleanup-main`.
