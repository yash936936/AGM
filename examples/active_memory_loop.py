"""Provider-neutral active-memory turn-loop example (offline, no LLM call).

For a real provider, implement the same generate(user_message, context_pack)
callback and return ActiveTurnGeneration. The controller always retrieves first
and validates the post-turn memory decision against the actual input string.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from agm import Ctx, MemoryStore
from agm.active_memory import run_active_turn
from agm.models import ActiveTurnGeneration, MemoryDecision


def offline_generate(user_message, context):
    """Deterministic stand-in: exercise sequencing without pretending to answer with an LLM."""
    relevant_ids = [item.id for item in context.relevant_memories[:3]]
    summary = ", ".join(relevant_ids) if relevant_ids else "none"
    answer = (
        "[offline adapter: no language model was called] "
        f"Prepared memory context for this question; directly retrieved IDs: {summary}. "
        "Connect a model-provider callback to generate a natural-language answer."
    )
    return ActiveTurnGeneration(
        answer=answer,
        memory_decision=MemoryDecision(
            action="ignore",
            reason="Offline demonstration does not infer or write new user memories.",
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AGM's provider-neutral active memory loop.")
    parser.add_argument("--db", default=os.environ.get("AGM_DB_PATH", "./agm.db"))
    parser.add_argument("--tenant", default=os.environ.get("AGM_TENANT", "local-dev"))
    parser.add_argument("--project", default=os.environ.get("AGM_PROJECT", "default"))
    parser.add_argument("--writer", default=os.environ.get("AGM_WRITER", "active-memory-demo"))
    parser.add_argument("--query", required=True, help="The current user message.")
    parser.add_argument("--entity", default=None)
    parser.add_argument("--as-of", default=None)
    parser.add_argument("--k", type=int, default=8)
    parser.add_argument("--token-budget", type=int, default=2000)
    args = parser.parse_args()

    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    ctx = Ctx(
        tenant_id=args.tenant,
        writer_id=args.writer,
        tier="trusted_agent",
        project=args.project,
        agent="active-memory-demo",
    )
    with MemoryStore(args.db) as store:
        result = run_active_turn(
            store, ctx, args.query, offline_generate,
            entity=args.entity, as_of=args.as_of, k=args.k,
            token_budget=args.token_budget,
        )

    print("=== MEMORY CONTEXT (insert this before model generation) ===")
    print(result.context.context)
    print()
    print("=== ANSWER ===")
    print(result.answer)
    print()
    print("=== POST-TURN MEMORY POLICY ===")
    print(f"status={result.memory_action.status}")
    print(result.memory_action.message)
    print("Offline demo only; it made no LLM request.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
