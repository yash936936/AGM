"""D-047: an entity hint scopes graph seeds; expansion may still reach linked entities."""
from __future__ import annotations

import pytest

from agm import Ctx, MemoryStore, Relation, WriteItem


@pytest.fixture()
def store(tmp_path):
    with MemoryStore(str(tmp_path / "hint.db")) as s:
        yield s


def _ctx(tenant="t", project="p", tier="human_verified", writer="w"):
    return Ctx(tenant_id=tenant, writer_id=writer, tier=tier, project=project)


def _seed(store, ctx):
    for e, owner in (("alpha", "team-red"), ("beta", "team-blue"), ("gamma", "team-green")):
        store.write(ctx, WriteItem(kind="fact", entity=e, attribute="owner", value=owner, text=f"{e} is owned by {owner}."))
    store.write(ctx, WriteItem(kind="fact", entity="alpha", attribute="dependency", value="beta",
                               text="alpha relies on beta to serve users.", relations=[Relation(rel="relates", target="beta")]))


Q = "Which team owns the service that alpha depends on?"


def test_hint_with_expansion_reaches_the_linked_entity(store):
    ctx = _ctx()
    _seed(store, ctx)
    hinted = store.retrieve(ctx, Q, entity="alpha", k=8, expand=True)
    pairs = {(i.entity, i.value, i.via) for i in hinted.items}
    assert ("beta", "team-blue", "expand") in pairs
    assert all(i.entity in {"alpha", "beta"} for i in hinted.items)  # unrelated gamma never appears
    unhinted = store.retrieve(ctx, Q, k=8, expand=True)
    assert any(i.entity == "beta" and i.value == "team-blue" for i in unhinted.items)


def test_hint_with_flat_retrieval_remains_a_hard_filter(store):
    ctx = _ctx()
    _seed(store, ctx)
    flat = store.retrieve(ctx, Q, entity="alpha", k=8, expand=False)
    assert {i.entity for i in flat.items} == {"alpha"}


def test_hint_does_not_cross_tenant_or_project_or_status_filters(store):
    ctx = _ctx()
    _seed(store, ctx)
    other_tenant, other_project = _ctx(tenant="t2"), _ctx(project="p2")
    for c in (other_tenant, other_project):
        store.write(c, WriteItem(kind="fact", entity="beta", attribute="owner", value="team-foreign",
                                 text="beta is owned by team-foreign."))
    values = {i.value for i in store.retrieve(ctx, Q, entity="alpha", k=8, expand=True).items}
    assert "team-foreign" not in values
    # a contested low-trust claim about the linked entity stays withheld by default (D-046) even through expansion
    low = _ctx(tier="untrusted", writer="rumor")
    r = store.write(low, WriteItem(kind="fact", entity="beta", attribute="owner", value="team-evil",
                                   text="Heard that beta now belongs to team-evil."))
    assert r.status == "contested"
    default = {i.value for i in store.retrieve(ctx, Q, entity="alpha", k=8, expand=True).items}
    assert "team-evil" not in default
    opted = {i.value for i in store.retrieve(ctx, Q, entity="alpha", k=8, expand=True, include_contested=True).items}
    assert "team-evil" in opted


def test_hint_unknown_entity_still_abstains(store):
    ctx = _ctx()
    _seed(store, ctx)
    result = store.retrieve(ctx, "Who owns delta?", entity="delta", k=8, expand=True)
    assert result.items == [] and result.abstain
