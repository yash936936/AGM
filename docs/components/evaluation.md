# Evaluation, scripts, tests and examples

**Rule:** evaluation rules are written into `decisions.md` before results exist, tuning and held-out sets are separate, and every report includes cases where the simple baseline wins (D-007). Synthetic numbers are smoke tests.

**`eval/`**
- `labelled_v3.py`: the pre-registered v3 labelled benchmark (reports in `docs/benchmarks/`).
- `relation_heldout.py`: frozen held-out paraphrases for relation-following (D-048).
- `benchmark_runner.py`, `synthetic_v2.py`, `stale_facts.py`: earlier synthetic benchmarks.
- `keyword_baseline.py`, `iterative_baseline.py`: baselines. `spacy_embedder.py`: real word vectors, eval only.
- `repeated_retrieval_benchmark.py`, `rest_concurrent_benchmark.py`: latency and load (RSS sampled off the event loop since DBG-003).
- `active_memory_simulation.py`: active-memory turn simulation.

**`scripts/`**: `check_repo_hygiene.py` (secret and database artefact scan), `check_package.py` (wheel inspection), `build_real_history_cases.py` and `evaluate_real_history.py` (local real-data evaluation; raw histories never leave your machine; runbook in `docs/acceptance/real_history_local_runbook.md`).

**`tests/`**: pytest suite, one file per area (names in the other guides). CI runs it on Ubuntu and Windows, Python 3.11–3.13, plus hygiene, `git diff --check`, the REST smoke client and the package check.

**`examples/`**: clients and sample data, including `rest_smoke_client.py` (also run in CI), `chatgpt_actions.md`, `curl.md`.

**Easy to break:** committing real case data (`eval/real/` is gitignored), tuning to the held-out set, reporting only the cases graph wins.

**Open work:** R2.1 to R2.5, R2.7 (gate G1).

---
**Next:** Return to [`context.md`](../../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
