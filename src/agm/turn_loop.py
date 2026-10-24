"""Host-independent active-memory turn controller.

The controller retrieves before the model call and evaluates proposed memory
operations after the response. It intentionally does not commit mutations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from .active_memory import TurnMemoryContext, prepare_turn_context
from .active_memory_policy import MemoryProposal, PolicyDecision, evaluate_memory_proposal
from .models import Ctx
from .store import MemoryStore


@dataclass(frozen=True)
class ModelTurnResponse:
    answer: str
    proposals: tuple[MemoryProposal, ...] = ()


@dataclass(frozen=True)
class ActiveTurnResult:
    context: TurnMemoryContext
    answer: str
    decisions: tuple[PolicyDecision, ...]


ModelCallback = Callable[[str, str], ModelTurnResponse]


def run_active_turn(
    store: MemoryStore,
    ctx: Ctx,
    user_message: str,
    model_call: ModelCallback,
    *,
    profile_queries: Sequence[str] = (),
    goal_queries: Sequence[str] = (),
    entity: str | None = None,
    as_of: str | None = None,
    k: int = 8,
    token_budget: int = 2000,
    expand: bool = True,
    high_stakes: bool = False,
) -> ActiveTurnResult:
    """Retrieve context, call the model, then evaluate candidate memory actions.

    The callback receives the user message and untrusted memory context. It
    returns an answer and optional proposed memory operations. Eligible
    decisions are recommendations only: a host must execute existing tools
    using the same authenticated tenant/project identity and explicit intent.
    """
    context = prepare_turn_context(
        store, ctx, user_message,
        profile_queries=profile_queries,
        goal_queries=goal_queries,
        entity=entity,
        as_of=as_of,
        k=k,
        token_budget=token_budget,
        expand=expand,
        high_stakes=high_stakes,
    )
    response = model_call(user_message, context.prompt_context)
    decisions = tuple(
        evaluate_memory_proposal(
            proposal, current_user_message=user_message,
        )
        for proposal in response.proposals
    )
    return ActiveTurnResult(
        context=context,
        answer=response.answer,
        decisions=decisions,
    )
