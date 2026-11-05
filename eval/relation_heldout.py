#!/usr/bin/env python3
"""Held-out relation-wording check for graph retrieval (R2.6e). Synthetic smoke evidence only (D-007).

Phrasing banks and pass criteria below were written BEFORE the R2.6e change and before any result was seen.
The same queries run before and after the change; the fix may not reference any wording in these banks.

Banks (all on the labelled_v3 world; gold = owner of the service reached by following the dependency edge):
  trigger      wording containing the old keyword trigger ("dependency")
  plain        relational wording without any trigger word ("depends on", "relies on", "calls", "built on", ...)
  control      NON-relational "Which team owns {e}?": first result must be the entity's own owner
Metrics: hit@5 (gold among the top 5, entity-aware) and top1 (first item is gold).

PRE-REGISTERED CRITERIA for shipping R2.6e (all must hold, hint and no-hint, pooled over seeds):
  plain 1-hop hit@5 >= 0.8 and plain 2-hop hit@5 >= 0.8;
  trigger hit@5 not lower than before by more than 0.02;
  control top1 >= 0.95 and not lower than before by more than 0.02.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agm import MemoryStore  # noqa: E402
from agm.embed import HashEmbedder  # noqa: E402
from eval.labelled_v3 import _vals, build_world  # noqa: E402
from eval.synthetic_v2 import deterministic_node_ids  # noqa: E402

BANKS = {
    ("trigger", 1): ["Which team owns the dependency of {e}?", "Who is in charge of the dependency behind {e}?",
                     "Who owns the dependency that {e} has?"],
    ("trigger", 2): ["Which team owns the dependency of the dependency of {e}?",
                     "Who owns the dependency of the dependency that {e} has?"],
    ("plain", 1): ["Which team owns the service {e} depends on?", "Who is the owner of what {e} relies on?",
                   "Which team owns the service that {e} calls?", "{e} is built on another service; which team owns it?",
                   "Which team owns the thing {e} needs in order to work?"],
    ("plain", 2): ["Which team owns the service that the service {e} depends on depends on?",
                   "Who owns what the service {e} relies on relies on?"],
    ("control", 0): ["Which team owns {e}?", "Who is the owner of {e}?", "{e} is owned by which team?"],
}


def run_seed(seed: int, episodes: int, k: int, hint: bool) -> dict:
    out: dict[tuple[str, int], list[dict]] = {key: [] for key in BANKS}
    with tempfile.TemporaryDirectory(prefix=f"agm-held-{seed}-") as tmp, deterministic_node_ids(seed):
        with MemoryStore(str(Path(tmp) / "m.db"), embedder=HashEmbedder()) as store:
            world, qs = build_world(store, seed, episodes)
            counters: dict[tuple[str, int], int] = {}
            for q in qs:
                if q.family != "multi_hop":
                    continue
                hops = int(q.id.split(":")[-1])
                for kind in ("trigger", "plain"):
                    i = counters.get((kind, hops), 0); counters[(kind, hops)] = i + 1
                    text = BANKS[(kind, hops)][i % len(BANKS[(kind, hops)])].format(e=q.entity)
                    out[(kind, hops)].append(_score(store, world, text, q.entity, set(q.gold), hint, k))
                if hops == 1:   # control: owner of the entity itself
                    own = store.retrieve(world.ctx, "owner", entity=q.entity, k=8, expand=False)
                    gold = {(i.entity, i.attribute, i.value) for i in own.items if i.attribute == "owner"}
                    i = counters.get(("control", 0), 0); counters[("control", 0)] = i + 1
                    text = BANKS[("control", 0)][i % len(BANKS[("control", 0)])].format(e=q.entity)
                    out[("control", 0)].append(_score(store, world, text, q.entity, gold, hint, k))
    return out


def _score(store, world, text, entity, gold, hint, k):
    r = store.retrieve(world.ctx, text, entity=entity if hint else None, k=k, expand=True, graph_hops=2)
    items = list(r.items)
    return {"hit": bool(_vals(items) & gold), "top1": bool(items and _vals(items[:1]) & gold)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", type=int, default=5); ap.add_argument("--episodes", type=int, default=600)
    ap.add_argument("--k", type=int, default=5); ap.add_argument("--output", type=Path)
    a = ap.parse_args()
    report: dict = {}
    print(f"relation_heldout | seeds={a.seeds} episodes={a.episodes} k={a.k} (hash embedder)\n")
    for hint in (False, True):
        runs = [run_seed(s, a.episodes, a.k, hint) for s in range(a.seeds)]
        tag = "hint" if hint else "no-hint"
        print(f"=== {tag} ===  {'bank':14}{'n':>5}{'hit@5':>8}{'top1':>8}")
        report[tag] = {}
        for key in BANKS:
            rows = [r for run in runs for r in run[key]]
            hit = statistics.fmean(r["hit"] for r in rows); top1 = statistics.fmean(r["top1"] for r in rows)
            name = f"{key[0]} {key[1]}-hop" if key[1] else key[0]
            print(f"{'':12}{name:14}{len(rows):5d}{hit:8.3f}{top1:8.3f}")
            report[tag][name] = {"n": len(rows), "hit5": hit, "top1": top1}
        print()
    if a.output:
        a.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
