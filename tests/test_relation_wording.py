"""D-048: following outgoing relations must not depend on query wording."""
from __future__ import annotations

import pytest

from agm import Ctx, MemoryStore, Relation, WriteItem

CTX = Ctx(tenant_id="t", writer_id="w", tier="human_verified", project="p")
PLAIN_1HOP = [
    "Which team owns the service alpha depends on?",
    "Who is the owner of what alpha relies on?",
    "Which team owns the service that alpha calls?",
    "alpha is built on another service; which team owns it?",
]
PLAIN_2HOP = [
    "Which team owns the service that the service alpha depends on depends on?",
    pytest.param(
        "Who owns what the service alpha relies on relies on?",
        marks=pytest.mark.xfail(strict=True, reason="R2.6c: abstains on low lexical similarity before expansion runs"),
    ),
]


@pytest.fixture()
def store(tmp_path):
    with MemoryStore(str(tmp_path / "w.db")) as s:
        for e, owner in (("alpha", "team-red"), ("beta", "team-blue"), ("gamma", "team-green"), ("delta", "team-grey")):
            s.write(CTX, WriteItem(kind="fact", entity=e, attribute="owner", value=owner, text=f"{e} is owned by {owner}."))
        for src, dst in (("alpha", "beta"), ("beta", "gamma")):
            s.write(CTX, WriteItem(kind="fact", entity=src, attribute="dependency", value=dst,
                                   text=f"{src} runs on top of {dst}.", relations=[Relation(rel="relates", target=dst)]))
        # delta points at alpha: a predecessor that must not be mistaken for a dependency
        s.write(CTX, WriteItem(kind="fact", entity="delta", attribute="dependency", value="alpha",
                               text="delta runs on top of alpha.", relations=[Relation(rel="relates", target="alpha")]))
        yield s


def _owners(result):
    return {(i.entity, i.value) for i in result.items if i.attribute == "owner"}


@pytest.mark.parametrize("hint", [None, "alpha"])
@pytest.mark.parametrize("query", PLAIN_1HOP)
def test_one_hop_reaches_the_dependency_owner_with_any_wording(store, query, hint):
    assert ("beta", "team-blue") in _owners(store.retrieve(CTX, query, entity=hint, k=5, expand=True, graph_hops=2))


@pytest.mark.parametrize("hint", [None, "alpha"])
@pytest.mark.parametrize("query", PLAIN_2HOP)
def test_two_hop_reaches_the_second_dependency_owner(store, query, hint):
    assert ("gamma", "team-green") in _owners(store.retrieve(CTX, query, entity=hint, k=5, expand=True, graph_hops=2))


@pytest.mark.parametrize("hint", [None, "alpha"])
def test_plain_owner_question_still_returns_the_entitys_own_owner_first(store, hint):
    for query in ("Which team owns alpha?", "Who is the owner of alpha?"):
        first = store.retrieve(CTX, query, entity=hint, k=5, expand=True, graph_hops=2).items[0]
        assert (first.entity, first.value) == ("alpha", "team-red"), query


def test_relation_following_respects_tenant_and_contested_filters(store):
    other = Ctx(tenant_id="t2", writer_id="w", tier="human_verified", project="p")
    store.write(other, WriteItem(kind="fact", entity="beta", attribute="owner", value="team-foreign", text="beta is owned by team-foreign."))
    low = Ctx(tenant_id="t", writer_id="rumor", tier="untrusted", project="p")
    assert store.write(low, WriteItem(kind="fact", entity="beta", attribute="owner", value="team-evil",
                                      text="Heard that beta now belongs to team-evil.")).status == "contested"
    values = {v for _, v in _owners(store.retrieve(CTX, PLAIN_1HOP[0], k=8, expand=True, graph_hops=2))}
    assert "team-foreign" not in values and "team-evil" not in values
    opted = {v for _, v in _owners(store.retrieve(CTX, PLAIN_1HOP[0], k=8, expand=True, graph_hops=2, include_contested=True))}
    assert "team-evil" in opted


def test_unanchored_query_does_not_follow_relations(store):
    result = store.retrieve(CTX, "Which team owns the service?", k=5, expand=True, graph_hops=2)
    assert all(i.via != "expand" or i.entity in {"alpha", "beta", "gamma", "delta"} for i in result.items)
