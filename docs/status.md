# Status — 2026-11-02 (v0.7.0)

**Current:** v0.6.0 cleanup merged (PR #61, CI green on all six jobs). R1 client/CLI plus follow-up fixes (hashed keys, hot reload, delete 404, body limit, read-only active-memory routes) on branch `feat/r1-client`; full suite result is recorded in the PR; real CLI end-to-end run (bootstrap, connect, serve, write, retrieve, quarantine) verified. Windows not yet run for R1.

Before R1: cleanup and MCP removal. Full suite: 264 passed (Python 3.12, Linux sandbox). Repo hygiene and wheel inspection pass. `agm demo` passes. REST smoke client passes (inside the suite).

**Not verified:** Windows and Python 3.11/3.13 (CI matrix will cover it once pushed); everything under external gates.

**Open external gates:** held-out real-history evaluation NOT RUN; independent security/privacy review NOT PERFORMED; real third-party-host integration NOT VERIFIED; independent acceptance-matrix sign-off OPEN. M2 NOT ACCEPTED. Not production-ready.

**R2 so far:** a post-hoc iterative flat baseline erases graph's only synthetic win (multi_hop); graph then differs from flat mainly in retrieve calls (1 vs 3) and is slower per call. See `docs/benchmarks/r2_post_hoc_iterative_baseline.md`. The graph hypothesis is therefore still unproven.

**R2 v3 (synthetic, pre-registered rule):** graph NOT JUSTIFIED under both hash and spaCy embeddings (best other: iterative flat). It wins only multi-hop and exposed four core issues (contested handling differs between flat and graph; entity hint blocks expansion; abstention rarely fires; sibling entities leak). See `docs/benchmarks/r2_labelled_v3.md` and roadmap R2.6. Real-data check: `docs/acceptance/real_history_local_runbook.md`.

**R2.6a done (D-046):** flat and graph now treat contested candidates identically (withheld by default, flag on the current fact, `include_contested` opt-in).

**Next:** R2 (real evidence) and R3 (security) from `ROADMAP.md`.

**History:** earlier phase reports, audit logs, benchmark logs and the Phase-8 harness are in git tag `archive/pre-cleanup-main`.
