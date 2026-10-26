import pytest

from agm import Ctx, MemoryStore
from agm.active_memory_policy import MemoryProposal
from agm.reference_host import HostPrincipal, ReferenceHost


def _ctx(tenant, writer, project="default"):
    return Ctx(
        tenant_id=tenant,
        writer_id=writer,
        tier="human_verified",
        project=project,
    )


def test_reference_host_requires_resolved_identity_and_uses_host_scopes(tmp_path):
    with MemoryStore(str(tmp_path / "host-auth.db")) as store:
        principals = {
            "alice-session": HostPrincipal(
                "alice-session",
                _ctx("tenant-a", "alice", "project-a"),
                frozenset({"memory:write", "memory:read"}),
            )
        }
        host = ReferenceHost(
            store,
            resolve_principal=principals.get,
            verify_confirmation=lambda subject, proposal: True,
        )
        proposal = MemoryProposal(
            action="write",
            evidence_quote="I prefer Python",
            entity="user",
            attribute="language",
            value="Python",
        )
        result = host.handle_turn(
            authenticated_subject="alice-session",
            current_user_message="I prefer Python",
            proposal=proposal,
        )
        assert result.review.eligible_proposals == (proposal,)
        assert result.execution.item_id

        with pytest.raises(PermissionError, match="authenticated host principal"):
            host.handle_turn(
                authenticated_subject="forged-session",
                current_user_message="I prefer Rust",
                proposal=MemoryProposal(
                    action="write",
                    evidence_quote="I prefer Rust",
                    entity="user",
                    attribute="language",
                    value="Rust",
                ),
            )


def test_reference_host_mutation_waits_for_host_verified_confirmation(tmp_path):
    with MemoryStore(str(tmp_path / "host-confirm.db")) as store:
        principal = HostPrincipal(
            "alice-session",
            _ctx("tenant-a", "alice", "project-a"),
            frozenset({"memory:write"}),
        )
        host = ReferenceHost(
            store,
            resolve_principal=lambda subject: principal if subject == principal.subject else None,
            verify_confirmation=lambda subject, proposal: False,
        )
        proposal = MemoryProposal(
            action="write",
            evidence_quote="Remember that I prefer Python",
            entity="user",
            attribute="language",
            value="Python",
        )
        result = host.handle_turn(
            authenticated_subject="alice-session",
            current_user_message="Remember that I prefer Python",
            proposal=proposal,
        )
        assert result.awaiting_confirmation
        assert result.execution is None
        assert store.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_reference_host_never_uses_another_tenant_context(tmp_path):
    with MemoryStore(str(tmp_path / "host-isolation.db")) as store:
        principals = {
            "alice-session": HostPrincipal(
                "alice-session",
                _ctx("tenant-a", "alice", "project-a"),
                frozenset({"memory:write", "memory:read"}),
            ),
            "bob-session": HostPrincipal(
                "bob-session",
                _ctx("tenant-b", "bob", "project-b"),
                frozenset({"memory:write", "memory:read"}),
            ),
        }
        host = ReferenceHost(
            store,
            resolve_principal=principals.get,
            verify_confirmation=lambda subject, proposal: True,
        )
        proposal = MemoryProposal(
            action="write",
            evidence_quote="My private marker is ALPHA-ONLY",
            entity="user",
            attribute="marker",
            value="ALPHA-ONLY",
        )
        host.handle_turn(
            authenticated_subject="alice-session",
            current_user_message="My private marker is ALPHA-ONLY",
            proposal=proposal,
        )
        bob_turn = host.handle_turn(
            authenticated_subject="bob-session",
            current_user_message="What is my private marker?",
        )
        assert "ALPHA-ONLY" not in bob_turn.turn.context.prompt_context
        assert not bob_turn.turn.context.items


def test_reference_host_rejected_proposal_does_not_mutate(tmp_path):
    with MemoryStore(str(tmp_path / "host-reject.db")) as store:
        principal = HostPrincipal(
            "alice-session",
            _ctx("tenant-a", "alice"),
            frozenset({"memory:write"}),
        )
        host = ReferenceHost(
            store,
            resolve_principal=lambda subject: principal if subject == principal.subject else None,
            verify_confirmation=lambda subject, proposal: True,
        )
        proposal = MemoryProposal(
            action="write",
            evidence_quote="I prefer Python",
            entity="user",
            attribute="language",
            value="Python",
        )
        result = host.handle_turn(
            authenticated_subject="alice-session",
            current_user_message="Tell me a joke",
            proposal=proposal,
        )
        assert not result.review.eligible_proposals
        assert result.execution is None
        assert store.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_reference_host_correction_history_delete_and_rebuild(tmp_path):
    db = str(tmp_path / "host-lifecycle.db")
    principal = HostPrincipal(
        "alice-session",
        _ctx("tenant-a", "alice", "project-a"),
        frozenset({"memory:write", "memory:read", "memory:delete"}),
    )
    host = ReferenceHost(
        None,  # replaced below after the store is opened
        resolve_principal=lambda subject: principal if subject == principal.subject else None,
        verify_confirmation=lambda subject, proposal: True,
    )
    with MemoryStore(db) as store:
        host = ReferenceHost(
            store,
            resolve_principal=lambda subject: principal if subject == principal.subject else None,
            verify_confirmation=lambda subject, proposal: True,
        )
        written = host.handle_turn(
            authenticated_subject="alice-session",
            current_user_message="My editor is Vim",
            proposal=MemoryProposal(
                action="write", evidence_quote="My editor is Vim",
                entity="user", attribute="editor", value="Vim",
            ),
        )
        original_id = written.execution.item_id
        corrected = host.handle_turn(
            authenticated_subject="alice-session",
            current_user_message="Actually, I use Neovim",
            proposal=MemoryProposal(
                action="correct", evidence_quote="Actually, I use Neovim",
                entity="user", attribute="editor", value="Neovim",
                target_memory_id=original_id,
            ),
        )
        corrected_id = corrected.execution.item_id
        history = host.handle_turn(
            authenticated_subject="alice-session",
            current_user_message="What did I tell you about my editor?",
            proposal=MemoryProposal(action="history", entity="user", attribute="editor"),
        )
        assert {node.value for node in history.execution} >= {"Vim", "Neovim"}

        for memory_id in (corrected_id, original_id):
            deleted = host.handle_turn(
                authenticated_subject="alice-session",
                current_user_message="Please forget that memory",
                proposal=MemoryProposal(
                    action="delete", entity="user", target_memory_id=memory_id,
                ),
            )
            assert deleted.execution.deleted
        store.rebuild_views()
        assert not store.retrieve(principal.ctx, "user editor", entity="user").items
