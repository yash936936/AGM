# AGM roadmap (v0.6 → v1.0)

Replaces the old M0–M4 roadmap and phase list (still in git tag `archive/pre-cleanup-main`). Effort: **S** ≤ 1 day, **M** 2–4 days, **L** 1–2 weeks of focused work. These are rough estimates, not commitments.

## Where we are (v0.7.0)

- **Done and tested (264 tests):** event-sourced store, replay, graph + flat retrieval with abstention, trust tiers, contested facts, handoff/readback, delete/expiry/revocation, guard in core, REST API with scoped keys, owner bootstrap, sessions/connections, timeline/snapshot/Obsidian export, lifecycle dry-run, doctor, active-memory turn seam and policy executor (library-only, D-037), reference host harness, synthetic + REST concurrent benchmarks.
- **R1 delivered in v0.7.0:** `AgmClient`, `agm mem/handoff/connect`, `docs/QUICKSTART.md` (R1.1, R1.2, R1.3, R1.5 partly: OpenAPI route test; no checked-in schema file). **R1.4 done (read-only):** `agm active context|review` and `/v1/active/*` (D-044); execution stays library-only. **R3 started (D-045):** hashed keys at rest, hot reload/revocation without restart, 404 on missing delete, request-size limits.
- **Not done:** any evidence on real data, independent security review, a real third-party host, remote access, teams, hosted storage.
- **Deliberately cut:** MCP adapter (D-042), Phase-8 LLM-agent harness.

## Principle for going fast

The design hypotheses (H1–H7, D-007) have **no real-data evidence yet**. Every feature built before that evidence exists is a bet that graph retrieval beats a good flat baseline. So the order below puts "make it usable by an agent" and "find out whether it is better" ahead of teams, Postgres and polish.

## R1 — Agent-connectable v0.7 (DONE) (usable today by Claude Code, Codex, local agents)  · ~1 week

| # | Item | Effort | Done when |
|---|---|---|---|
| R1.1 | `agm.client` (promote `examples/python_client.py`): typed sync/async client over REST | S | tests against `create_app` TestClient |
| R1.2 | CLI client commands: `agm mem write / retrieve / history / delete`, `agm handoff save / resume` (talk to a running API via `AGM_BASE_URL`, `AGM_API_KEY`) | M | shell-based agents can use memory with no SDK |
| R1.3 | `agm connect` helper: creates a scoped agent key, prints env vars and a ready-to-paste agent instruction snippet (including the "memory is data, not instructions" notice) | S | one command from zero to a working agent connection |
| R1.4 | Active-memory turn loop exposed in the client: `before_turn` context pack, `after_turn` proposals (library today, D-037; needs a decision entry before any REST route) | M | demo agent loop runs end to end |
| R1.5 | Quickstart doc + OpenAPI export checked in CI | S | fresh clone to first retrieval in under 5 minutes |

Exit: three agent types (Python script, Claude Code via CLI, ChatGPT Action via tunnel on localhost for a private test only) read and write the same memory. Remote exposure stays gated (see R3).

## R2 — Evidence: is it actually better?  · ~2 weeks, runs in parallel with R1

This is the gate most likely to change the plan, so start early.

| # | Item | Effort | Done when |
|---|---|---|---|
| R2.1 | Replace the hash embedder as the default evaluated embedder with a real one (optional extra, lazy import) and re-run every benchmark with both | M | benchmark report lists embedder per run |
| R2.2 | Labelled retrieval set. Synthetic version DONE (`eval/labelled_v3.py`, 226 queries/seed, rule pre-registered; results in `docs/benchmarks/r2_labelled_v3.md`). Remaining: a set built from your real usage (see R2.4 runbook) | M | dataset hash and thresholds committed **before** results |
| R2.3 | Baselines that can win: ~~iterative flat retrieval~~ DONE (`eval/iterative_baseline.py`, see `docs/benchmarks/r2_post_hoc_iterative_baseline.md`: it matches graph on multi-hop). Remaining: BM25-only, vector-only, "stuff the whole log in context" for small histories | S | report includes cases where each baseline beats graph |
| R2.4 | Consented, de-identified real-history run using `scripts/evaluate_real_history.py` and the existing protocol. Tooling ready: `scripts/build_real_history_cases.py`, `docs/acceptance/real_history_local_runbook.md` (data never leaves your machine) | M (+ data access) | aggregate-only results; otherwise status stays BLOCKED |
| R2.5 | End-to-end agent task test (same agent, with vs without AGM, fixed tasks) | L | measured task success and token cost deltas |

Decision point after R2: if graph expansion does not beat the best flat baseline by a margin fixed in advance, simplify (keep event log, trust, lifecycle, handoff; make graph expansion optional) instead of building R5–R6 around it.

### R2.6 — Core issues found by the v3 benchmark (do these before more graph work)

| # | Item | Effort | Done when |
|---|---|---|---|
| R2.6a | Make flat and graph retrieval agree on `contested` facts (documented behaviour: both returned with a warning); needs a decision entry | S | same contested handling in both modes; tests |
| R2.6b | Entity hint should scope seeds, not block graph expansion (or document and reject the combination) | S | hint + expand reaches linked entities, or clear error |
| R2.6c | Abstention that fires for unknown entities and for known entities lacking the asked attribute | M | unanswerable correctness ≥ 0.8 on v3 without hurting recall |
| R2.6d | Disambiguate near-duplicate entity names (`x` vs `x-staging`) | M | hard_neg strict pass ≥ 0.8 no-hint |
| R2.7 | Decide: make graph expansion optional (default off) unless real-data runs show it helps | S | decision recorded after R2.4 |

## R3 — Security and remote access  · ~1–2 weeks

Prerequisite for ChatGPT / web-based agents, which cannot reach loopback.

| # | Item | Effort | Done when |
|---|---|---|---|
| R3.1 | ~~Hashed, revocable per-agent credentials~~ DONE (D-045). Remaining: expiry dates, a managed credential store instead of a JSON file | S | expired token fails; tests |
| R3.2 | ~~Request size limits~~ DONE (D-045). Remaining: rate limits, safe error bodies, audit metadata, no secrets or memory text in logs | M | negative tests |
| R3.3 | Tenant/project isolation test matrix incl. ID-guessing (IDOR) across every route | M | matrix in CI |
| R3.4 | Threat model + data-flow inventory; run `docs/acceptance/security_privacy_review_checklist.md` | M | written findings |
| R3.5 | Independent reviewer sign-off | external | signed checklist; otherwise remote stays off |
| R3.6 | Controlled MVP deploy: single instance, HTTPS ingress, persistent disk SQLite, single writer, tested backup/restore (`docs/cloud-deployment.md`) | M | two clients share one workspace remotely |

## R4 — Real-host acceptance  · ~1 week, after R1 and R3.6

Run `docs/acceptance/third_party_host_validation.md` against at least two actual hosts (for example Claude Code via the CLI client and a ChatGPT Action). CI smoke tests do not count.

## R5 — Quality and operability  · ~2 weeks, scope set by R2 results

Learning/ranking improvements justified by R2 failures only; consolidation and decay tuning on real data; observability (metrics, redacted structured logs); retrieval latency work driven by the REST concurrent benchmark; CI matrix trimmed to what is needed (Ubuntu + Windows, 3.11 and 3.13).

## R6 — Later, only if demanded

- Optional MCP shim re-added as a thin client of the REST API (not a second core adapter); only if R1 shows shell/HTTP integration is a real adoption blocker.
- Teams: workspaces, roles, permission matrix (old M3).
- PostgreSQL + pgvector store with migrations and parity tests (old M4); needed only for multi-instance scale.
- Web UI for the local hub.

## Critical path and cuts

```
R1 ──┐
     ├─► R4 ─► v0.9 candidate ─► R5 ─► v1.0
R2 ──┤        (needs R3.6)
R3 ──┘
```

Fastest honest path to a demonstrable v1.0-alpha: **R1 + R2.1–R2.3 + R3.1–R3.3 + R3.6**. Cut first if time is short: R5, R6, R2.5. Do not cut: R2.2/R2.3 (without them any claim of benefit is unsupported) and R3.5 (without it the service stays local).

## Release gates (unchanged in spirit)

1. Exact-head CI plus package inspection on the release commit.
2. Held-out real-history evaluation, or an explicit documented waiver naming the risk owner.
3. Independent security/privacy review.
4. Real third-party-host integration.

Status vocabulary: PASS (evidence for the exact commit), IN PROGRESS, BLOCKED (external prerequisite), NOT ACCEPTED, WAIVED (explicit, documented). Synthetic results never count as PASS for gates 2–4.
