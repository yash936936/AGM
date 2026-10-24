from agm import Ctx, MemoryStore, WriteItem
from agm.active_memory_policy import MemoryProposal
from agm.turn_loop import ModelTurnResponse, run_active_turn


def test_turn_loop_retrieves_before_model_and_only_evaluates_proposals(tmp_path):
    db_path = tmp_path / "turn.db"
    ctx = Ctx(tenant_id="t1", project="p1", writer_id="writer", tier="trusted_agent")
    with MemoryStore(str(db_path)) as store:
        store.write(ctx, WriteItem(text="The user's preferred answer style is concise.", kind="fact",
                                   entity="user", attribute="answer_style", value="concise"))
        seen = {}

        def model_call(message, memory_context):
            seen["message"] = message
            seen["context"] = memory_context
            return ModelTurnResponse(answer="I will keep the answer concise.", proposals=(
                MemoryProposal(action="write", evidence_quote="I prefer concise answers",
                               entity="user", attribute="answer_style", value="concise"),
            ))

        result = run_active_turn(store, ctx, "I prefer concise answers.", model_call,
                                 profile_queries=("user answer style",), token_budget=2000)
        assert seen["message"] == "I prefer concise answers."
        assert "untrusted data" in seen["context"].lower()
        assert result.answer == "I will keep the answer concise."
        assert len(result.decisions) == 1 and result.decisions[0].eligible
