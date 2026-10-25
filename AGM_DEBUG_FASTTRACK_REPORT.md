# AGM Debug Fast-Track Report

## Baseline
- Repository: `yash936936/AGM`
- Baseline branch: `main`
- Baseline commit: `fb732d2e49bc99205cd14964a9d0ba01163bfbb0`
- Review branch: `debug/revocation-replay-fasttrack-review`
- Plan commit: `e8356e7bd5fd19472a23fbb850e345b8f1116711`
- Documentation update commit: `bdf6a9be0e8bff69e704f5f6bbf7389c8134a3bc`

## ZIP assessment
The supplied `fasttrack.zip` contains only:
- `fasttrack/prompts/m0_m1_fast_track.md`
- `fasttrack/scripts/verify_all.py`
- `fasttrack/tests/test_m0_open_gaps.py`

It is not a complete code snapshot. The prompt assumes an older or alternate starting state and proposes an M0/M1 feature build. That does not align cleanly with current `context.md`, `docs/status.md`, `docs/M0_M4_ROADMAP.md`, or the active D-028/D-029 retention decisions. The test file is absent from current main, so it was not added wholesale.

## Release-blocking regression
Current main CI run: https://github.com/yash936936/AGM/actions/runs/40189884890

The exact main head failed on Python 3.11, 3.12, and 3.13 with `1 failed, 189 passed, 1 warning` in each job. The common failure is:

`tests/test_privacy_edge_acceptance.py::test_revocation_since_cutoff_preserves_older_memory_after_rebuild_and_reopen`

Observed behavior: a later item is removed at the moment of cutoff-based writer revocation, but reappears after reopening the database and calling `rebuild_views()`. Repository hygiene and `git diff --check` passed in that run. This issue is unresolved.

## Changed files
- `prompts/fasttrack_debug_plan_revised.md`: records the new sequence and gate logic, with revocation replay first, M0 retention audit second, and evidence-led M1 inventory last.
- `docs/debug.md`: prepended a review entry with the ZIP assessment and observed CI evidence.
- `docs/status.md`: updated current status and next action.
- This report: records baseline findings and unverified work.

No runtime source code changed in this review.

## Commands and evidence
- ZIP listing/content inspection: performed in this session.
- Current `context.md`, `AGENTS.md`, `docs/status.md`, `docs/decisions.md`, `docs/debug.md`, `docs/M0_M4_ROADMAP.md`, `docs/M0_ACCEPTANCE_MATRIX.md`, `src/agm/store.py`, and `tests/test_privacy_edge_acceptance.py`: inspected remotely via GitHub.
- GitHub Actions run `40189884890`: inspected, including job logs for Python 3.11, 3.12, and 3.13.
- Local `python -m pytest -q tests/test_privacy_edge_acceptance.py`: NOT RUN.
- Local `python -m pytest -q`: NOT RUN.
- Local compileall, hygiene, and `git diff --check`: NOT RUN. Only the hosted CI hygiene and whitespace steps are known to pass.
- MCP and REST smoke clients: NOT RUN.
- Evaluation and active-memory simulation: NOT RUN.
- Package build and archive inspection: NOT RUN.
- Local Windows verification: NOT RUN.

## Next work
1. Fix and add regression coverage for durable cutoff-based revocation across replay/rebuild/reopen.
2. Run focused acceptance, full tests, hygiene and whitespace checks.
3. Validate `expire_before` against D-028/D-029 including atomic rollback, repeat-run idempotence and replay.
4. Inventory remaining M0 gaps against the acceptance matrix.
5. Inventory the six M1 requirements using actual implementation and test paths. Do not automatically implement the ZIP's full auth/session/connection/UI specification.
6. Obtain exact-head CI on Python 3.11, 3.12, and 3.13; then run owner-side Windows smoke clients, evaluation and packaging checks.

## Contract concerns and deferred work
- Do not change frozen model, REST, MCP or CLI contracts without a new numbered decision.
- Do not add hard dependencies.
- Full M1 owner auth, sessions, connection management, timeline, snapshot, export and UI remain deferred until scoped against current contracts.
- Held-out real-history evaluation is NOT RUN.
- Independent security/privacy review is NOT ESTABLISHED.
- No production-readiness claim is justified.
