# Real-history evaluation: local runbook (your data stays on your machine)

Companion to `real_history_evaluation_protocol.md`. Use it to produce the one thing the roadmap cannot generate for you: evidence on **your** kind of data. Nothing in this runbook requires sending raw data to anyone. Share only the aggregate JSON report, and only if you are comfortable doing so.

**Entry check (from the protocol):** you own or are authorised to use the data, you have de-identified it (no names, contacts, credentials, health or financial details), and you will delete the case file when done. If any of that is uncertain, stop and use synthetic data.

## 1. Write 20–40 cases (30–45 minutes)

Copy `examples/real_history_authoring.template.json` to a private folder **outside the repo** and edit it. Each case is one fact (or a few) your agents would really store, and one question they would really ask later. Aim for a mix:

| Type | What to write | Why |
|---|---|---|
| recall | a fact, then a question phrased the way you would really ask (not copied from the fact) | basic usefulness, paraphrase handling |
| stale | a fact, a correction, and a question about the current value | stale-value suppression |
| deletion | a fact you would want forgotten | must never resurface |
| abstention | a question with no stored answer | agent must not invent one |

Label answers **before** running anything, and do not edit cases after seeing results (a changed case needs a new run). Write at least a third of the questions in wording that differs from the stored text.

## 2. Build, run, compare

```bash
python scripts/build_real_history_cases.py /private/path/cases.json /private/path/cases.jsonl
python scripts/evaluate_real_history.py /private/path/cases.jsonl --output /private/path/agm_report.json
python eval/keyword_baseline.py /private/path/cases.jsonl --output /private/path/keyword_report.json
```
(PowerShell/Git Bash: use real paths such as `D:/private/agm-eval/cases.json`.) The first script validates the cases with the evaluator's own schema checks. Each case runs in a fresh temporary database with a close/reopen and a view rebuild before the query.

## 3. Read the result honestly

Compare `case_pass_rate`, expected-value recall, forbidden-value leaks and abstention accuracy between `agm_report.json` and `keyword_report.json`. Any forbidden-value leak (stale or deleted value returned) is a defect to investigate, not an average to offset. With 20–40 cases the confidence intervals are wide: treat a result as a signal, not a verdict, and say so.

Decision rule to fix **before** you run: AGM is worth keeping as the retrieval layer for your data only if it beats the keyword baseline on pass rate by a margin you choose in advance (say 10 points) with zero leaks. If it does not, that is useful news: the simpler tool is enough for this data.

## 4. What is safe to share

The two aggregate reports contain counts and rates, not memory text. If you want help interpreting them, paste those two JSON files. Do not share `cases.json`, `cases.jsonl`, or any log that contains memory text. Delete the case files when finished.
