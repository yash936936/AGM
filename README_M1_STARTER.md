# AGM M1 starter overlay

This overlay starts M1 with a repeatable real-history evaluation harness and the M1 lifecycle plan. It does not invent evaluation results or contain real personal data.

## Apply

Extract into the root of your existing AGM checkout, merging the `scripts/`, `tests/`, `docs/`, and `examples/` directories.

## Run the synthetic smoke benchmark

```bash
python scripts/evaluate_real_history.py examples/real_history_eval.synthetic.jsonl
```

The sample is synthetic and only checks that the harness runs. It is not evidence of real-history quality.

## Run the test suite

```bash
python -m pytest -q
```

## Evaluate a real-history benchmark

Prepare a JSONL file outside Git using explicitly consented, de-identified histories. Use opaque case IDs; do not include names, contact details, account IDs, credentials, or raw transcript excerpts. See `docs/REAL_HISTORY_ACCEPTANCE.md` and `docs/M1_KICKOFF.md`.

```bash
python scripts/evaluate_real_history.py /secure/path/heldout.jsonl --output /secure/path/aggregate-report.json
```

The evaluator prints aggregate metrics only and uses a temporary SQLite database per case. It does not output query text or retrieved values. Keep the dataset, report, and any identity mapping outside the repository unless the report has been reviewed and cleared for publication.

## Important

The evaluation is not “fixed” by inventing a dataset. Until an eligible dataset is supplied and the benchmark is run, real-history acceptance remains pending. The harness provides the missing repeatable measurement path; M1 can proceed without misrepresenting the release status.
