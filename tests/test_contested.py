import pytest

from agm import Ctx, MemoryStore, WriteItem


@pytest.fixture
def store(tmp_path):
    instance = MemoryStore(str(tmp_path / "contested.db"))
    yield instance
    instance.close()


def test_stale_base_version_creates_contested_candidate_and_returns_both(store):
    tenant = "tenant-c"
    project = "ops"
    current_writer = Ctx(tenant_id=tenant, writer_id="writer-current", tier="human_verified", project=project)
    stale_writer = Ctx(tenant_id=tenant, writer_id="writer-stale", tier="trusted_agent", project=project)

    first = store.write(current_writer, WriteItem(
        kind="fact", entity="service-api", attribute="database", value="SQLite",
        text="service-api uses SQLite.",
    ))
    correction = store.write(current_writer, WriteItem(
        kind="fact", entity="service-api", attribute="database", value="PostgreSQL",
        text="service-api uses PostgreSQL.", base_version=1,
    ))
    assert correction.status == "superseded"

    stale = store.write(stale_writer, WriteItem(
        kind="fact", entity="service-api", attribute="database", value="MySQL",
        text="service-api uses MySQL.", base_version=1,
    ))
    assert stale.status == "contested"
    assert stale.item_id
    assert stale.contested_with == correction.item_id
    assert stale.warnings and "Stale base_version" in stale.warnings[0]

    current = store.conn.execute("SELECT status, value FROM nodes WHERE id = ?", (correction.item_id,)).fetchone()
    candidate = store.conn.execute("SELECT status, value FROM nodes WHERE id = ?", (stale.item_id,)).fetchone()
    assert tuple(current) == ("active", "PostgreSQL")
    assert tuple(candidate) == ("contested", "MySQL")
    edge = store.conn.execute(
        "SELECT COUNT(*) FROM edges WHERE src = ? AND dst = ? AND type = 'contests'",
        (stale.item_id, correction.item_id),
    ).fetchone()[0]
    assert edge == 1

    retrieved = store.retrieve(stale_writer, "service-api database", k=8, expand=True)
    result_ids = {item.id for item in retrieved.items}
    assert correction.item_id in result_ids
    assert stale.item_id in result_ids
    flagged = {item.id: item.contested_with for item in retrieved.items}
    assert flagged[correction.item_id] == stale.item_id
    assert flagged[stale.item_id] == correction.item_id


def test_matching_base_version_allows_normal_correction(store):
    ctx = Ctx(tenant_id="t", writer_id="w", tier="tool_verified", project="p")
    old = store.write(ctx, WriteItem(
        kind="fact", entity="worker", attribute="status", value="idle", text="worker is idle."
    ))
    new = store.write(ctx, WriteItem(
        kind="fact", entity="worker", attribute="status", value="busy", text="worker is busy.", base_version=1
    ))
    assert new.status == "superseded"
    assert new.superseded_id == old.item_id
    assert store.conn.execute("SELECT status FROM nodes WHERE id = ?", (old.item_id,)).fetchone()[0] == "superseded"


def test_contested_event_replays_with_edges_and_same_ids(store):
    ctx1 = Ctx(tenant_id="t", writer_id="a", tier="human_verified", project="p")
    ctx2 = Ctx(tenant_id="t", writer_id="b", tier="trusted_agent", project="p")
    old = store.write(ctx1, WriteItem(kind="fact", entity="worker", attribute="location", value="east", text="worker is east."))
    store.write(ctx1, WriteItem(kind="fact", entity="worker", attribute="location", value="west", text="worker is west.", base_version=1))
    contested = store.write(ctx2, WriteItem(kind="fact", entity="worker", attribute="location", value="north", text="worker is north.", base_version=1))
    before_nodes = [tuple(row) for row in store.conn.execute("SELECT * FROM nodes ORDER BY id")]
    before_edges = [tuple(row) for row in store.conn.execute("SELECT * FROM edges ORDER BY src, dst, type, event_id")]
    store.rebuild_views()
    after_nodes = [tuple(row) for row in store.conn.execute("SELECT * FROM nodes ORDER BY id")]
    after_edges = [tuple(row) for row in store.conn.execute("SELECT * FROM edges ORDER BY src, dst, type, event_id")]
    assert before_nodes == after_nodes
    assert before_edges == after_edges
    assert old.item_id is not None
    assert contested.item_id is not None


def test_large_trust_gap_keeps_higher_tier_fact_current(store):
    trusted = Ctx(tenant_id="t-gap", writer_id="human", tier="human_verified", project="p")
    untrusted = Ctx(tenant_id="t-gap", writer_id="external", tier="untrusted", project="p")
    current = store.write(trusted, WriteItem(
        kind="fact", entity="release", attribute="date", value="Friday", text="release date is Friday."
    ))
    candidate = store.write(untrusted, WriteItem(
        kind="fact", entity="release", attribute="date", value="Monday", text="release date is Monday."
    ))
    assert candidate.status == "contested"
    assert "Trust gap" in candidate.warnings[0]
    assert store.conn.execute("SELECT status FROM nodes WHERE id = ?", (current.item_id,)).fetchone()[0] == "active"
    assert store.conn.execute("SELECT status FROM nodes WHERE id = ?", (candidate.item_id,)).fetchone()[0] == "contested"


def test_contested_candidates_do_not_advance_accepted_chain_version(store):
    trusted = Ctx(tenant_id="t-version", writer_id="trusted", tier="human_verified", project="p")
    stale = Ctx(tenant_id="t-version", writer_id="stale", tier="trusted_agent", project="p")
    first = store.write(trusted, WriteItem(
        kind="fact", entity="api", attribute="database", value="SQLite", text="api uses SQLite."
    ))
    candidate = store.write(stale, WriteItem(
        kind="fact", entity="api", attribute="database", value="MySQL", text="api uses MySQL.", base_version=0
    ))
    assert candidate.status == "contested"
    assert store.conn.execute("SELECT version FROM nodes WHERE id = ?", (candidate.item_id,)).fetchone()[0] == 2

    accepted = store.write(trusted, WriteItem(
        kind="fact", entity="api", attribute="database", value="PostgreSQL", text="api uses PostgreSQL.", base_version=1
    ))
    assert accepted.status == "superseded"
    assert store.conn.execute("SELECT version FROM nodes WHERE id = ?", (accepted.item_id,)).fetchone()[0] == 2
    active = store.conn.execute(
        "SELECT version, value FROM nodes WHERE tenant = ? AND status = 'active'", (trusted.tenant_id,)
    ).fetchone()
    assert tuple(active) == (2, "PostgreSQL")
    assert first.item_id is not None
