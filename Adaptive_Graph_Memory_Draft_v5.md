# Adaptive Graph Memory: Draft v5

*Planning stage, architecture-focused. Supersedes v4. Items marked **\[proposed\]** are suggested defaults and need confirmation.*

## 1. Summary

A **model-agnostic memory layer** for AI agents. It sits outside any LLM, so a session can end and a different model, agent or LLM can continue with the same context.

- **Core structure:** a typed temporal graph (episodes, facts, entities, procedures), stored as an append-only event log with the graph as a view over it.
- **Lifecycle:** consolidation (experience becomes durable knowledge) and decay (unused or superseded items fade).
- **Trust:** every item carries confidence, provenance and writer identity, which drive ranking, abstention and write control.
- **Portability:** a handoff protocol (task state plus relevant long-term memory, packed for the target model), with fidelity measured, not assumed.
- **Hierarchy:** emerges from consolidation as a derived layer, and becomes a retrieval index only if scale demands it.

## 2. Problem statement

Long-running agents, often across several models, accumulate memory that is episodic, entity-centric and time-dependent. Current memory layers tend to fail in these ways:

1. **Stale and contradicted facts** returned next to current ones.
2. **Unbounded growth** that degrades retrieval.
3. **Cross-cutting questions** (all about one entity, what changed over time) that similarity search handles poorly.
4. **Unwarranted confidence.** Lossy extraction gives facts with no provenance, treated the same as verified ones.
5. **Untrusted or malicious content** stored as knowledge.
6. **Lost context at model or agent switches**, so users re-explain decisions.
7. **Conflicting writes** when several agents share memory.

Which of these dominate in practice is an empirical question (section 11).

## 3. Core thesis and hypotheses

**Central bet (unproven):** a graph that consolidates, decays and scores trust on its own contents, behind a model-neutral interface, gives more accurate, current and better-calibrated recall than strong flat retrieval, and supports reliable continuation across models, at comparable latency and cost.

| ID | Hypothesis | Tested against |
| --- | --- | --- |
| H1 | Graph expansion improves multi-hop, entity-centric and temporal questions | Flat hybrid RAG, flat ANN with metadata filters |
| H2 | Explicit supersession with validity windows reduces stale-fact errors | Flat retrieval with recency heuristics |
| H3 | Consolidation and decay keep accuracy and latency stable as memory grows | Same system with both off (never-forget control) |
| H4 | Confidence and provenance improve abstention and cut unsupported answers | Same system ignoring scores |
| H5 | Handoff through memory preserves task continuity across models | Original model continuing with full context |
| H6 | Write control (trust tiers, probation) limits damage from bad writers | Same system with all writers trusted equally |
| H7 (conditional) | A derived hierarchy reduces latency or tokens at large scale | Collapsed search over all nodes |

**Kill criterion.** If H1 and H2 both fail at the target scale, ship the flat system with the trust, handoff and safety layers and stop. H3 to H6 can each be applied to a flat store, so they don't depend on the graph winning.

**Weakest points.** H3 (forgetting can destroy needed information) and H5 (injected context is not understood context) are the least proven. Test them first against their controls.

## 4. Target scale and workload \[proposed\]

- **Workload:** a long-running coding agent (objective outcomes such as tests passing), with a conversational assistant as a second case.
- **Scale:** 50k to 1M items per agent, with a 5k to 50k development tier.
- **Query mix:** single-fact, entity-centric, temporal, multi-hop, and unanswerable (abstention).
- **Time horizon:** simulated weeks to months of activity.
- **Multi-agent and multi-model cases:** two to four agents or models sharing a store, and at least three model pairs for handoff tests.

## 5. Architecture

### 5.1 Event log and graph view

All writes are events: writer ID, logical timestamp (hybrid logical clock), base version, idempotency key, payload. The graph, indexes and summaries are rebuildable views. This makes revocation, rollback and audit possible. Raw inputs are archived untouched.

### 5.2 Memory types

| Type | Meaning | Default lifetime | Update rule |
| --- | --- | --- | --- |
| Episode | A raw event or task record | Short to medium, decays unless consolidated | Append-only |
| Fact | An atomic statement about an entity | Long, until superseded | Supersede, never overwrite |
| Entity | A canonical identity with aliases | Long | Merge only with evidence |
| Procedure | A reusable how-to, decision or rule, with rationale | Long, versioned | New version, history kept |

**Task state** is a separate structured object (goal, plan, progress, decisions, open questions, files and tools touched). It is persisted per session for handoff, not mixed into the long-term graph.

### 5.3 Node and edge structure

Every node has: ID, type, content, valid-from and valid-to, **confidence**, **provenance** (source episode and span), **writer ID and writer trust tier**, usage statistics, decay weight, and an embedding tagged with its embedding-model ID. One fixed embedding model serves the store, independent of the chat LLM, and items are re-embedded on upgrade.

| Edge | Connects | Purpose |
| --- | --- | --- |
| Mentions | Fact or episode to entity | Entity-centric expansion |
| Supersedes | Old fact to new fact | Validity filtering, history |
| Contests | Competing facts | Flags unresolved conflict |
| Derived-from | Fact or procedure to source episodes | Provenance, audit, safe deletion, rollback |
| Relates | Typed link between facts or entities | Multi-hop expansion |
| Similar | Sparse kNN link, built offline | Soft association |
| Summarises | Group node to members | The derived hierarchy |

**Confidence** combines extraction confidence, source and writer trust, corroboration by **independent** sources, and age. It is a ranking feature and an abstention input, never a hard filter.

### 5.4 Consolidation

Runs in batches and in shadow mode before commit.

- **Episode to fact:** repeated or high-salience episodes are distilled into facts, linked via Derived-from.
- **Fact to procedure:** facts that repeatedly precede success are promoted to a procedure. Promotion needs corroboration and passes the procedure gate (section 5.8).
- **Merge:** duplicates merge, with corroboration counts updated by independent source only.
- **Entity resolution:** aliases merge above an evidence threshold, otherwise flagged.
- **Group formation:** community detection over entity and similarity edges produces topic groups and summaries (the emergent hierarchy). Summaries are a rebuildable cache.

### 5.5 Decay and pruning

- **Decay weight** falls with age and non-use, and rises with retrieval, citation and corroboration.
- **Archive, don't delete.** Low-weight items move to cold storage and can be restored on a cold-path miss.
- **Pin list** exempts user-pinned items, safety-critical facts and anything legally required.
- **Superseded facts** stay queryable for history but are excluded from "current" answers.
- **Hard deletion** removes content and all derived data (embeddings, edges, summaries, caches), then verifies the item no longer surfaces.
- **Hysteresis** on thresholds prevents items oscillating between active and archived.

### 5.6 Read path

1. Embed the query once.
2. **Seed:** hybrid search (vector plus keyword) with metadata filters (entity, time, type, tenant, scope). This step alone is the flat baseline.
3. **Expand:** bounded traversal (hop limit, fan-out cap, hub degree caps), filtered by validity.
4. **Rank:** similarity combined with confidence, corroboration, writer trust, recency and decay weight. Rerank the top 20 to 30.
5. **Sufficiency check:** if evidence is weak, widen once (including cold storage), then abstain with what is known and how uncertain it is.
6. **Return** snippets with provenance, confidence, contested flags and the route taken.

Each session reads from a **consistent snapshot**, refreshed at defined points such as handoff. Retrieved memory is always labelled as data, never as instructions. Expansion must beat step 2 or it is removed.

### 5.7 Write path

1. Authenticate the writer, redact secrets, screen for instruction-like text, assign trust tier.
2. Segment into atomic units and classify.
3. Extract with exact source span and confidence.
4. **Salience filter:** store only what is worth keeping (new information, corrections, task outcomes).
5. Decide ADD, UPDATE, SUPERSEDE or NO-OP. Updates use **compare-and-swap** on the version the writer saw. A stale base makes the write a **contested candidate** linked to the competing fact.
6. Write to the searchable store immediately. Consolidation and entity resolution follow asynchronously.

### 5.8 Multi-agent write control

**Concurrency**

- Single-valued facts: latest valid-time wins unless there is a large trust gap.
- Multi-valued facts: keep both.
- Unresolved or high-stakes conflicts: keep both, flag, and return both at retrieval with a warning.
- Consolidation and decay take a short per-entity lease so they don't race with live agents.
- Idempotency keys prevent duplicates from retries.

**Trust tiers** (for example: human-verified, verified tool output, trusted agent, untrusted or external content)

- New or low-trust writes enter on **probation**: no promotion to procedures, no use in consolidation, excluded from high-stakes retrieval until corroborated by an independent writer or checked against the source.
- **Procedure gate:** anything that changes agent behaviour needs a test pass or human approval.
- **Namespaces:** agents write to their own namespace and reach shared memory only through promotion.
- **Revocation and rollback:** revoke a writer or time window, then recompute everything derived from it.
- **Automatic trust adjustment** from contradiction rate, anomalous write volume, and how often an agent's memories precede task failures.

### 5.9 Portability and handoff

**Handoff packet** (built at session end):

- Final task state.
- Decisions with rationale, user corrections, unresolved items.
- Pointers to the raw transcript and key episodes, so nothing depends on a summary alone.

**Context assembly** (at new session start), under the target model's token budget:

1. Pinned items.
2. Task state.
3. Retrieved long-term memory, ranked by relevance, confidence and trust.
4. Formatting for the target model (window size, instruction style, tool support).

**Readback before proceeding.** The new session states its understanding of the task, key decisions and open items. This is compared with the packet (automatically, or by the user for important tasks). Mismatches are fixed before work begins. If fidelity is low, the new model gets links to raw episodes and is told to ask before assuming.

**Volatile-fact check.** Facts that can drift (files, versions, deadlines) are re-verified before being acted on.

**Interface.** A model-neutral API or MCP server exposing retrieve, write, supersede, delete and handoff.

**Scoping.** Memory is tagged by user, project and agent, with read and write permissions per connecting agent. Switching to a different provider sends memory to that provider, so sensitive items need an explicit sharing policy.

### 5.10 The optional hierarchy

A view over the graph, produced by consolidation. It becomes a retrieval index only if H7 is supported: scale tests show a latency or token problem that flat-plus-graph can't meet, and the index beats collapsed search over all nodes.

## 6. Why this design, and its costs

**Reasons**

- It matches agent memory's real structure (entities, time, relations).
- It makes memory a durable asset independent of any one model.
- Supersession, provenance, trust, deletion and rollback are native graph and log operations.
- Each component can be ablated, so failures are attributable.

**Counterpoints**

- **Extraction is the ceiling.** Wrong merges and wrong edges look authoritative.
- **Forgetting is risky.** Decay can remove the one fact you later need.
- **Confidence must be calibrated.** Uncalibrated scores give false assurance, and calibration needs labelled data.
- **Consolidation can launder errors.** A wrong fact repeated by one source must not gain corroboration.
- **Readback checks what a model says it understood, not how it will behave.** Scores from an LLM judge are noisy estimates.
- **Trust scores can be gamed**, and a trusted but wrong agent still pollutes memory.
- **Meaning-level conflicts can't be resolved automatically.** They stay flagged for an arbiter.
- **Handoff is lossy** even with raw links. Models may weigh the same facts differently.
- **Traversal is less predictable than tree pruning.** Hubs need caps.
- **Novelty is thin.** Temporal graph memory is close to this design. The measurable differences are lifecycle, calibrated trust, write control and portability.
- **Published graph-memory gains are mixed**, and many are vendor-reported. Verify independently.
- **Scope is wide.** See section 8.

## 7. Guardrails (Tier 1)

Each uses Detect, Act, Escalate, with an ID, version, test set and metric.

- **P2 Lossy extraction:** check that the source span supports each fact, quarantine below threshold, audit samples.
- **P3 Contradictions:** same entity and attribute with different values. Supersede if clearly newer, otherwise contest.
- **P11 Secrets and personal data:** redact before storage, never embed raw secrets.
- **P12 Prompt injection in memory:** quarantine instruction-like text, label retrieved memory as untrusted data.
- **P13 Deletion:** delete content and all derived data, then verify.
- **P21 Over-forgetting:** alert when answers exist only in archived items and the archive-hit rate rises.
- **P22 Writer poisoning:** probation, trust adjustment, revocation and rollback.
- **P23 Stale handoff:** volatile-fact verification and readback mismatch handling.

Tenant isolation is designed in from the start.

## 8. Scope control

**First version includes:** the event log, typed graph, supersession, confidence and provenance, consolidation, decay, writer identity and trust tiers, compare-and-swap writes, the handoff protocol with readback, and Tier 1 guardrails.

**Deferred until evidence supports them:** reflection (lessons derived from episodes), task-conditioned retrieval, a success-signal learning loop, a derived tree index, and Tier 2 and 3 playbooks.

If the first version proves too large, cut in this order: multi-agent namespaces and automatic trust adjustment, then consolidation beyond episode-to-fact, then the handoff interface polish. Keep the event log, supersession, provenance and the baselines in step 0.

## 9. Sequencing with gates

| Step | Work | Gate to proceed |
| --- | --- | --- |
| 0 | Flat baselines (hybrid RAG, flat ANN with filters), failure analysis | Failure taxonomy shows enough temporal, cross-entity, growth or handoff failures to justify the graph. Otherwise stop |
| 1 | Event log, temporal graph, supersession, provenance, trust, Tier 1 guardrails | H1 or H2 beats baselines by the pre-registered margin |
| 2 | Handoff protocol and multi-agent write control | H5 and H6 meet pre-registered thresholds against their controls |
| 3 | Consolidation and decay in shadow mode | H3 holds against the never-forget control |
| 4 | Derived hierarchy (conditional) | Only if H7's trigger conditions are met |

## 10. Risks

- Graph does not beat flat retrieval (kill criterion).
- Extraction errors and wrong merges (P2, shadow-mode merging).
- Over-forgetting (pin list, archive, P21, never-forget control).
- Error laundering through consolidation (independent-source corroboration).
- Miscalibrated confidence (calibration metric, labelled audit set).
- Poisoned or low-quality writers (P22, probation, rollback).
- Handoff fidelity falls short (readback, raw links, fidelity tests).
- Provider data exposure on model switches (sharing policy).
- Hubs, traversal cost and maintenance cost.
- Crowded field (differentiate on measured results).
- Planning momentum and elegance bias (the step 0 stop condition makes stopping cheap).

## 11. Evaluation

- **Baselines:** (1) flat hybrid RAG with good chunking and reranking, (2) flat ANN with metadata filters, (3) a Graphiti or Mem0 style layer, (4) collapsed search and a community-summary baseline (for H7 only).
- **Ablations, one at a time:** graph expansion, supersession, consolidation, decay, confidence ranking, trust tiers.
- **Controls:** never-forget store (H3), confidence-ignored ranker (H4), equal-trust writers (H6), original model with full context (H5).
- **Benchmarks:** LongMemEval, LoCoMo, a custom coding-agent set, long-horizon simulations, and multi-agent write-conflict scenarios. Synthetic sets must not embed a built-in hierarchy. Include adversarial writer scenarios (injected and low-quality memories).
- **Metrics:**
  - *Quality:* accuracy, stale-fact error rate, unsupported-fact rate, abstention correctness, calibration error, archive-hit rate.
  - *Handoff:* task success, repeated questions, contradictions of earlier decisions, readback mismatch rate, across at least three model pairs.
  - *Write control:* conflict rate, contested-fact resolution accuracy, poisoned-write detection and rollback completeness.
  - *Cost:* p50 and p95 latency, tokens per query, store growth rate, hub degree.
- **Statistics:** confidence intervals and multiple seeds. Check power before setting tolerances. Treat LLM-judge scores as estimates.
- **Pre-registration:** fix the equal-accuracy tolerance, minimum wins and thresholds for H1 to H7 before recording any baseline.
- **Reporting:** state handoff results as "X% fidelity on Y tasks across these model pairs", never "seamless".

## 12. Open decisions

- **D1.** Confirm workload, scale, horizon and the model pairs for handoff tests.
- **D2.** Thresholds and tolerances for H1 to H7, fixed before any baseline.
- **D3.** Confidence formula and calibration method.
- **D4.** Decay function, archive thresholds and pin-list policy.
- **D5.** Consolidation triggers (time, count or salience).
- **D6.** Entity-resolution policy (auto-merge versus flag).
- **D7.** Expansion method and caps.
- **D8.** Trust tier definitions and promotion rules.
- **D9.** Conflict resolution rules per attribute type.
- **D10.** Handoff packet schema and readback comparison method.
- **D11.** Cross-provider sharing policy.
- **D12.** Whether any hierarchy is built as an index (decided by H7).
- **D13.** Independent verification of benchmark and related-work claims before any public statement.

## 13. What changed from v4

| v4 | v5 |
| --- | --- |
| Graph is the primary store | Append-only event log is the source of truth, graph is a view |
| Portability not covered | Handoff packet, context assembly, readback, model-neutral interface, fixed embedding model |
| Single-agent assumption | Concurrency control, compare-and-swap, contested facts, snapshot reads, leases |
| Confidence and provenance | Adds writer identity, trust tiers, probation, namespaces, revocation and rollback |
| Hypotheses H1 to H5 | Adds H5 (handoff fidelity) and H6 (write control), H7 is now the hierarchy |
| Guardrails to P21 | Adds P22 writer poisoning and P23 stale handoff |
| No sequencing | Short gated sequence with explicit cut order if scope is too large |
| "Seamless" implied | Replaced by measured fidelity reporting |

The riskiest bets in this version are H3 and H5. Test those against their controls before building the rest.
