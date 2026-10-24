# AGM real-history acceptance protocol

## Why this is separate from unit tests

The `test_m0_history_acceptance.py` tests use synthetic data to verify persistence across store instances, tenant isolation, correction history, and deletion after replay. They do **not** prove quality on real user histories. Production readiness requires an evaluation set collected with explicit authorization and a documented privacy process.

## Dataset requirements

- Use only histories whose owners have explicitly consented to this evaluation and the stated retention period.
- Prefer a de-identified dataset. Replace names, email addresses, phone numbers, addresses, account IDs, credentials, and unique identifiers before adding data to the test corpus.
- Never put production databases, raw conversation exports, API keys, or unredacted personal data in Git, CI artifacts, issue trackers, or this ZIP.
- Keep any mapping from pseudonyms to identities outside the repository with restricted access. Document deletion and expiry.
- Use a frozen evaluation split that is separate from histories used to tune retrieval.
- Report dataset size and composition without publishing raw examples that could re-identify a participant.

## Required evaluation dimensions

1. **Cross-session recall:** write in session A, close the store/process, reopen in session B, query the relevant fact, and score whether the correct fact is retrieved.
2. **Correction and temporal accuracy:** ensure a corrected fact is current, old values remain available only for history/as-of queries, and stale values are not returned as current.
3. **Personalization relevance:** measure whether retrieved preferences/goals are relevant to the query and whether irrelevant personal details are suppressed.
4. **Tenant isolation:** no record from another tenant may be returned, even for highly distinctive query terms.
5. **Deletion:** after deletion, restart and rebuild views; verify the fact cannot be retrieved and is absent from active derived stores and event payloads according to the documented scrub contract.
6. **Abstention and uncertainty:** unsupported questions should abstain rather than fabricate or overstate confidence.
7. **Trust and corroboration:** low-trust, uncorroborated memories must respect high-stakes filters; revoking a writer removes that writer's corroboration evidence.
8. **Injection resistance:** retrieved memory content is data, not instructions; instruction-like content must not override the system/developer policy.
9. **Longitudinal drift:** repeated writes, corrections, and retrieval over time must not silently resurrect deleted or superseded values.
10. **Operational reliability:** reopen after process termination, repeated requests, duplicate idempotency keys, and injected failures.

## Scoring and release thresholds

Pre-register thresholds before inspecting the held-out results. At minimum report:

- exact fact recall and top-k recall;
- current-versus-stale answer accuracy;
- unsupported-query abstention precision/recall;
- tenant-isolation violations (release-blocking; expected 0);
- post-deletion recall violations (release-blocking; expected 0 under the stated local threat model);
- high-stakes uncorroborated-memory leakage (release-blocking; expected 0);
- false personalization rate and irrelevant-memory exposure rate;
- latency p50/p95 and error rate by history size;
- results with confidence intervals and breakdowns by history size, language, and query type where sample sizes permit.

Do not invent a threshold after seeing results. Store the evaluation protocol, dataset version/hash, code commit SHA, environment, aggregate metrics, and reviewer sign-off. Do not store raw personal histories in the report.

## Current status

- Synthetic persistence/tenant/correction/deletion acceptance tests: provided in this overlay; run them in the full AGM checkout.
- Real user-history evaluation: **not run**. No consented, de-identified dataset was supplied in this task, so no real-history performance claim is supported.
- Production readiness: **not established** until the held-out evaluation and security/privacy review pass.
