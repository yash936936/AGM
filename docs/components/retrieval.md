# Retrieval

**Purpose:** return the right current facts for a query, or abstain.

**Files**
- `src/agm/store.py` (`MemoryStore.retrieve`): the flat baseline: embed the query, seed from FTS5 plus vector similarity under tenant, project, time and trust filters.
- `src/agm/retrieve.py` (`graph_retrieve`): bounded graph expansion on top of the flat seeds, then validity filter, ranking, sufficiency check (widen once, else abstain).
- `src/agm/embed.py`: `Embedder` interface and `HashEmbedder`, a deterministic, dependency-light feature-hashing embedder. A real sentence embedder is only available in `eval/spacy_embedder.py`; making one a package extra is item R2.1 and needs a decision entry first (AGENTS.md invariant 10).

**Current rules**
- Contested candidates are withheld by default in flat and graph mode; the current fact carries `contested_with`. `include_contested` returns both, each flagged (D-046).
- `entity=` scopes graph seeds only; neighbours come from the full eligible set. With `expand=False` it is a hard filter (D-047).
- Graph retrieval always follows outgoing relation edges from the anchored entity, whatever the query wording; wording only affects ranking (D-048).

**Easy to break:** vector search loads every embedding for the tenant and project into Python on each query (R5.1). Do not tune to held-out phrasings. FTS5 text is tokenised and quoted, never passed raw.

**Known open defects:** answer-slot priority depends on attribute wording (R2.6f); abstention rarely fires (R2.6c); near-duplicate names leak (R2.6d). See `debug.md` DBG-007.

**Tests:** `test_retrieve.py`, `test_entity_hint_expansion.py`, `test_relation_wording.py`, `test_labelled_v3.py`, `test_iterative_baseline.py`.
**Decisions:** D-006, D-046, D-047, D-048.

---
**Next:** Return to [`context.md`](../../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
