# AGM Phase 2 Report

**Scope:** Graph layer, ranking, confidence/trust placeholders, compare-and-swap conflicts, and abstention.

**Review status:** Implemented and tested in the builder environment. Windows verification by the repository owner and supervisor review are still pending. D-008 weights remain uncalibrated placeholders.

## Files created or changed

- `README.md` — Phase 2 setup, usage, capability boundaries, and scoring caveat.
- `context.md` — current state and next-step routing.
- `pyproject.toml` — package version `0.2.0` and Phase 2 description.
- `scripts/pack.py` — creates a Phase 2 archive when `PHASE2_REPORT.md` exists, otherwise keeps Phase 1 packaging; excludes `.git`, environments, caches, databases, and previous build output.
- `src/agm/__init__.py` — Phase 2 package metadata.
- `src/agm/cli.py` — Phase 2 label in the CLI/demo output; existing command behavior retained.
- `src/agm/store.py` — entity and alias resolution, alias-aware identity/history/filtering, graph edges, stale-base and trust-gap contested writes, event-stable entity references, and delete/replay consistency fixes.
- `src/agm/retrieve.py` — flat-seed compatibility, bounded entity/edge expansion, temporal validity filtering, score ranking, one-time widening, abstention, and route reporting.
- `src/agm/trust.py` — tier weights, provisional confidence formula, age/recency factor, independent corroboration count, and weighted rank.
- `tests/test_retrieve.py` — Phase 2 retrieval and alias regression coverage.
- `tests/test_contested.py` — compare-and-swap, trust-gap, contested replay and version-chain tests.
- `tests/test_trust_phase2.py` — D-008 tier, age and ranking formula tests.
- `tests/test_replay.py` — added replay consistency checks for aliases, graph edges, FTS and hard deletion.
- `docs/decisions.md` — D-011 through D-013 (newest entries).
- `docs/debug.md` — Phase 2 implementation/test log.
- `docs/phases.md` — roadmap updated with implementation state.
- `docs/readme.md` — truthful project state and commands.
- `docs/status.md` — current phase and validation status.

Phase 1 source files and contracts are retained. The supplied overlay archive contains the above files plus the existing Phase 1 source/tests needed for local integration; it is meant to be extracted into the existing repository, not to replace the whole repository with a docs-incomplete snapshot.

## Tests and what they prove

### Phase 1 regression tests

- `tests/test_store.py`: write and retrieve, correction/supersession, idempotency, no-op writes, multi-valued facts, deletion and FTS query safety, and required entity validation.
- `tests/test_replay.py::test_replay_rebuild_is_deterministic_after_writes_supersede_delete`: replay reconstructs matching node rows and embeddings after write, correction and deletion.

### Phase 2 tests

- `test_expand_false_matches_phase1_flat_baseline`: `expand=False` returns the Phase 1 flat baseline behavior.
- `test_graph_expansion_returns_related_entity_fact`: graph expansion finds an entity-related fact beyond the direct seed.
- `test_unanswerable_query_abstains_after_one_widening`: unsupported queries trigger widening and abstention instead of blindly returning a nearest match.
- `test_entity_alias_resolves_for_filter_and_history`: aliases resolve for entity-filtered retrieval and history.
- `test_as_of_filter_applies_to_graph_expansion`: expanded nodes respect the requested validity interval.
- `test_independent_writer_corroboration_raises_effective_confidence`: an independent writer can contribute to the provisional corroboration factor.
- `test_write_through_unique_alias_updates_canonical_entity`: a correction through a unique alias keeps the entity identity and version chain.
- `test_alias_added_later_updates_fts_for_existing_entity_nodes`: adding an alias makes existing nodes discoverable with the alias text.
- `test_ambiguous_alias_refuses_write_instead_of_merging_entities`: an ambiguous alias cannot silently merge distinct entities.
- `test_graph_expansion_supports_two_hops_but_caps_at_two`: the internal retrieval helper supports at most two hops.
- `test_stale_base_version_creates_contested_candidate_and_returns_both`: a stale `base_version` creates a contested candidate and keeps both competing facts visible.
- `test_matching_base_version_allows_normal_correction`: a current base version allows a normal correction.
- `test_contested_event_replays_with_edges_and_same_ids`: contested facts and edges reproduce through event replay.
- `test_large_trust_gap_keeps_higher_tier_fact_current`: a large tier gap contests a lower-trust correction rather than overwriting the stronger fact.
- `test_contested_candidates_do_not_advance_accepted_chain_version`: a contested candidate does not advance the accepted single-value version chain.
- `test_tier_weights_match_decision_d008`: the four tier weights match D-008.
- `test_age_factor_is_one_at_zero_age_and_half_after_ten_years`: the provisional 10-year age scale is deterministic at its documented boundaries.
- `test_rank_score_matches_d008_weighted_sum`: rank calculation follows the D-008 weighted sum.
- Additional replay tests verify canonical entity identity and relation targets survive when the event that first declared an alias is scrubbed, and that deleted source nodes do not regain edges after rebuild.

## Commands executed in the builder environment

Runtime: Python 3.13.5. This is not the owner's Windows/Python 3.14.7 environment.

- `PYTHONPATH=src python -m pytest -q`
  ```text
  ...............................                                          [100%]
  31 passed in 0.55s
  ```
- `PYTHONPATH=src python -m compileall -q src tests`
  ```text
  Exit code 0; no output.
  ```
- `PYTHONPATH=src python -m agm demo`
  ```text
  Current memories:
    agm.phase = Phase 2 [n_628a53486e884c899018e17d31ec8b6f]
  Including superseded memories:
    Phase 2 [n_52d8a3958d904faaa7ae52bdf53ec7cc]
    draft [n_b2543d610188453e856e5b43ea0cc951]
  Delete old draft: True; replacement: n_52d8a3958d904faaa7ae52bdf53ec7cc
  ```
- `PYTHONPATH=src python -m agm rebuild --db ./demo.db`
  ```text
  Rebuilt views: 0 nodes
  ```
  This command opened a separate, empty `demo.db`. The demo intentionally uses a temporary database and does not populate `./demo.db`.
- `python -m pip install -e ".[dev]"`: **NOT RUN in the builder environment for Phase 2**. The owner successfully installed the Phase 1 environment on Windows earlier; Phase 2 adds no runtime dependencies.
- `python scripts/pack.py`
  ```text
  Created `dist/agm-phase2.zip`; archive inspection confirmed zero `.git`, database, or cache entries.
  ```
  The handoff overlay is separately assembled from an explicit file list so it can be extracted over the owner's existing checkout without replacing design documents that were not present in the builder workspace.
- Owner's Windows/Python 3.14.7 Phase 2 tests: **NOT RUN yet**.

## Contract concerns and limitations

1. The frozen `RetrieveResult` contract has no general `warnings` field. Contested retrieved nodes use `contested_with`; the write result carries a human-readable warning in `WriteResult.warnings`. No Pydantic contract was changed.
2. The frozen public `MemoryStore.retrieve` signature has no `hops` parameter. Public graph retrieval defaults to one hop; the internal helper supports one or two hops and rejects depths over two.
3. D-008 says to abstain below 0.25 but does not define its age factor or how to separate evidence sufficiency from composite ranking. D-012 defines the threshold over absolute evidence relevance, while D-013 defines a provisional 10-year age factor. These are explicit, uncalibrated choices, not measured results.
4. Entity-alias resolution is deliberately conservative: only unique aliases resolve; ambiguous aliases raise `ValueError` rather than auto-merging identities. Evidence-threshold entity merge is not implemented in Phase 2.
5. Phase 3 REST/MCP adapters, authentication, redaction/quarantine, Phase 4 full trust probation/revocation and handoff methods, and Phase 5 evaluation/lifecycle are outside this scope and remain unfinished.

## Assumptions

- Existing frozen Pydantic model and public method signatures remain authoritative.
- A unique alias can be used as an input name for filters, history, writes, and relation targets.
- Relationship targets resolve to entity IDs/canonical names at write time for deterministic replay.
- The age factor is `1 / (1 + age_days / 3650)` until labelled evaluation data allows calibration.
- The D-008 trust, confidence, recency and decay coefficients are ranking placeholders, not probabilities.
- Hard deletion remains irreversible: its original event payload is scrubbed per D-010.

## Not finished

Phase 2 code is implemented and the builder environment passes all 31 tests, but it has not yet received Windows verification or supervisor review. Phases 3–5 have not been implemented. Do not expose a network service before the Phase 3 auth and guard layers are implemented and reviewed.
