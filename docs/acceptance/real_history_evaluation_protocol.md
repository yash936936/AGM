# Held-out, consented real-history evaluation protocol

Status: **Protocol drafted; evaluation NOT RUN.** This document defines the evidence required to close the gate. It does not itself provide user-history data, consent, or evaluation results.

## 1. Entry criteria

Do not ingest any history until the dataset owner has documented:

- explicit, informed consent covering this evaluation and the intended processing;
- lawful authority to use the data, with any required organizational approval;
- a de-identification and minimization plan, including handling of names, contact details, credentials, health/financial details, and other sensitive content;
- who can access the source data, derived fixtures, logs, and reports, and when each will be deleted;
- an approved isolated environment and a documented incident/contact path.

Use synthetic fixtures instead if any entry criterion is missing. Do not copy raw conversations into Git, issues, CI logs, or benchmark reports.

## 2. Freeze the protocol before looking at held-out results

Record the AGM commit SHA, Python/runtime and dependency versions, OS, configuration, retrieval settings, dataset manifest hash, evaluator version, and random seed where applicable. Freeze case inclusion/exclusion, labels, scoring, baselines, and pass/fail thresholds before running the held-out set. Changes after inspection require a new protocol version and a fresh holdout.

Separate data preparation and labelling from implementation tuning. Keep the held-out labels and case IDs inaccessible to the person tuning retrieval until the run is frozen. Record exclusions and reasons without retaining unnecessary raw text.

## 3. Dataset and split

Use only the minimum data needed for the research question. A reviewer independent of implementation should verify consent and split hygiene. Split by person/account and conversation timeline, not randomly by individual turns, to reduce leakage across train/tune and held-out sets. Ensure the same fact or near-duplicate is not represented across splits.

Each evaluation case should contain only the minimum fields required by the existing evaluator, with synthetic opaque case IDs. Expected answers, forbidden/stale answers, and abstention expectations must be labelled before running AGM. Include cases for:

- cross-session recall of a consented fact;
- correction and current-value selection, including stale-value suppression;
- explicit deletion and no resurfacing after reopen/rebuild;
- writer/tenant/project isolation;
- ambiguity and justified abstention;
- adversarial or untrusted text that must not be treated as instructions;
- revocation, retention, and privacy-sensitive data handling where the data and consent permit.

Do not infer or manufacture labels for facts that cannot be judged reliably.

## 4. Baselines and metrics

Run the same held-out cases against AGM and at least a simple keyword baseline. If a flat-memory baseline is available, include it as a paired comparator. Use identical inputs, expected/forbidden labels, and runtime conditions where comparable.

Report, at minimum:

- expected-value recall / case pass rate;
- forbidden-value leakage count and rate;
- stale-value selection rate after correction;
- correct abstention rate;
- cross-scope leakage count;
- deleted/revoked content resurfacing count after rebuild/reopen;
- retrieval and end-to-end latency p50, p95, p99;
- throughput and error rate;
- dataset/case counts, exclusions, and confidence intervals where sample size supports them.

Report aggregate results only. Do not publish raw conversations, memory payloads, identifying case IDs, or excerpts that could re-identify a person. Small subgroup results should be suppressed where disclosure risk exists.

## 5. Acceptance and stop conditions

The release owner and independent evaluator must freeze numeric thresholds before the held-out run. There are no implicit pass thresholds in this protocol. Any forbidden-value disclosure, cross-scope leakage, or deleted/revoked-content resurfacing is a security/privacy failure requiring triage, not an average score to offset.

Stop immediately if consent is uncertain, unexpected sensitive data appears in outputs/logs, data escapes the approved environment, or the split/labels appear contaminated. Preserve only approved diagnostic metadata, restrict access, and follow the documented incident process.

## 6. Required evidence package

Store the restricted raw-data manifest outside the repository. The shareable report should include:

- protocol version and approval record;
- code SHA and environment/configuration manifest;
- de-identified aggregate metrics and uncertainty;
- baseline comparison and failure taxonomy;
- deviations, exclusions, and incidents;
- evaluator identity/independence statement and sign-off;
- final disposition: PASS, FAIL, or INCONCLUSIVE.

A successful synthetic benchmark or passing CI suite is not a substitute for this gate.

## Gate status

- Protocol: drafted in repository.
- Consented held-out dataset: not supplied or verified.
- Frozen thresholds and approvals: pending.
- Held-out run and independent result review: **NOT RUN**.
