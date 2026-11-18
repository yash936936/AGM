from __future__ import annotations

from types import SimpleNamespace

from eval.labelled_v3 import MODES, ANSWERABLE, _vals, run_seed
from eval.synthetic_v2 import make_embedder


def test_scoring_is_entity_aware():
    other = SimpleNamespace(entity="b", attribute="owner", value="infra-ops")
    assert _vals([other]) == {("b", "owner", "infra-ops")}
    assert ("a", "owner", "infra-ops") not in _vals([other])


def test_small_run_has_every_mode_regime_and_family():
    out = run_seed(0, episodes=20, k=5, embedder=make_embedder("hash"))
    assert out["questions"] >= 100
    for hint in (False, True):
        for mode in MODES:
            rows = out[(mode, hint)]
            assert len(rows) == out["questions"] and all("pass" in r for r in rows)
    families = {r["family"] for r in out[("graph", False)]}
    assert set(ANSWERABLE) <= families and {"injection", "unanswerable"} <= families
    assert all(r["pass"] for r in out[("graph", False)] if r["family"] == "injection")



def test_vector_baseline_is_independent_cosine_search():
    import numpy as np

    from eval.labelled_v3 import VectorBaseline

    class TinyEmbedder:
        model_id = "tiny-test-v1"

        def embed(self, text):
            return np.asarray([2.0, 0.0] if "alpha" in text else [0.0, 3.0], dtype=np.float32)

    docs = [
        {"text": "alpha owner team-a", "entity": "alpha", "attr": "owner", "value": "team-a"},
        {"text": "beta owner team-b", "entity": "beta", "attr": "owner", "value": "team-b"},
    ]
    rows, score = VectorBaseline(docs, TinyEmbedder()).search("alpha", 1)
    assert rows == [docs[0]]
    assert score == 1.0


def test_whole_log_baseline_reports_context_size_and_respects_budget():
    out = run_seed(0, episodes=5, k=5, embedder=make_embedder("hash"), whole_log_max_chars=1)
    rows = out[("whole_log", False)]
    assert rows
    assert all(row["context_chars"] > 1 for row in rows)
    assert all(row["context_tokens_estimate"] > 0 for row in rows)
    assert all(row["abstain"] is False and row["context_fits"] is False and row["n"] == 0 for row in rows)
    fits = run_seed(0, episodes=5, k=5, embedder=make_embedder("hash"), whole_log_max_chars=200000)
    full_rows = fits[("whole_log", False)]
    assert all(row["context_fits"] is True and row["n"] > 0 for row in full_rows)
