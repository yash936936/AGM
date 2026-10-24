#!/usr/bin/env python3
"""Run the host-independent active-memory turn loop without calling an LLM."""
from __future__ import annotations
import argparse
from agm import Ctx, MemoryStore
from agm.turn_loop import ModelTurnResponse, run_active_turn


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="./agm.db")
    parser.add_argument("--tenant", default="local-dev")
    parser.add_argument("--project", default="default")
    parser.add_argument("--query", required=True)
    parser.add_argument("--profile-query", action="append", default=[])
    parser.add_argument("--goal-query", action="append", default=[])
    parser.add_argument("--token-budget", type=int, default=2000)
    parser.add_argument("--k", type=int, default=8)
    args = parser.parse_args()
    ctx = Ctx(tenant_id=args.tenant, project=args.project, writer_id="active-memory-demo",
              tier="trusted_agent", agent="active-memory-demo")

    def offline_model_call(user_message: str, memory_context: str) -> ModelTurnResponse:
        return ModelTurnResponse(answer=(
            f"Offline turn completed for: {user_message}\\n"
            "No LLM was called. The prepared memory context was supplied to the callback."
        ))

    with MemoryStore(args.db) as store:
        result = run_active_turn(store, ctx, args.query, offline_model_call,
                                 profile_queries=args.profile_query, goal_queries=args.goal_query,
                                 k=args.k, token_budget=args.token_budget)
        print(result.answer)
        print(f"Context items: {len(result.context.items)}")
        print(f"Context sections: {len(result.context.sections)}")
        print(f"Estimated tokens: {result.context.estimated_tokens}/{result.context.token_budget}")
        print(f"Conflict groups: {len(result.context.conflicts)}")
        print(f"Memory proposals: {len(result.decisions)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
