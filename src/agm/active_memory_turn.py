"""Active-turn orchestration with explicit host authorization boundaries."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

from .active_memory import TurnMemoryContext, prepare_turn_context
from .active_memory_policy import MemoryProposal, PolicyDecision, evaluate_memory_proposal
from .models import Ctx, WriteItem
from .store import MemoryStore


@dataclass(frozen=True)
class ActiveMemoryTurn:
    context: TurnMemoryContext


@dataclass(frozen=True)
class ActiveMemoryReview:
    decisions: tuple[PolicyDecision, ...]

    @property
    def eligible_proposals(self) -> tuple[MemoryProposal, ...]:
        return tuple(d.proposal for d in self.decisions if d.eligible)

    @property
    def rejected_decisions(self) -> tuple[PolicyDecision, ...]:
        return tuple(d for d in self.decisions if not d.eligible)


def begin_active_memory_turn(store: MemoryStore, ctx: Ctx, query: str, *,
    profile_queries: Sequence[str] = (), goal_queries: Sequence[str] = (),
    entity: str | None = None, as_of: str | None = None, k: int = 8,
    token_budget: int = 2000, expand: bool = True, high_stakes: bool = False,
    include_contested: bool = False,
) -> ActiveMemoryTurn:
    """Prepare bounded, tenant-scoped context without writing."""
    return ActiveMemoryTurn(prepare_turn_context(
        store, ctx, query, profile_queries=profile_queries, goal_queries=goal_queries,
        entity=entity, as_of=as_of, k=k, token_budget=token_budget,
        expand=expand, high_stakes=high_stakes, include_contested=include_contested))


def review_active_memory_proposals(proposals: Sequence[MemoryProposal], *,
    current_user_message: str) -> ActiveMemoryReview:
    """Evaluate proposals only; eligibility is never mutation authorization."""
    return ActiveMemoryReview(tuple(
        evaluate_memory_proposal(p, current_user_message=current_user_message)
        for p in proposals))


def execute_authorized_memory_proposal(store: MemoryStore, ctx: Ctx,
    proposal: MemoryProposal, *, current_user_message: str,
    scopes: frozenset[str], authorized: bool = False, confirmed: bool = False):
    """Execute eligible proposals only after host authorization and confirmation."""
    decision = evaluate_memory_proposal(proposal, current_user_message=current_user_message)
    if not decision.eligible:
        raise ValueError(f"Proposal rejected: {decision.reason}")
    required = {"write": "memory:write", "correct": "memory:write",
                "history": "memory:read", "delete": "memory:delete"}.get(proposal.action)
    if required is None:
        raise ValueError("Unsupported memory action.")
    if "*" not in scopes and "admin" not in scopes and required not in scopes:
        raise PermissionError(f"Missing required scope: {required}")
    if not authorized:
        raise PermissionError("Host authorization is required.")
    if proposal.action != "history" and not confirmed:
        raise PermissionError("Explicit confirmation is required for mutations.")
    if proposal.action == "history":
        if not proposal.entity:
            raise ValueError("History requires an entity.")
        return store.history(ctx, proposal.entity, proposal.attribute)
    if proposal.action == "delete":
        if not proposal.target_memory_id:
            raise ValueError("Deletion requires an exact target memory ID.")
        return store.delete(ctx, proposal.target_memory_id)
    if not proposal.entity or not proposal.attribute or not proposal.value:
        raise ValueError("Entity, attribute, and value are required.")
    item = WriteItem(kind="fact", entity=proposal.entity, attribute=proposal.attribute,
                     value=proposal.value, text=proposal.evidence_quote)
    if proposal.action == "correct":
        if not proposal.target_memory_id:
            raise ValueError("Correction requires an exact target memory ID.")
        return store.supersede(ctx, proposal.target_memory_id, item,
                               "User correction in current turn")
    return store.write(ctx, item)
