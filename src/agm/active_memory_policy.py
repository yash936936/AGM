"""Conservative policy for model-proposed active-memory operations.

This module only evaluates proposals. It never mutates MemoryStore. A host must
explicitly execute approved actions through the existing authenticated tools.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MemoryAction = Literal["write", "correct", "history", "delete"]


@dataclass(frozen=True)
class MemoryProposal:
    action: MemoryAction
    evidence_quote: str = ""
    entity: str | None = None
    attribute: str | None = None
    value: str | None = None
    target_memory_id: str | None = None
    reason: str = ""


@dataclass(frozen=True)
class PolicyDecision:
    proposal: MemoryProposal
    eligible: bool
    reason: str


_CORRECTION_MARKERS = (
    "actually", "correction", "i meant", "that's wrong", "that is wrong",
    "instead", "no longer", "changed to", "update that",
)
_FORGET_MARKERS = (
    "forget", "delete that memory", "remove that memory", "don't remember",
    "do not remember", "erase that",
)
_HISTORY_MARKERS = (
    "what did i say", "what did i tell you", "what do you remember", "memory history",
    "previously told you", "what changed", "history of",
)


def evaluate_memory_proposal(
    proposal: MemoryProposal,
    *,
    current_user_message: str,
) -> PolicyDecision:
    """Evaluate a proposed operation against the actual user message."""
    message = current_user_message.strip()
    folded = message.casefold()
    quote = proposal.evidence_quote.strip()

    if not message:
        return PolicyDecision(proposal, False, "Current user message is empty.")

    if proposal.action in ("write", "correct"):
        if not quote or quote not in message:
            return PolicyDecision(proposal, False, "Evidence quote must occur verbatim in the current user message.")
        if not proposal.entity or not proposal.attribute or not proposal.value:
            return PolicyDecision(proposal, False, "Entity, attribute, and value are required.")
        if proposal.action == "correct" and not any(marker in folded for marker in _CORRECTION_MARKERS):
            return PolicyDecision(proposal, False, "Correction requires explicit correction language in the user message.")
        if proposal.action == "correct" and not proposal.target_memory_id:
            return PolicyDecision(proposal, False, "Correction requires an exact target memory ID.")
        return PolicyDecision(
            proposal, True,
            "Evidence is grounded in the current user message; host confirmation and scoped tool authorization are still required.",
        )

    if proposal.action == "history":
        if not any(marker in folded for marker in _HISTORY_MARKERS):
            return PolicyDecision(proposal, False, "History access requires an explicit recall/history request.")
        if not proposal.entity:
            return PolicyDecision(proposal, False, "History requires a specific entity.")
        return PolicyDecision(proposal, True, "User explicitly requested recall/history; use the authenticated history/retrieval tool.")

    if proposal.action == "delete":
        if not any(marker in folded for marker in _FORGET_MARKERS):
            return PolicyDecision(proposal, False, "Deletion requires an explicit forget/delete request.")
        if not proposal.target_memory_id:
            return PolicyDecision(proposal, False, "Deletion requires an exact target memory ID.")
        return PolicyDecision(proposal, True, "Explicit forgetting request detected; confirm the exact target and use the scoped deletion tool.")

    return PolicyDecision(proposal, False, "Unsupported memory action.")
