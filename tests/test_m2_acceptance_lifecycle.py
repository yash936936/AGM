from __future__ import annotations

from agm import Ctx, MemoryStore, WriteItem
from agm.active_memory import prepare_turn_context
from agm.active_memory_policy import MemoryProposal
from agm.active_memory_turn import execute_authorized_memory_proposal


def test_context_preparation_is_project_scoped_as_well_as_tenant_scoped(tmp_path):
    db = tmp_path / "project-scope.db"
    local = Ctx(tenant_id="shared-tenant", writer_id="local-writer", tier="human_verified", project="project-a")
    foreign = Ctx(tenant_id="shared-tenant", writer_id="foreign-writer", tier="human_verified", project="project-b")
    with MemoryStore(str(db)) as store:
        local_item = store.write(local, WriteItem(
            kind="fact", entity="user", attribute="preference", value="local-marker",
            text="Project A preference local-marker.",
        ))
        foreign_item = store.write(foreign, WriteItem(
            kind="fact", entity="user", attribute="preference", value="foreign-marker",
            text="Project B preference foreign-marker.",
        ))
        prepared = prepare_turn_context(
            store, local, "preference", profile_queries=("user preference",), token_budget=1000,
        )
        returned_ids = {item.id for item in prepared.items}
        assert local_item.item_id in returned_ids
        assert foreign_item.item_id not in returned_ids
        assert all(item.project == "project-a" for item in prepared.items)


def test_m2_correction_and_delete_execution_survive_rebuild_and_reopen(tmp_path):
    db = tmp_path / "m2-lifecycle.db"
    ctx = Ctx(tenant_id="m2-tenant", writer_id="m2-writer", tier="human_verified", project="m2-project")
    old_marker = "M2-OLD-VALUE-71"
    current_marker = "M2-CURRENT-VALUE-82"
    with MemoryStore(str(db)) as store:
        old = store.write(ctx, WriteItem(
            kind="fact", entity="M2 Test User", attribute="editor", value=old_marker,
            text=f"My editor is {old_marker}.",
        ))
        correction_message = f"Actually, my editor is {current_marker}."
        correction = MemoryProposal(
            action="correct", evidence_quote=correction_message, entity="M2 Test User",
            attribute="editor", value=current_marker, target_memory_id=old.item_id,
        )
        result = execute_authorized_memory_proposal(
            store, ctx, correction, current_user_message=correction_message,
            scopes=frozenset({"memory:write"}), authorized=True, confirmed=True,
        )
        assert result.item_id
        store.rebuild_views()
        current = store.retrieve(ctx, "M2 Test User editor", entity="M2 Test User")
        assert any(item.id == result.item_id and item.value == current_marker for item in current.items)
        history = store.history(ctx, "M2 Test User", "editor")
        assert {item.id for item in history} >= {old.item_id, result.item_id}

        delete_message = "Please forget that memory."
        deletion = MemoryProposal(
            action="delete", entity="M2 Test User", target_memory_id=result.item_id,
        )
        deleted = execute_authorized_memory_proposal(
            store, ctx, deletion, current_user_message=delete_message,
            scopes=frozenset({"memory:delete"}), authorized=True, confirmed=True,
        )
        assert deleted.deleted
        store.rebuild_views()

    with MemoryStore(str(db)) as reopened:
        reopened.rebuild_views()
        current = reopened.retrieve(ctx, "M2 Test User editor", entity="M2 Test User")
        assert all(item.id != result.item_id for item in current.items)
        payloads = " ".join(str(row[0]) for row in reopened.conn.execute("SELECT payload FROM events"))
        assert current_marker not in payloads
        assert old_marker in payloads
