"""Safe orchestration seam for active memory around an assistant turn.

The module deliberately separates retrieval and proposal review from mutation.
A host may use the returned context before a model call, review proposals after
the turn, and then execute explicitly authorized operations through existing
scoped MemoryStore/API methods. No LLM or automatic write is performed here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .active_memory import TurnMemoryContext, prepare_turn_context
from .active_memory_policy import MemoryProposal, PolicyDecision, evaluate_memory_proposal
from .models import Ctx
from .store import MemoryStore


@dataclass(frozen=True)
class ActiveMemoryTurn:
    """Read-only memory context prepared for one assistant turn."""

    context: TurnMemoryContext


@dataclass(frozen=True)
class ActiveMemoryReview:
    """Policy outcomes for proposals made during a turn; not mutation approval."""

    decisions: tuple[PolicyDecision, ...]

    @property
    def eligible_proposals(self) -> tuple[MemoryProposal, ...]:
        """Return proposals eligible for host review, not automatic execution."""
        return tuple(decision.proposal for decision in self.decisions if decision.eligible)

    @property
    def rejected_decisions(self) -> tuple[PolicyDecision, ...]:
        return tuple(decision for decision in self.decisions if not decision.eligible)


def begin_active_memory_turn(
    store: MemoryStore,
    ctx: Ctx,
    query: str,
    *,
    profile_queries: Sequence[str] = (),
    goal_queries: Sequence[str] = (),
    entity: str | None = None,
    as_of: str | None = None,
    k: int = 8,
    token_budget: int = 2000,
    expand: bool = True,
    high_stakes: bool = False,
) -> ActiveMemoryTurn:
    """Prepare pre-answer memory context without writing to the store."""
    return ActiveMemoryTurn(
        context=prepare_turn_context(
            store, ctx, query,
            profile_queries=profile_queries,
            goal_queries=goal_queries,
            entity=entity,
            as_of=as_of,
            k=k,
            token_budget=token_budget,
            expand=expand,
            high_stakes=high_stakes,
        )
    )


def review_active_memory_proposals(
    proposals: Sequence[MemoryProposal],
    *,
    current_user_message: str,
) -> ActiveMemoryReview:
    """Review proposals against the current user message without persistence.

    Eligibility is a policy signal only, not a grant of authority. This function
    cannot persist changes because it receives no MemoryStore.
    """
    return ActiveMemoryReview(
        decisions=tuple(
            evaluate_memory_proposal(proposal, current_user_message=current_user_message)
            for proposal in proposals
        )
    )
