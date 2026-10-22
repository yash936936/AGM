"""Model-neutral task handoff helpers for Phase 4."""
from __future__ import annotations

import re
from typing import Iterable

from .models import Readback, ReadbackReport, TaskState

_TOKEN_RE = re.compile(r"[^\w]+", flags=re.UNICODE)


def _tokens(value: str) -> set[str]:
    return {token for token in _TOKEN_RE.split(value.casefold()) if token}


def _matches(expected: str, candidates: Iterable[str], *, threshold: float = 0.60) -> bool:
    expected_tokens = _tokens(expected)
    if not expected_tokens:
        return True
    normalized_expected = " ".join(expected.casefold().split())
    for candidate in candidates:
        normalized_candidate = " ".join(candidate.casefold().split())
        if not normalized_candidate:
            continue
        if normalized_expected in normalized_candidate:
            return True
        candidate_tokens = _tokens(candidate)
        if not candidate_tokens:
            continue
        overlap = len(expected_tokens & candidate_tokens)
        jaccard = overlap / len(expected_tokens | candidate_tokens)
        if jaccard >= threshold:
            return True
    return False


def compare_readback(task_state: TaskState, readback: Readback) -> ReadbackReport:
    """Report goal, decisions and open questions absent from a target-model readback."""
    mismatches: list[str] = []
    if not _matches(task_state.goal, [readback.goal]):
        mismatches.append("Goal does not match the saved task goal.")

    expected_decisions = [str(item.get("text", "")).strip() for item in task_state.decisions]
    for decision in (value for value in expected_decisions if value):
        if not _matches(decision, readback.decisions):
            mismatches.append(f"Missing decision in readback: {decision}")

    for question in task_state.open_questions:
        if not _matches(question, readback.open_items):
            mismatches.append(f"Missing open item in readback: {question}")

    return ReadbackReport(passed=not mismatches, mismatches=mismatches)
