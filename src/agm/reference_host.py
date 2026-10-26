"""Reference host wiring for AGM active-memory proposals.

This is an integration harness, not production authentication. A real host must
provide a resolver backed by its own authenticated session and a confirmation
verifier backed by its trusted UI/workflow state. Never accept Ctx or scopes
directly from an untrusted request.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .active_memory_policy import MemoryProposal
from .active_memory_turn import (
    ActiveMemoryReview,
    ActiveMemoryTurn,
    begin_active_memory_turn,
    execute_authorized_memory_proposal,
    review_active_memory_proposals,
)
from .models import Ctx
from .store import MemoryStore


@dataclass(frozen=True)
class HostPrincipal:
    """Trusted identity resolved by the host, never deserialized from a request."""

    subject: str
    ctx: Ctx
    scopes: frozenset[str]


@dataclass(frozen=True)
class HostTurnResult:
    turn: ActiveMemoryTurn
    review: ActiveMemoryReview
    execution: object | None = None
    awaiting_confirmation: bool = False


PrincipalResolver = Callable[[str], HostPrincipal | None]
ConfirmationVerifier = Callable[[str, MemoryProposal], bool]


class ReferenceHost:
    """Minimal before/review/authorize/execute orchestration for a real host to adapt."""

    def __init__(
        self,
        store: MemoryStore,
        *,
        resolve_principal: PrincipalResolver,
        verify_confirmation: ConfirmationVerifier,
    ) -> None:
        self._store = store
        self._resolve_principal = resolve_principal
        self._verify_confirmation = verify_confirmation

    def handle_turn(
        self,
        *,
        authenticated_subject: str,
        current_user_message: str,
        proposal: MemoryProposal | None = None,
    ) -> HostTurnResult:
        """Handle one turn using host-resolved identity and host-verified confirmation.

        The subject is an opaque handle from the host's authenticated session, not
        a user ID or scope supplied by the client. The resolver returns the trusted
        Ctx and scopes. Mutations are not executed until the confirmation verifier
        confirms this exact proposal for this subject.
        """
        principal = self._resolve_principal(authenticated_subject)
        if principal is None or principal.subject != authenticated_subject:
            raise PermissionError("No authenticated host principal for this session.")

        turn = begin_active_memory_turn(
            self._store, principal.ctx, current_user_message
        )
        if proposal is None:
            return HostTurnResult(
                turn=turn,
                review=ActiveMemoryReview(()),
            )

        review = review_active_memory_proposals(
            (proposal,), current_user_message=current_user_message
        )
        if not review.eligible_proposals:
            return HostTurnResult(turn=turn, review=review)

        is_mutation = proposal.action != "history"
        confirmed = (
            not is_mutation
            or self._verify_confirmation(authenticated_subject, proposal)
        )
        if is_mutation and not confirmed:
            return HostTurnResult(
                turn=turn, review=review, awaiting_confirmation=True
            )

        execution = execute_authorized_memory_proposal(
            self._store,
            principal.ctx,
            proposal,
            current_user_message=current_user_message,
            scopes=principal.scopes,
            authorized=True,
            confirmed=confirmed,
        )
        return HostTurnResult(turn=turn, review=review, execution=execution)
