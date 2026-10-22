# AGM Phase 5 implementation report

Date: 2026-10-23

## 1. Files created or changed

- `eval/stale_facts.py` — deterministic offline scenarios comparing flat and graph retrieval.
- `src/agm/trust.py` — lazy decay weight and read-only lifecycle candidate selection.
- `src/agm/retrieve.py` — graph ranking uses lazy decay calculated from idle time, retrieval usage, citations and corroboration.
- `src/agm/cli.py` — Phase 5 demo now labels the stored example correctly, and includes handoff/readback plus `agm lifecycle --dry-run`.
- `src/agm/__init__.py` and `pyproject.toml` — Phase 5/version metadata (`0.5.0`).
- `tests/test_lifecycle.py` — decay and no-mutation lifecycle checks.
- `tests/test_eval.py` — evaluation output and D-007 caveat smoke test.
- `tests/test_cli.py` — prevents the demo from displaying the stale Phase 3 label and checks successful handoff readback.
- `README.md`, `docs/readme.md`, `context.md`, `docs/phases.md`, `docs/status.md`, `docs/debug.md`, `docs/decisions.md` — implementation state and decision log.
- `scripts/pack.py` — includes Phase 5 evaluation/tests/report in workspace and overlay packages.

## 2. Test coverage

- `test_lazy_decay_rewards_recent_use_and_pinned_memories`: older unused memories have lower decay; recent usage, citations and corroboration raise it; pinned memories remain at 1.0.
- `test_lifecycle_candidates_skip_pinned_and_recent_memories`: only qualifying active, unpinned items appear as archive candidates.
- `test_lifecycle_cli_dry_run_does_not_mutate_events_or_views`: snapshots events and nodes before and after the CLI, and asserts they are identical.
- `test_lifecycle_threshold_must_be_valid`: invalid thresholds raise `ValueError`.
- `test_synthetic_eval_reports_flat_graph_metrics_and_d007_caveat`: executes the evaluation command and checks both modes, core metrics and D-007 wording.
- `test_demo_reports_current_phase_and_completes_handoff`: verifies that the demo says Phase 5 rather than Phase 3 and that handoff readback succeeds.
- Existing Phase 1–4 tests continue to run in the same suite.

## 3. Commands run

### User's Windows validation before the final demo-label polish

The user reported the following actual results on Python 3.14.7, AGM 0.5.0:

- `python -m pip install -e ".[dev]"` — successful.
- `python -m pytest -q` — `61 passed` in 20.24s, with one Starlette/httpx deprecation warning.
- `python eval/stale_facts.py` — successful; see evaluation results below.
- `python -m agm demo` — successful handoff readback, but output exposed a stale Phase 3 label.
- `python -m agm lifecycle --db ./agm.db --dry-run` — zero candidates, no mutations.
- `python -m agm rebuild --db ./demo.db` — zero nodes in a separate empty database, as expected.
- `python scripts/pack.py` — created Phase 5 workspace and overlay ZIPs.

The Phase 5 label was then corrected and a regression test was added. After that correction, the following commands were run in the builder environment from the repo root:

### `PYTHONPATH=src python -m pytest -q`

```text
61 passed, 1 skipped in 2.71s
```

The skipped test is `tests/test_mcp_stdio.py`; the official MCP SDK is unavailable in this builder runtime. The user's prior Windows environment has the MCP SDK installed, but the final label-polish patch should be rerun on Windows. Expected count with the new demo regression test is 62 passed if the MCP test runs.

### `PYTHONPATH=src python -m compileall -q src tests eval`

```text
Exit code 0
```

### `PYTHONPATH=src python -m agm demo`

Expected behavior after the fix: the stored phase is `Phase 5`, the old `Phase 3` label does not appear, and the handoff readback passes. The latest final console output should be captured after packaging if a verbatim record is needed.

### `PYTHONPATH=src python eval/stale_facts.py`

User's Windows output:

```text
AGM synthetic retrieval smoke evaluation
Scenarios: 4; top-k: 5; embedder: hash-256-v1
Metrics: accuracy = expected answer present in returned items; stale error = old value returned for corrected-fact case; abstention = abstained scenarios / all scenarios.

mode        accuracy   stale-error   abstention   expanded
----------------------------------------------------------
flat         100.0%         0.0%        0.0%          0
graph        100.0%         0.0%       25.0%          3

Caveat (D-007): this synthetic smoke test is not evidence for or against hypotheses H1-H7.
Scores are affected by hand-authored cases and the weak hashing embedder; do not treat them as benchmark results.
```

### Lifecycle and rebuild

```text
Lifecycle dry run: 0 candidate(s); threshold=0.30
No events or memory views were changed.
Rebuilt views: 0 nodes
```

The rebuild targeted a separate empty `demo.db`, so zero nodes is expected and is not a failed replay test.

### Packaging

`python scripts/pack.py` created `dist/agm-phase5.zip` and `dist/agm-phase5-overlay.zip`. Inspect the refreshed archive before distributing it.

## 4. Contract concerns

- No frozen public Pydantic contract or SQLite table schema was changed in Phase 5.
- `decay_weight` is computed lazily for graph ranking and lifecycle reports; persisted `nodes.decay_weight` remains a legacy/default column and is not rewritten.
- `agm lifecycle` requires `--dry-run`. Actual archival/mutation is intentionally not implemented.
- The D-019 decay formula and 0.30 candidate threshold are provisional, not calibrated.

## 5. Assumptions

- Idle time starts at `last_used` where present, otherwise `valid_from`.
- An incoming `derived_from` edge counts as a citation. Independent corroborations use the existing Phase 4 trust helper.
- Pinned items get a decay weight of 1.0 and do not appear as lifecycle candidates.
- The evaluation uses four small, hand-authored scenarios and the default `hash-256-v1` embedder.

## 6. Remaining checks and limitations

- The user's reported Windows run passed 61 tests before the final demo-label correction. The corrected workspace passes 61 tests with the MCP stdio test skipped in the builder environment; rerun on Windows to verify the added regression test alongside MCP.
- No memory is actually archived; lifecycle is reporting-only, as required by this phase.
- Evaluation is only a smoke test and does not support or refute H1–H7 (D-007). No labelled dataset, preregistration, confidence intervals, or statistical testing is included.
- Confidence, rank and decay coefficients remain provisional. Keep services on loopback pending separate security review.
