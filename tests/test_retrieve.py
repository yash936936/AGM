import pytest

from agm import Ctx, MemoryStore, Relation, WriteItem


@pytest.fixture
def ctx():
    return Ctx(tenant_id="tenant-r", writer_id="writer-a", tier="human_verified", project="research")


@pytest.fixture
def store(tmp_path):
    instance = MemoryStore(str(tmp_path / "retrieve.db"))
    yield instance
    instance.close()


def test_expand_false_matches_phase1_flat_baseline(store, ctx):
    store.write(ctx, WriteItem(
        kind="fact", entity="Ada Lovelace", attribute="field", value="mathematics",
        text="Ada Lovelace worked in mathematics.",
    ))
    store.write(ctx, WriteItem(kind="episode", text="The Analytical Engine used punched cards."))
    baseline = store._retrieve_flat(ctx, "Ada mathematics", k=5, _track_usage=False)
    result = store.retrieve(ctx, "Ada mathematics", k=5, expand=False)
    assert result == baseline
    assert result.route.expand_used is False
    assert result.route.expanded_n == 0


def test_graph_expansion_returns_related_entity_fact(store, ctx):
    store.write(ctx, WriteItem(
        kind="fact", entity="Ada Lovelace", attribute="project", value="Analytical Engine",
        text="Ada Lovelace researched a project called the Analytical Engine.",
        relations=[Relation(rel="relates", target="Analytical Engine")],
    ))
    related = store.write(ctx, WriteItem(
        kind="fact", entity="Analytical Engine", attribute="designer", value="Charles Babbage",
        text="The machine designer was Charles Babbage.",
    ))
    flat = store.retrieve(ctx, "Ada Lovelace biography", k=8, expand=False)
    graph = store.retrieve(ctx, "Ada Lovelace biography", k=8, expand=True)

    assert any(item.id == related.item_id for item in graph.items)
    assert not any(item.id == related.item_id for item in flat.items if item.via == "expand")
    assert graph.route.expand_used is True
    assert graph.route.seed_n >= 1
    assert graph.route.expanded_n >= 1
    assert any(item.id == related.item_id and item.via == "expand" for item in graph.items)


def test_unanswerable_query_abstains_after_one_widening(store, ctx):
    store.write(ctx, WriteItem(
        kind="fact", entity="Ada Lovelace", attribute="field", value="mathematics",
        text="Ada Lovelace worked in mathematics.",
    ))
    result = store.retrieve(ctx, "zzqxxv hypermorphism unspeakable", k=5, expand=True)
    assert result.abstain is True
    assert result.items == []
    assert result.abstain_reason
    assert result.route.widened is True
    assert result.route.expand_used is True


def test_entity_alias_resolves_for_filter_and_history(store, ctx):
    write = store.write(ctx, WriteItem(
        kind="fact", entity="Ada Lovelace", attribute="occupation", value="mathematician",
        text="Ada Lovelace was a mathematician.",
        relations=[Relation(rel="alias", target="Lady Lovelace")],
    ))
    retrieved = store.retrieve(ctx, "occupation mathematician", entity="Lady Lovelace", expand=False)
    history = store.history(ctx, "Lady Lovelace", attribute="occupation")
    assert [item.id for item in retrieved.items] == [write.item_id]
    assert [item.id for item in history] == [write.item_id]


def test_as_of_filter_applies_to_graph_expansion(store, ctx):
    old = store.write(ctx, WriteItem(
        kind="fact", entity="Ada", attribute="location", value="London",
        text="Ada lived in London.", valid_from="2020-01-01T00:00:00Z",
    ))
    new = store.write(ctx, WriteItem(
        kind="fact", entity="Ada", attribute="location", value="Paris",
        text="Ada lived in Paris.", valid_from="2022-01-01T00:00:00Z",
    ))
    result = store.retrieve(ctx, "Ada location", entity="Ada", as_of="2021-01-01T00:00:00Z", expand=True)
    assert [item.id for item in result.items] == [old.item_id]
    assert all(item.id != new.item_id for item in result.items)


def test_independent_writer_corroboration_raises_effective_confidence(store):
    from agm.trust import effective_confidence

    source = Ctx(tenant_id="tenant-confidence", writer_id="writer-source", tier="trusted_agent", project="p")
    independent = Ctx(tenant_id="tenant-confidence", writer_id="writer-reviewer", tier="tool_verified", project="p")
    result = store.write(source, WriteItem(
        kind="fact", entity="build", attribute="result", value="passing",
        text="build result is passing.", confidence=0.8,
    ))
    row = store.conn.execute("SELECT * FROM nodes WHERE id = ?", (result.item_id,)).fetchone()
    before = effective_confidence(store.conn, row)

    confirmation = store.write(independent, WriteItem(
        kind="fact", entity="build", attribute="result", value="passing",
        text="build result is passing.", confidence=0.9,
    ))
    after = effective_confidence(store.conn, row)
    store.write(independent, WriteItem(
        kind="fact", entity="build", attribute="result", value="passing",
        text="build result is passing.", confidence=0.9,
    ))
    after_repeat = effective_confidence(store.conn, row)

    assert confirmation.status == "noop"
    assert confirmation.item_id == result.item_id
    assert after > before
    assert after_repeat == pytest.approx(after, abs=1e-9)
    assert store.conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0] == 1
    assert store.conn.execute("SELECT COUNT(*) FROM events WHERE type = 'corroborate'").fetchone()[0] == 2


def test_write_through_unique_alias_updates_canonical_entity(store, ctx):
    first = store.write(ctx, WriteItem(
        kind="fact", entity="Ada Lovelace", attribute="location", value="London",
        text="Ada Lovelace lived in London.",
        relations=[Relation(rel="alias", target="Lady Lovelace")],
    ))
    corrected = store.write(ctx, WriteItem(
        kind="fact", entity="Lady Lovelace", attribute="location", value="Paris",
        text="Lady Lovelace lived in Paris.", valid_from="2024-01-01T00:00:00Z",
    ))

    assert corrected.status == "superseded"
    assert corrected.superseded_id == first.item_id
    assert store.conn.execute("SELECT COUNT(*) FROM entities WHERE tenant = ?", (ctx.tenant_id,)).fetchone()[0] == 1
    current = store.retrieve(ctx, "Lady Lovelace location", entity="Ada Lovelace", expand=False)
    assert [node.id for node in current.items] == [corrected.item_id]
    assert current.items[0].entity == "ada lovelace"


def test_alias_added_later_updates_fts_for_existing_entity_nodes(store, ctx):
    first = store.write(ctx, WriteItem(
        kind="fact", entity="Ada Lovelace", attribute="field", value="mathematics",
        text="Ada Lovelace worked in mathematics.", multi_valued=True,
    ))
    store.write(ctx, WriteItem(
        kind="fact", entity="Ada Lovelace", attribute="known_for", value="computing",
        text="Ada Lovelace contributed to computing.", multi_valued=True,
        relations=[Relation(rel="alias", target="Lady Lovelace")],
    ))
    indexed = store.conn.execute(
        "SELECT entity FROM nodes_fts WHERE node_id = ?", (first.item_id,)
    ).fetchone()["entity"]
    assert "lady lovelace" in indexed
    retrieved = store.retrieve(ctx, '"Lady Lovelace" mathematics', entity="Lady Lovelace", expand=False)
    assert any(node.id == first.item_id for node in retrieved.items)


def test_ambiguous_alias_refuses_write_instead_of_merging_entities(store):
    a = Ctx(tenant_id="amb", writer_id="a", tier="human_verified", project="p")
    b = Ctx(tenant_id="amb", writer_id="b", tier="human_verified", project="p")
    store.write(a, WriteItem(
        kind="fact", entity="Person A", attribute="role", value="researcher", text="Person A is a researcher.",
        relations=[Relation(rel="alias", target="Alex")],
    ))
    store.write(b, WriteItem(
        kind="fact", entity="Person B", attribute="role", value="designer", text="Person B is a designer.",
        relations=[Relation(rel="alias", target="Alex")],
    ))

    before = store.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    with pytest.raises(ValueError, match="resolves to multiple entities"):
        store.write(a, WriteItem(
            kind="fact", entity="Alex", attribute="status", value="busy", text="Alex is busy."
        ))
    assert store.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == before


def test_graph_expansion_supports_two_hops_but_caps_at_two(store, ctx):
    from agm.retrieve import graph_retrieve

    store.write(ctx, WriteItem(
        kind="fact", entity="Ada Lovelace", attribute="project", value="Analytical Engine",
        text="Ada Lovelace researched the Analytical Engine.", multi_valued=True,
        relations=[Relation(rel="relates", target="Analytical Engine")],
    ))
    store.write(ctx, WriteItem(
        kind="fact", entity="Analytical Engine", attribute="designer", value="Charles Babbage",
        text="The Analytical Engine was designed by Charles Babbage.", multi_valued=True,
        relations=[Relation(rel="relates", target="Charles Babbage")],
    ))
    babbage = store.write(ctx, WriteItem(
        kind="fact", entity="Charles Babbage", attribute="field", value="computing",
        text="Charles Babbage worked in computing.", multi_valued=True,
    ))

    one_hop = graph_retrieve(store, ctx, "Ada Lovelace biography", k=8, _hops=1)
    two_hops = graph_retrieve(store, ctx, "Ada Lovelace biography", k=8, _hops=2)
    assert not any(node.id == babbage.item_id and node.via == "expand" for node in one_hop.items)
    assert any(node.id == babbage.item_id and node.via == "expand" for node in two_hops.items)

    with pytest.raises(ValueError, match="between 1 and 2"):
        graph_retrieve(store, ctx, "Ada Lovelace biography", k=8, _hops=3)


def test_graph_hop_intent_finds_the_exact_downstream_owner(store, ctx):
    store.write(ctx, WriteItem(
        kind="fact", entity="svc-a", attribute="owner", value="team-a",
        text="svc-a owner is team-a",
    ))
    store.write(ctx, WriteItem(
        kind="fact", entity="svc-b", attribute="owner", value="team-b",
        text="svc-b owner is team-b",
    ))
    store.write(ctx, WriteItem(
        kind="fact", entity="svc-c", attribute="owner", value="team-c",
        text="svc-c owner is team-c",
    ))
    store.write(ctx, WriteItem(
        kind="fact", entity="svc-a", attribute="dependency", value="svc-b",
        text="svc-a dependency is svc-b",
        relations=[Relation(rel="relates", target="svc-b")],
    ))
    store.write(ctx, WriteItem(
        kind="fact", entity="svc-b", attribute="dependency", value="svc-c",
        text="svc-b dependency is svc-c",
        relations=[Relation(rel="relates", target="svc-c")],
    ))

    one_hop = store.retrieve(
        ctx, "Who owns the service exactly 1 dependency hop downstream of svc-a?",
        k=8, expand=True, graph_hops=2,
    )
    two_hops = store.retrieve(
        ctx, "Who owns the service exactly 2 dependency hops downstream of svc-a?",
        k=8, expand=True, graph_hops=2,
    )
    assert any(item.attribute == "owner" and item.value == "team-b" for item in one_hop.items)
    assert any(item.attribute == "owner" and item.value == "team-c" for item in two_hops.items)


def test_graph_does_not_follow_superseded_dependency_edges(store, ctx):
    store.write(ctx, WriteItem(
        kind="fact", entity="svc-old", attribute="owner", value="old-team",
        text="svc-old owner is old-team",
    ))
    store.write(ctx, WriteItem(
        kind="fact", entity="svc-current", attribute="owner", value="current-team",
        text="svc-current owner is current-team",
    ))
    first = store.write(ctx, WriteItem(
        kind="fact", entity="svc-root", attribute="dependency", value="svc-old",
        text="svc-root dependency is svc-old",
        relations=[Relation(rel="relates", target="svc-old")],
    ))
    corrected = store.write(ctx, WriteItem(
        kind="fact", entity="svc-root", attribute="dependency", value="svc-current",
        text="svc-root dependency is svc-current",
        relations=[Relation(rel="relates", target="svc-current")],
    ))
    assert corrected.status == "superseded"
    assert first.item_id != corrected.item_id

    result = store.retrieve(
        ctx, "Who owns the service exactly 1 dependency hop downstream of svc-root?",
        k=8, expand=True, graph_hops=1,
    )
    assert any(item.attribute == "owner" and item.value == "current-team" for item in result.items)
    assert not any(item.attribute == "owner" and item.value == "old-team" for item in result.items)


def test_unresolved_catalogued_numeric_entity_id_abstains_in_flat_and_graph(store, ctx):
    store.write(ctx, WriteItem(
        kind="fact", entity="svc-12", attribute="owner", value="team-12",
        text="svc-12 owner is team-12",
    ))
    query = "What runtime and owner are configured for svc-012?"
    for expand in (False, True):
        result = store.retrieve(ctx, query, k=8, expand=expand)
        assert result.abstain is True
        assert result.items == []
        assert "identifier" in (result.abstain_reason or "")

    exact = store.retrieve(ctx, "Who owns svc-12?", k=8, expand=False)
    assert exact.abstain is False
    assert any(item.value == "team-12" for item in exact.items)


def test_batch_corroboration_counts_match_single_row_helper(store, ctx):
    from agm.retrieve import _batch_independent_corroborations
    from agm.trust import independent_corroborations

    second_writer = Ctx(
        tenant_id=ctx.tenant_id, writer_id="writer-independent",
        tier="tool_verified", project=ctx.project,
    )
    store.write(ctx, WriteItem(
        kind="fact", entity="build", attribute="result", value="passing",
        text="build result is passing",
    ))
    store.write(second_writer, WriteItem(
        kind="fact", entity="build", attribute="result", value="passing",
        text="build result is passing",
    ))
    rows = store.conn.execute(
        "SELECT * FROM nodes WHERE tenant = ? AND project = ?",
        (ctx.tenant_id, ctx.project),
    ).fetchall()
    batch = _batch_independent_corroborations(store.conn, rows)
    assert batch == {
        str(row["id"]): independent_corroborations(store.conn, row)
        for row in rows
    }
