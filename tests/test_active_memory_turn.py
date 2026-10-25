import pytest

from agm import Ctx, MemoryStore, WriteItem
from agm.active_memory_policy import MemoryProposal
from agm.active_memory_turn import begin_active_memory_turn, review_active_memory_proposals


@pytest.fixture
def ctx():
    return Ctx(tenant_id="turn-tenant", writer_id="turn-writer", tier="human_verified", project="turn-project")


@pytest.fixture
def store(tmp_path):
    instance = MemoryStore(str(tmp_path / "active-turn.db"))
    yield instance
    instance.close()


def test_begin_turn_prepares_context_without_mutating_event_log(store, ctx):
    stored = store.write(ctx, WriteItem(kind="fact", entity="user", attribute="preference", value="Python", text="User prefers Python examples."))
    before = store.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    turn = begin_active_memory_turn(store, ctx, "Show a code example", profile_queries=("user preference Python",), token_budget=1000)

    after = store.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    assert stored.item_id in {item.id for item in turn.context.items}
    assert turn.context.estimated_tokens <= turn.context.token_budget
    assert "untrusted data" in turn.context.prompt_context.lower()
    assert after == before


def test_review_separates_eligible_proposals_from_rejected_ones():
    eligible = MemoryProposal(action="write", evidence_quote="I prefer Python", entity="user", attribute="preference", value="Python")
    rejected = MemoryProposal(action="delete", entity="old address")
    review = review_active_memory_proposals((eligible, rejected), current_user_message="I prefer Python. Please help me code.")

    assert review.eligible_proposals == (eligible,)
    assert len(review.rejected_decisions) == 1
    assert "explicit forget/delete" in review.rejected_decisions[0].reason
    assert all(not decision.eligible for decision in review.rejected_decisions)


def test_review_does_not_need_store_and_cannot_mutate_it():
    proposal = MemoryProposal(action="correct", evidence_quote="Actually, use Rust", entity="project", attribute="language", value="Rust")
    review = review_active_memory_proposals((proposal,), current_user_message="Actually, use Rust.")
    assert review.decisions[0].eligible
    assert "host confirmation" in review.decisions[0].reason


def test_begin_turn_rejects_invalid_context_budget(store, ctx):
    with pytest.raises(ValueError, match="token_budget"):
        begin_active_memory_turn(store, ctx, "Question?", token_budget=0)
