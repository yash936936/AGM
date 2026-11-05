# AGM roadmap: v0.7 → v1.0

Updated 2026-11-04 (after D-046). Supersedes earlier roadmaps (old M0–M4 and phase lists live in git tag `archive/pre-cleanup-main`).

**Effort:** S ≤ 1 day, M 2–4 days, L 1–2 weeks of focused work. **Calendar** (rough, depends on your hours): at ~10 focused hours a week, double the day counts; full-time, they hold. These are estimates, not commitments.

## 1. Where we are

- **Code:** v0.7.0. Event-sourced SQLite store, flat and graph retrieval, trust tiers, contested handling (D-046), handoff, lifecycle (delete/expiry/revocation), guard in core, REST API, stdlib client, CLI (`mem`, `handoff`, `active`, `connect`, `hash-keys`), read-only active-memory routes. 289 tests; CI (Ubuntu + Windows × Python 3.11–3.13) green on the latest `main` run (#642).
- **Decided and done:** MCP removed (D-042); client/CLI (D-043); read-only active routes (D-044); hashed keys, hot reload, 404 on missing delete, body limit (D-045); contested candidates withheld by default (D-046).
- **Evidence so far (synthetic only):** on the pre-registered v3 benchmark graph retrieval is level with agent-style flat retrieval at best (hash embedder, within noise) and behind it with real word vectors; its only clear win is multi-hop. Four core defects were found; one is fixed.
- **Not done:** any evidence on real data; abstention; entity-hint/expansion interaction; near-duplicate entity names; independent security review; remote access; a real third-party host; scalable vector search; a licence; packaging.
- **Known unknown:** one Windows/Python 3.13 CI failure (#641) was never diagnosed; the next run on the same code passed. Treat as a possibly flaky test until proven otherwise (R0.1).

## 2. The question that decides the plan

Nothing in the design has been shown to beat a simple baseline on **your** kind of data. So the plan has two decision gates, and work after each gate depends on its outcome:

- **Gate G1 (graph or not):** after R2.4 (your real-data run) and the R2 core fixes. Graph expansion stays on by default only if it beats the best flat baseline by a margin fixed in advance, with zero forbidden-value leaks. Otherwise it becomes optional (default off) and the product is "event log + trust + lifecycle + handoff + flat retrieval", which is still a coherent tool.
- **Gate G2 (go remote):** after R3.4–R3.5 (threat model and independent review). Until it passes, the server stays loopback-only.

## 3. Milestones

| Version | Meaning | Contains | Rough size |
|---|---|---|---|
| **v0.7.x** (now) | Stable local prototype | R0, R2.6b–d | ~2–3 weeks |
| **v0.8** | Local-complete and evidence-backed | G1 decided, R2.4, R5.1–R5.2 | ~3–4 weeks |
| **v0.9** | Remote beta | R3, R4 (G2 passed) | ~4–5 weeks |
| **v1.0** | Release | R5 remainder, R7, release gates | ~2–3 weeks |

Total to v1.0 about **12–16 weeks at ~10 h/week** (6–8 full-time). The largest uncertainties are external: your real-data cases (R2.4), a security reviewer (R3.5), and what G1 decides.

## R0: Hygiene and project health (do first; ~2–3 days)

| # | Item | Effort | Done when |
|---|---|---|---|
| R0.1 | Windows flaky tests. **Found and fixed one cause:** the REST benchmark sampled memory by spawning PowerShell inside the event loop, freezing the load workers (0 requests in a 0.5 s window) and distorting its own latencies; fixed with a regression test. Not confirmed to be the same failure as CI #641 (its log was never read), so keep watching: if a Windows job goes red again, capture the `FAILED` lines | S | 10 consecutive green Windows runs after this fix |
| R0.2 | **Add a LICENSE.** The public repo has none, so by default nobody may legally use it. Pick one (MIT or Apache-2.0 are the usual choices); your decision | S | `LICENSE` + `license` field in `pyproject.toml` |
| R0.3 | Turn on branch protection for `main` (require CI) once you want it, and add 3.14 to the CI matrix (your machine already runs 3.14) | S | matrix includes 3.14 |
| R0.4 | `CHANGELOG.md` and a release procedure (tag, build, `check_package.py`) | S | v0.7.0 tagged with notes |
| R0.5 | Decide what to do with the old working folder and its two uncommitted test files (`test_retrieve.py`, `test_privacy_edge_acceptance.py`): merge anything still useful, then retire it | S | one working copy only |

## R2: Retrieval correctness and evidence

### R2.6: core defects found by the v3 benchmark (~1.5 weeks)

| # | Item | Effort | Done when |
|---|---|---|---|
| R2.6a | ~~Flat and graph agree on contested candidates~~ DONE (D-046) | | |
| R2.6b | ~~An entity hint scopes the seeds but no longer blocks expansion~~ DONE (D-047) | S | hint + expand reaches linked entities on the multi-hop family; tests |
| R2.6e | **Relation-following depends on query wording.** Graph follows outgoing relation edges only when the query contains words from a fixed list (`dependent`, `dependency`, `dependencies`, `downstream`, `reachable`); "depends on" does not match. Measured with a hint: 2-hop questions 15/15, 1-hop 0/15. Replace the keyword trigger with a wording-independent rule, and validate on a **held-out** set of paraphrases (do not tune to the v3 wording) | M | 1-hop and 2-hop multi-hop both ≥ 0.8 on held-out phrasings, no new leaks |
| R2.6c | Abstention that fires for unknown entities and for known entities lacking the asked attribute. **Riskiest item:** a stricter rule can hurt recall, so measure both on v3 before and after | M | unanswerable correctness ≥ 0.8 on v3 while single-fact recall drops by ≤ 0.02 |
| R2.6d | Disambiguate near-duplicate names (`x` vs `x-staging`) without a hint | M | hard_neg strict pass ≥ 0.8 no-hint |

### R2.1–R2.5: evidence (runs in parallel; ~2–3 weeks, partly your time)

| # | Item | Effort | Done when |
|---|---|---|---|
| R2.1 | Re-run all benchmarks with a real sentence embedder (optional extra, lazy import). Word vectors are weaker than sentence embeddings, so this may change the paraphrase results | M | reports list the embedder per run; graph-vs-baseline verdict recorded for each |
| R2.2 | Real-usage labelled set (20–40 cases), built by **you** locally with `scripts/build_real_history_cases.py` and `docs/acceptance/real_history_local_runbook.md` | M (your time) | cases written and frozen before any run |
| R2.3 | Remaining baselines: BM25-only, vector-only, and "put the whole log in context" for small histories | S | report shows where each baseline beats graph |
| R2.4 | Run the evaluator and keyword baseline on your cases; share only the two aggregate reports | S | decision margin chosen in advance; result recorded |
| R2.5 | End-to-end agent task test: same agent, same tasks, with and without AGM; measure success and token cost | L | measured deltas, small but honest sample |

**G1 decision** (R2.7): record the outcome as a decision entry. If graph is not justified, set `expand` default to off, keep the code, and drop graph-specific work from later phases.

## R3: Security and remote access (~3–4 weeks; needed for ChatGPT and web agents)

| # | Item | Effort | Done when |
|---|---|---|---|
| R3.1 | ~~Hashed keys~~ DONE (D-045). Remaining: key expiry and rotation, a managed credential store instead of a JSON file | M | expired key fails; tests |
| R3.2 | ~~Body size limits~~ DONE (D-045). Remaining: rate limits, safe error bodies, audit log (who read/wrote/deleted what, never memory text), no secrets in logs | M | negative tests; audit trail verified |
| R3.3 | Isolation test matrix: every route × cross-tenant, cross-project, ID guessing, wrong scope | M | matrix runs in CI |
| R3.4 | Threat model and data-flow inventory; run `docs/acceptance/security_privacy_review_checklist.md` | M | written findings with owners |
| R3.5 | **Independent** reviewer sign-off (external) | external | signed checklist, or remote stays off |
| R3.6 | Controlled deploy: single instance behind HTTPS (reverse proxy), persistent disk, single writer, **tested backup and restore**, key rotation drill | M | two clients share one workspace remotely |

**G2 gate:** non-loopback binding is allowed only after R3.4 and R3.5 pass.

## R4: Real-host acceptance (~1 week, after R1 and R3.6)

Run `docs/acceptance/third_party_host_validation.md` against at least two real hosts, for example Claude Code through the CLI client (with the `connect` instruction block in `CLAUDE.md`) and a ChatGPT Action through the deployed instance. CI smoke tests do not count.

Also: a checked-in OpenAPI file with a CI drift check (finishes R1.5), and a short per-host setup guide.

## R5: Scale, quality and operability (~3 weeks; scope set by G1 and real data)

| # | Item | Effort | Done when |
|---|---|---|---|
| R5.1 | **Vector search does a full scan:** each query loads every embedding for the tenant/project into Python. Measure at 10k, 100k and 1M nodes, then fix (cached matrix, sqlite-vec, or an ANN index) | M–L | p95 retrieval < 100 ms at 100k nodes (target to confirm with measurements) |
| R5.2 | Embedder strategy: stored embedder id per vector, re-embed migration when the model changes, optional sentence-transformers extra, documented default | M | switching models does not corrupt or silently mix vectors |
| R5.3 | Schema/event-log versioning and an upgrade path between releases, with replay tests across versions | M | old logs replay on new code in CI |
| R5.4 | Observability: redacted structured logs, basic metrics, `doctor` extended | S | documented runbook |
| R5.5 | Learning/ranking improvements, only where real-data failures justify them; consolidation and decay tuning | L | each change justified by a measured failure |

## R6: Only if demanded

- Optional MCP shim as a **thin client of the REST API** (not a second core adapter), if shell/HTTP integration proves a real adoption blocker (trigger: two or more users cannot use the CLI).
- Teams: workspaces, roles, permission matrix. PostgreSQL + pgvector with migrations and parity tests (trigger: multi-instance scale or a team customer).
- Web UI for the local hub.

## R7: Release (~1 week)

PyPI package and a Docker image; tagged versions with changelog; docs trimmed to README, QUICKSTART, architecture, decisions, acceptance. v1.0 requires the four release gates below.

## 4. Critical path

```
R0 ─► R2.6b-d ─► G1 ◄─ R2.1–R2.5 (your cases)
                  │
                  ├─► R5 (scope by G1) ───────────────┐
R3.1–R3.4 ─► R3.5 (G2) ─► R3.6 ─► R4 ─► v0.9 ─► R7 ─► v1.0
```

Fastest honest path to a demonstrable **v0.9**: R0 + R2.6b–d + R2.4 + G1 + R3.1–R3.6 + R4. Cut first if time is short: R5.5, R6, R2.5. **Do not cut:** R2.2–R2.4 (without them any claim of benefit is unsupported), R3.5 (without it the service stays local), R5.1 (without it it only works for small stores), R0.2 (without a licence nobody may use it).

## 5. Next two weeks (concrete)

1. R0.1, R0.2, R0.4 (licence decision is yours).
2. R2.6b, then R2.6c with before/after numbers, then R2.6d; each as a small patch with a decision entry.
3. You write 20–40 real cases (R2.2) and run the local evaluator (R2.4), sharing only the aggregate reports.
4. Hold G1 with whatever evidence exists, even if only partial, and record the outcome.

## 6. What only you can do

| Item | Why |
|---|---|
| Choose a licence (R0.2) | legal decision |
| Write real cases from your usage (R2.2) | only you have the data; your own protocol forbids sending raw histories |
| Find an independent security reviewer (R3.5) | independence cannot be supplied by the builder |
| Choose where to deploy and pay for it (R3.6) | account and cost decisions |
| Decide G1 and G2 | product decisions |

## 7. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Graph retrieval does not pay off on real data | Medium–high (synthetic evidence is already marginal) | Medium | G1 plan: make it optional; the rest of the product stands without it |
| Abstention tuning trades recall for safety | Medium | Medium | measure before/after on v3 and on real cases; keep the rule configurable |
| Remote exposure before review | Low if G2 is respected | High | loopback guard stays; tunnel tests only with throwaway data |
| Solo maintainer, two AI assistants generating code | Medium | Medium | every change goes through CI, a decision entry for contract changes, and small patches; AGENTS.md rules stay authoritative |
| Weak default embedder gives poor paraphrase handling | High with the hash embedder | Medium | R2.1 and R5.2; document the limit honestly until fixed |
| Scale cliff from full vector scans | Medium | Medium | R5.1 measurement before claiming capacity |
| Flaky CI erodes trust in tests | Medium | Low–medium | R0.1 |

## 8. Release gates (unchanged in spirit)

1. Exact-head CI plus package inspection on the release commit.
2. Held-out real-history evaluation, or an explicit documented waiver naming the risk owner.
3. Independent security/privacy review.
4. Real third-party-host integration.

Status vocabulary: PASS (evidence for the exact commit), IN PROGRESS, BLOCKED (external prerequisite), NOT ACCEPTED, WAIVED (explicit, documented). Synthetic results never count as PASS for gates 2–4.
