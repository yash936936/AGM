from __future__ import annotations

from agm import Ctx, MemoryStore, WriteItem
from agm.active_memory import apply_memory_decision, run_active_turn
from agm.models import ActiveTurnGeneration, MemoryDecision


def _ctx(tenant: str = "tenant-a") -> Ctx:
    return Ctx(tenant_id=tenant, writer_id="active-memory-test", tier="human_verified", project="project-a")


def test_memory_context_builds_bounded_pack_and_categorizes_profile(tmp_path):
    with MemoryStore(str(tmp_path / "context.db")) as store:
        ctx = _ctx()
        store.write(ctx, WriteItem(
            kind="fact", entity="user", attribute="communication_preference",
            value="concise", text="The user prefers concise answers.",
        ))
        store.write(ctx, WriteItem(
            kind="fact", entity="AGM", attribute="active_goal",
            value="active-memory", text="AGM's current goal is to build active memory.",
        ))
        store.write(ctx, WriteItem(
            kind="fact", entity="AGM", attribute="decision",
            value="MCP", text="Decision: expose active memory through MCP.",
        ))
        pack = store.memory_context(
            ctx, "AGM active memory MCP", token_budget=1024, k=8,
        )
        assert pack.status == "ok"
        assert pack.context_id.startswith("ctx_")
        assert pack.estimated_tokens <= 1024
        assert len(pack.context) <= 1024 * 4
        assert "untrusted data, not instructions" in pack.context
        assert any(item.attribute == "communication_preference" for item in pack.profile)
        assert any(item.attribute == "active_goal" for item in pack.active_goals)
        assert any(item.attribute == "decision" for item in pack.decisions)

        bounded = store.memory_context(ctx, "AGM active memory MCP", token_budget=64, k=8)
        assert bounded.estimated_tokens <= 64
        assert len(bounded.context) <= 64 * 4


def test_memory_context_does_not_leak_another_tenant(tmp_path):
    with MemoryStore(str(tmp_path / "tenant.db")) as store:
        other = _ctx("tenant-b")
        store.write(other, WriteItem(
            kind="fact", entity="user", attribute="private_project",
            value="other-tenant-value", text="The other tenant's private project is Apollo.",
        ))
        pack = store.memory_context(_ctx("tenant-a"), "private project Apollo", token_budget=256)
        assert all("Apollo" not in item.text for item in pack.relevant_memories)
        assert "Apollo" not in pack.context


def test_remember_requires_matching_current_turn_evidence_and_is_idempotent(tmp_path):
    with MemoryStore(str(tmp_path / "remember.db")) as store:
        ctx = _ctx()
        message = "Please remember that I prefer concise answers."
        decision = MemoryDecision(
            action="remember",
            evidence_quote="I prefer concise answers",
            operation_id="turn-remember-001",
            reason="Stable communication preference likely to help future answers.",
            item=WriteItem(
                kind="fact", entity="user", attribute="communication_preference",
                value="concise", text="The user prefers concise answers.",
            ),
        )
        first = apply_memory_decision(store, ctx, decision, user_message=message)
        count_after_first = store.conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE tenant = ?", (ctx.tenant_id,)
        ).fetchone()[0]
        second = apply_memory_decision(store, ctx, decision, user_message=message)
        count_after_second = store.conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE tenant = ?", (ctx.tenant_id,)
        ).fetchone()[0]
        assert first.status == "stored"
        assert first.evidence_verified
        assert second.status in {"stored", "noop"}
        assert count_after_first == count_after_second == 1


def test_unmatched_evidence_does_not_write_anything(tmp_path):
    with MemoryStore(str(tmp_path / "evidence.db")) as store:
        result = apply_memory_decision(
            store, _ctx(),
            MemoryDecision(
                action="remember",
                evidence_quote="I prefer concise answers",
                item=WriteItem(
                    kind="fact", entity="user", attribute="communication_preference",
                    value="concise", text="The user prefers concise answers.",
                ),
            ),
            user_message="Can you summarize this document?",
        )
        assert result.status == "confirmation_required"
        assert store.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_correction_requires_explicit_correction_intent_and_preserves_history(tmp_path):
    with MemoryStore(str(tmp_path / "correct.db")) as store:
        ctx = _ctx()
        old = store.write(ctx, WriteItem(
            kind="fact", entity="AGM", attribute="database", value="SQLite",
            text="AGM uses SQLite.",
        ))
        decision = MemoryDecision(
            action="correct",
            target_item_id=old.item_id,
            evidence_quote="the project uses PostgreSQL instead",
            reason="User explicitly corrected the database choice.",
            item=WriteItem(
                kind="fact", entity="AGM", attribute="database", value="PostgreSQL",
                text="AGM uses PostgreSQL.",
            ),
        )
        blocked = apply_memory_decision(
            store, ctx, decision,
            user_message="The project uses PostgreSQL.",
        )
        assert blocked.status == "confirmation_required"
        changed = apply_memory_decision(
            store, ctx, decision,
            user_message="Actually, the project uses PostgreSQL instead.",
        )
        assert changed.status == "corrected"
        history = store.history(ctx, "AGM", "database")
        assert {item.value for item in history} == {"SQLite", "PostgreSQL"}


def test_forget_requires_explicit_request_and_matching_quote(tmp_path):
    with MemoryStore(str(tmp_path / "forget.db")) as store:
        ctx = _ctx()
        added = store.write(ctx, WriteItem(
            kind="fact", entity="user", attribute="communication_preference",
            value="concise", text="The user prefers concise answers.",
        ))
        blocked = apply_memory_decision(
            store, ctx,
            MemoryDecision(
                action="forget", target_item_id=added.item_id,
                evidence_quote="I prefer concise answers",
            ),
            user_message="I prefer concise answers.",
        )
        assert blocked.status == "confirmation_required"
        forgotten = apply_memory_decision(
            store, ctx,
            MemoryDecision(
                action="forget", target_item_id=added.item_id,
                evidence_quote="forget that I prefer concise answers",
            ),
            user_message="Please forget that I prefer concise answers.",
        )
        assert forgotten.status == "forgotten"
        assert store.conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE id = ?", (added.item_id,)
        ).fetchone()[0] == 0


def test_health_report_is_scoped_and_metadata_only(tmp_path):
    with MemoryStore(str(tmp_path / "health.db")) as store:
        ctx = _ctx()
        store.write(ctx, WriteItem(kind="episode", text="A test memory in tenant A."))
        store.write(_ctx("tenant-b"), WriteItem(kind="episode", text="A test memory in tenant B."))
        from agm.active_memory import memory_health

        report = memory_health(store, ctx)
        assert report.status == "ok"
        assert report.counts["active_items"] == 1
        assert report.counts["quarantined_items"] == 0
        assert all("test memory" not in str(value) for value in report.model_dump().values())


def test_active_turn_retrieves_before_generation_and_applies_post_turn_decision(tmp_path):
    with MemoryStore(str(tmp_path / "turn.db")) as store:
        ctx = _ctx()
        store.write(ctx, WriteItem(
            kind="fact", entity="AGM", attribute="database", value="SQLite",
            text="AGM uses SQLite.",
        ))
        observed = {}

        def generate(user_message, context):
            observed["query"] = context.query
            observed["context_id"] = context.context_id
            observed["has_memory"] = any(item.value == "SQLite" for item in context.relevant_memories)
            return ActiveTurnGeneration(
                answer="AGM uses SQLite, according to memory.",
                memory_decision=MemoryDecision(action="ignore", reason="No new durable fact."),
            )

        result = run_active_turn(store, ctx, "Which database does AGM use?", generate)
        assert observed["query"] == "Which database does AGM use?"
        assert observed["context_id"].startswith("ctx_")
        assert observed["has_memory"] is True
        assert result.answer == "AGM uses SQLite, according to memory."
        assert result.memory_action.status == "ignored"


def test_forget_removes_superseded_versions_and_survives_view_rebuild(tmp_path):
    with MemoryStore(str(tmp_path / "forget-history.db")) as store:
        ctx = _ctx()
        old = store.write(ctx, WriteItem(
            kind="fact", entity="AGM", attribute="database", value="SQLite",
            text="AGM uses SQLite.",
        ))
        new = store.write(ctx, WriteItem(
            kind="fact", entity="AGM", attribute="database", value="PostgreSQL",
            text="AGM uses PostgreSQL.",
        ))
        assert old.item_id and new.item_id
        forgotten = store.forget(ctx, new.item_id)
        assert forgotten["forgotten"] is True
        assert forgotten["deleted_count"] == 2
        store.rebuild_views()
        assert store.conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE id IN (?, ?)", (old.item_id, new.item_id)
        ).fetchone()[0] == 0
        assert store.history(ctx, "AGM", "database") == []


def test_correction_cannot_target_an_unrelated_fact(tmp_path):
    with MemoryStore(str(tmp_path / "wrong-correction-target.db")) as store:
        ctx = _ctx()
        old = store.write(ctx, WriteItem(
            kind="fact", entity="AGM", attribute="database", value="SQLite",
            text="AGM uses SQLite.",
        ))
        decision = MemoryDecision(
            action="correct", target_item_id=old.item_id,
            evidence_quote="Actually, the AGM theme is turquoise.",
            reason="Test wrong target protection",
            item=WriteItem(
                kind="fact", entity="AGM", attribute="theme", value="turquoise",
                text="AGM theme is turquoise.",
            ),
        )
        result = apply_memory_decision(
            store, ctx, decision,
            user_message="Actually, the AGM theme is turquoise.",
        )
        assert result.status == "confirmation_required"
        assert store.history(ctx, "AGM", "database")[0].value == "SQLite"


def test_forget_cannot_delete_unrelated_memory(tmp_path):
    with MemoryStore(str(tmp_path / "wrong-forget-target.db")) as store:
        ctx = _ctx()
        saved = store.write(ctx, WriteItem(
            kind="fact", entity="AGM", attribute="database", value="SQLite",
            text="AGM uses SQLite.",
        ))
        result = apply_memory_decision(
            store, ctx,
            MemoryDecision(
                action="forget", target_item_id=saved.item_id,
                evidence_quote="forget my turquoise color preference",
            ),
            user_message="Please forget my turquoise color preference.",
        )
        assert result.status == "confirmation_required"
        assert store.conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE id = ?", (saved.item_id,)
        ).fetchone()[0] == 1


def test_negated_forget_and_correction_requests_do_not_mutate(tmp_path):
    with MemoryStore(str(tmp_path / "negative-intent.db")) as store:
        ctx = _ctx()
        saved = store.write(ctx, WriteItem(
            kind="fact", entity="user", attribute="communication_preference",
            value="concise", text="The user prefers concise answers.",
        ))
        forget = apply_memory_decision(
            store, ctx,
            MemoryDecision(
                action="forget", target_item_id=saved.item_id,
                evidence_quote="delete my concise preference",
            ),
            user_message="I do not want you to delete my concise preference.",
        )
        correct = apply_memory_decision(
            store, ctx,
            MemoryDecision(
                action="correct", target_item_id=saved.item_id,
                evidence_quote="change the answer style",
                item=WriteItem(
                    kind="fact", entity="user", attribute="communication_preference",
                    value="detailed", text="The user prefers detailed answers.",
                ),
            ),
            user_message="I don't want you to change the answer style.",
        )
        stop_remembering = apply_memory_decision(
            store, ctx,
            MemoryDecision(
                action="forget", target_item_id=saved.item_id,
                evidence_quote="do not remember my concise preference",
            ),
            user_message="Please do not remember my concise preference.",
        )
        assert forget.status == "confirmation_required"
        assert correct.status == "confirmation_required"
        assert stop_remembering.status == "confirmation_required"
        assert store.conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE id = ?", (saved.item_id,)
        ).fetchone()[0] == 1


def test_remember_rejects_value_not_supported_by_evidence_quote(tmp_path):
    with MemoryStore(str(tmp_path / "unsupported-value.db")) as store:
        result = apply_memory_decision(
            store, _ctx(),
            MemoryDecision(
                action="remember",
                evidence_quote="I prefer concise answers",
                item=WriteItem(
                    kind="fact", entity="user", attribute="communication_preference",
                    value="detailed", text="The user prefers detailed answers.",
                ),
            ),
            user_message="Please remember that I prefer concise answers.",
        )
        assert result.status == "confirmation_required"
        assert store.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_repeated_correction_returns_same_result_without_duplicate_write(tmp_path):
    with MemoryStore(str(tmp_path / "correct-idempotent.db")) as store:
        ctx = _ctx()
        old = store.write(ctx, WriteItem(
            kind="fact", entity="AGM", attribute="database", value="SQLite",
            text="AGM uses SQLite.",
        ))
        decision = MemoryDecision(
            action="correct", target_item_id=old.item_id,
            evidence_quote="Actually, AGM uses PostgreSQL instead",
            operation_id="turn-correction-001",
            reason="User correction",
            item=WriteItem(
                kind="fact", entity="AGM", attribute="database", value="PostgreSQL",
                text="AGM uses PostgreSQL.",
            ),
        )
        first = apply_memory_decision(
            store, ctx, decision,
            user_message="Actually, AGM uses PostgreSQL instead.",
        )
        second = apply_memory_decision(
            store, ctx, decision,
            user_message="Actually, AGM uses PostgreSQL instead.",
        )
        assert first.status == second.status == "corrected"
        assert first.item_id == second.item_id
        history = store.history(ctx, "AGM", "database")
        assert [item.value for item in history] == ["SQLite", "PostgreSQL"]


def test_future_negation_does_not_trigger_forget_or_correction(tmp_path):
    with MemoryStore(str(tmp_path / "future-negative.db")) as store:
        ctx = _ctx()
        saved = store.write(ctx, WriteItem(
            kind="fact", entity="user", attribute="communication_preference",
            value="concise", text="The user prefers concise answers.",
        ))
        forget = apply_memory_decision(
            store, ctx,
            MemoryDecision(
                action="forget", target_item_id=saved.item_id,
                evidence_quote="I won't forget my concise preference",
            ),
            user_message="I won't forget my concise preference.",
        )
        correction = apply_memory_decision(
            store, ctx,
            MemoryDecision(
                action="correct", target_item_id=saved.item_id,
                evidence_quote="I won't change my concise preference",
                item=WriteItem(
                    kind="fact", entity="user", attribute="communication_preference",
                    value="detailed", text="The user prefers detailed answers.",
                ),
            ),
            user_message="I won't change my concise preference.",
        )
        assert forget.status == "confirmation_required"
        assert correction.status == "confirmation_required"
        assert store.conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE id = ?", (saved.item_id,)
        ).fetchone()[0] == 1


def test_context_pack_includes_both_sides_of_a_contested_fact(tmp_path):
    with MemoryStore(str(tmp_path / "context-conflict.db")) as store:
        accepted_ctx = Ctx(
            tenant_id="tenant-conflict", writer_id="trusted-owner",
            tier="human_verified", project="project-a",
        )
        stale_ctx = Ctx(
            tenant_id="tenant-conflict", writer_id="stale-agent",
            tier="trusted_agent", project="project-a",
        )
        first = store.write(accepted_ctx, WriteItem(
            kind="fact", entity="service-api", attribute="database", value="SQLite",
            text="service-api uses SQLite.",
        ))
        accepted = store.write(accepted_ctx, WriteItem(
            kind="fact", entity="service-api", attribute="database", value="PostgreSQL",
            text="service-api uses PostgreSQL.", base_version=1,
        ))
        contested = store.write(stale_ctx, WriteItem(
            kind="fact", entity="service-api", attribute="database", value="MySQL",
            text="service-api uses MySQL.", base_version=1,
        ))
        assert first.item_id and accepted.item_id and contested.item_id
        assert contested.status == "contested"
        pack = store.memory_context(
            accepted_ctx, "service-api database", entity="service-api",
            k=16, token_budget=1500,
        )
        assert "service-api uses PostgreSQL." in pack.context
        assert "service-api uses MySQL." in pack.context
        assert any(
            {entry.get("value"), entry.get("conflicting_value")} == {"PostgreSQL", "MySQL"}
            for entry in pack.conflicts
        )


def test_new_operation_can_reassert_previously_used_preference(tmp_path):
    with MemoryStore(str(tmp_path / "preference-recurrence.db")) as store:
        ctx = _ctx()
        initial = apply_memory_decision(
            store, ctx,
            MemoryDecision(
                action="remember", evidence_quote="I prefer concise answers",
                operation_id="turn-preference-1",
                item=WriteItem(
                    kind="fact", entity="user", attribute="communication_preference",
                    value="concise", text="The user prefers concise answers.",
                ),
            ),
            user_message="Please remember that I prefer concise answers.",
        )
        changed = apply_memory_decision(
            store, ctx,
            MemoryDecision(
                action="correct", target_item_id=initial.item_id,
                evidence_quote="Actually, I prefer detailed answers instead",
                operation_id="turn-preference-2",
                item=WriteItem(
                    kind="fact", entity="user", attribute="communication_preference",
                    value="detailed", text="The user prefers detailed answers.",
                ),
            ),
            user_message="Actually, I prefer detailed answers instead.",
        )
        restored = apply_memory_decision(
            store, ctx,
            MemoryDecision(
                action="remember", evidence_quote="I prefer concise answers",
                operation_id="turn-preference-3",
                item=WriteItem(
                    kind="fact", entity="user", attribute="communication_preference",
                    value="concise", text="The user prefers concise answers.",
                ),
            ),
            user_message="I prefer concise answers.",
        )
        assert changed.status == "corrected"
        assert restored.status == "stored"
        history = store.history(ctx, "user", "communication_preference")
        assert [item.value for item in history] == ["concise", "detailed", "concise"]


def test_retry_after_explicit_forget_does_not_restore_scrubbed_correction(tmp_path):
    with MemoryStore(str(tmp_path / "retry-after-forget.db")) as store:
        ctx = _ctx()
        old = store.write(ctx, WriteItem(
            kind="fact", entity="AGM", attribute="database", value="SQLite",
            text="AGM uses SQLite.",
        ))
        decision = MemoryDecision(
            action="correct", target_item_id=old.item_id,
            evidence_quote="Actually, AGM uses PostgreSQL instead",
            operation_id="turn-correction-to-forget",
            item=WriteItem(
                kind="fact", entity="AGM", attribute="database", value="PostgreSQL",
                text="AGM uses PostgreSQL.",
            ),
        )
        corrected = apply_memory_decision(
            store, ctx, decision,
            user_message="Actually, AGM uses PostgreSQL instead.",
        )
        assert corrected.status == "corrected"
        store.forget(ctx, corrected.item_id)
        retry = apply_memory_decision(
            store, ctx, decision,
            user_message="Actually, AGM uses PostgreSQL instead.",
        )
        assert retry.status == "not_found"
        assert store.history(ctx, "AGM", "database") == []


def test_host_operation_id_overrides_model_idempotency_values(tmp_path):
    with MemoryStore(str(tmp_path / "host-operation-id.db")) as store:
        ctx = _ctx()
        user_message = "Please remember that I prefer concise answers."

        def generate(message, context):
            return ActiveTurnGeneration(
                answer="Not an LLM call in this test.",
                memory_decision=MemoryDecision(
                    action="remember",
                    operation_id="model-claimed-operation",
                    evidence_quote="I prefer concise answers",
                    item=WriteItem(
                        kind="fact", entity="user", attribute="communication_preference",
                        value="concise", text="The user prefers concise answers.",
                        idempotency_key="model-proposed-key",
                    ),
                ),
            )

        first = run_active_turn(
            store, ctx, user_message, generate, operation_id="host-turn-001",
        )
        second = run_active_turn(
            store, ctx, user_message, generate, operation_id="host-turn-001",
        )
        event_keys = [
            row["idem_key"] for row in store.conn.execute(
                "SELECT idem_key FROM events WHERE tenant = ? AND type = 'add' ORDER BY id",
                (ctx.tenant_id,),
            ).fetchall()
        ]
        assert first.memory_action.status == "stored"
        assert second.memory_action.status in {"stored", "noop"}
        assert len(event_keys) == 1
        assert event_keys[0] not in {"model-proposed-key", "model-claimed-operation"}
        assert str(event_keys[0]).startswith("active-memory-v1:")


def test_active_turn_rejects_invalid_operation_id_before_generation(tmp_path):
    with MemoryStore(str(tmp_path / "invalid-operation-id.db")) as store:
        ctx = _ctx()
        called = {"value": False}

        def generate(message, context):
            called["value"] = True
            return ActiveTurnGeneration(
                answer="unreachable",
                memory_decision=MemoryDecision(action="ignore"),
            )

        import pytest

        with pytest.raises(ValueError, match="operation_id"):
            run_active_turn(
                store, ctx, "What should we remember?", generate,
                operation_id=" " * 201,
            )
        assert called["value"] is False
        assert store.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_high_stakes_context_does_not_expand_to_probationary_conflict(tmp_path):
    with MemoryStore(str(tmp_path / "context-high-stakes-conflict.db")) as store:
        accepted_ctx = Ctx(
            tenant_id="tenant-high-stakes", writer_id="trusted-owner",
            tier="human_verified", project="project-a",
        )
        stale_ctx = Ctx(
            tenant_id="tenant-high-stakes", writer_id="stale-agent",
            tier="trusted_agent", project="project-a",
        )
        accepted = store.write(accepted_ctx, WriteItem(
            kind="fact", entity="service-api", attribute="database", value="PostgreSQL",
            text="service-api uses PostgreSQL.",
        ))
        contested = store.write(stale_ctx, WriteItem(
            kind="fact", entity="service-api", attribute="database", value="MySQL",
            text="service-api uses MySQL.", base_version=0,
        ))
        assert accepted.item_id and contested.item_id and contested.status == "contested"
        pack = store.memory_context(
            accepted_ctx, "service-api database", entity="service-api",
            k=16, token_budget=1000, high_stakes=True,
        )
        assert "service-api uses PostgreSQL." in pack.context
        assert "service-api uses MySQL." not in pack.context


def test_context_text_includes_writer_and_source_span_provenance(tmp_path):
    from agm import SourceSpan

    with MemoryStore(str(tmp_path / "context-provenance.db")) as store:
        ctx = _ctx()
        episode = store.write(ctx, WriteItem(
            kind="episode", text="The user explicitly said they prefer concise answers.",
        ))
        assert episode.item_id
        store.write(ctx, WriteItem(
            kind="fact", entity="user", attribute="communication_preference",
            value="concise", text="The user prefers concise answers.",
            source_span=SourceSpan(episode_id=episode.item_id, start=4, end=42),
        ))
        pack = store.memory_context(
            ctx, "user prefers concise answers", entity="user", token_budget=1000,
        )
        assert "writer=active-memory-test" in pack.context
        assert f"source_episode={episode.item_id}" in pack.context
        assert "source_span=4:42" in pack.context


def test_context_string_discloses_primary_abstention(tmp_path):
    with MemoryStore(str(tmp_path / "context-abstention.db")) as store:
        pack = store.memory_context(
            _ctx(), "Find the owner of an absent service.", token_budget=256,
        )
        assert pack.abstain is True
        assert "Query retrieval abstained" in pack.context
        assert "Auxiliary memory alone is insufficient evidence." in pack.context
