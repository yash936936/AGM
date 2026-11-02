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
