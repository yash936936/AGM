import pytest

from agm import Ctx, MemoryStore, WriteItem
from agm.active_memory_policy import MemoryProposal
from agm.active_memory_turn import (
    begin_active_memory_turn, execute_authorized_memory_proposal,
    review_active_memory_proposals,
)


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


def test_execution_requires_authorization_scope_and_confirmation(store, ctx):
    proposal = MemoryProposal(action="write", evidence_quote="I prefer Python", entity="user", attribute="preference", value="Python")
    with pytest.raises(PermissionError, match="authorization"):
        execute_authorized_memory_proposal(store, ctx, proposal, current_user_message="I prefer Python", scopes=frozenset({"memory:write"}), confirmed=True)
    with pytest.raises(PermissionError, match="scope"):
        execute_authorized_memory_proposal(store, ctx, proposal, current_user_message="I prefer Python", scopes=frozenset({"memory:read"}), authorized=True, confirmed=True)
    with pytest.raises(PermissionError, match="confirmation"):
        execute_authorized_memory_proposal(store, ctx, proposal, current_user_message="I prefer Python", scopes=frozenset({"memory:write"}), authorized=True)
    assert store.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_authorized_write_correction_history_delete_survive_replay_and_reopen(tmp_path, ctx):
    db = str(tmp_path / "authorized-lifecycle.db")
    scopes = frozenset({"memory:write", "memory:read", "memory:delete"})
    original = MemoryProposal(action="write", evidence_quote="My editor is Vim", entity="user", attribute="editor", value="Vim")
    with MemoryStore(db) as store:
        written = execute_authorized_memory_proposal(store, ctx, original, current_user_message="My editor is Vim", scopes=scopes, authorized=True, confirmed=True)
        assert written.item_id
        correction = MemoryProposal(action="correct", evidence_quote="Actually, I use Neovim", entity="user", attribute="editor", value="Neovim", target_memory_id=written.item_id)
        corrected = execute_authorized_memory_proposal(store, ctx, correction, current_user_message="Actually, I use Neovim", scopes=scopes, authorized=True, confirmed=True)
        assert corrected.item_id
        history = execute_authorized_memory_proposal(store, ctx, MemoryProposal(action="history", entity="user", attribute="editor"), current_user_message="What did I tell you about my editor?", scopes=scopes, authorized=True)
        assert {node.value for node in history} >= {"Vim", "Neovim"}
        store.rebuild_views()
        result = store.retrieve(ctx, "user editor", entity="user")
        assert any(node.value == "Neovim" for node in result.items)
        assert not any(node.value == "Vim" for node in result.items)

    with MemoryStore(db) as reopened:
        reopened.rebuild_views()
        history = reopened.history(ctx, "user", "editor")
        assert {node.value for node in history} >= {"Vim", "Neovim"}
        delete_current = MemoryProposal(action="delete", entity="user", target_memory_id=corrected.item_id)
        deleted_current = execute_authorized_memory_proposal(reopened, ctx, delete_current, current_user_message="Please forget that memory", scopes=scopes, authorized=True, confirmed=True)
        assert deleted_current.deleted
        delete_original = MemoryProposal(action="delete", entity="user", target_memory_id=written.item_id)
        deleted_original = execute_authorized_memory_proposal(reopened, ctx, delete_original, current_user_message="Please forget that memory", scopes=scopes, authorized=True, confirmed=True)
        assert deleted_original.deleted
        reopened.rebuild_views()

    with MemoryStore(db) as final_store:
        final_store.rebuild_views()
        assert not final_store.retrieve(ctx, "user editor", entity="user").items
        payloads = " ".join(str(row[0]) for row in final_store.conn.execute("SELECT payload FROM events"))
        assert "Neovim" not in payloads
        assert "Vim" not in payloads


def test_authorized_lifecycle_is_tenant_and_project_scoped(tmp_path, ctx):
    db = str(tmp_path / "tenant-scope.db")
    scopes = frozenset({"memory:write", "memory:read", "memory:delete"})
    proposal = MemoryProposal(action="write", evidence_quote="My secret marker is TENANT-ALPHA", entity="user", attribute="marker", value="TENANT-ALPHA")
    with MemoryStore(db) as store:
        created = execute_authorized_memory_proposal(store, ctx, proposal, current_user_message="My secret marker is TENANT-ALPHA", scopes=scopes, authorized=True, confirmed=True)
        foreign_ctx = Ctx(tenant_id="other-tenant", writer_id="other-writer", tier="human_verified", project="turn-project")
        assert not store.retrieve(foreign_ctx, "TENANT-ALPHA", entity="user").items
        assert not store.history(foreign_ctx, "user", "marker")
        assert not store.delete(foreign_ctx, created.item_id).deleted
        store.rebuild_views()
        assert not store.retrieve(foreign_ctx, "TENANT-ALPHA", entity="user").items


def test_begin_turn_rejects_invalid_context_budget(store, ctx):
    with pytest.raises(ValueError, match="token_budget"):
        begin_active_memory_turn(store, ctx, "Question?", token_budget=0)
