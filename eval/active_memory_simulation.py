"""Deterministic multi-turn active-memory policy simulation.

This harness is not a model benchmark. Run with:
python eval/active_memory_simulation.py
"""
from __future__ import annotations

from agm.active_memory_policy import MemoryProposal, evaluate_memory_proposal


SCENARIOS = (
    ("explicit preference", "I prefer concise answers.", MemoryProposal(
        action="write", evidence_quote="I prefer concise answers",
        entity="user", attribute="answer_style", value="concise",
    ), True),
    ("unsupported model inference", "What should I eat?", MemoryProposal(
        action="write", evidence_quote="I love spicy food",
        entity="user", attribute="food_preference", value="spicy",
    ), False),
    ("explicit correction", "Actually, I work in Jaipur now.", MemoryProposal(
        action="correct", evidence_quote="I work in Jaipur now",
        entity="user", attribute="city", value="Jaipur",
    ), True),
    ("implicit correction rejected", "I work in Jaipur now.", MemoryProposal(
        action="correct", evidence_quote="I work in Jaipur now",
        entity="user", attribute="city", value="Jaipur",
    ), False),
    ("explicit forgetting", "Forget my old address.", MemoryProposal(
        action="delete", entity="old address",
    ), True),
    ("ambiguous deletion rejected", "I changed my address.", MemoryProposal(
        action="delete", entity="old address",
    ), False),
    ("explicit history", "What did I tell you about my goals?", MemoryProposal(
        action="history",
    ), True),
)


def main() -> int:
    failures = 0
    for name, message, proposal, expected in SCENARIOS:
        actual = evaluate_memory_proposal(
            proposal, current_user_message=message,
        ).eligible
        ok = actual is expected
        print(f"{'PASS' if ok else 'FAIL'} | {name} | expected={expected} actual={actual}")
        failures += not ok
    print(f"Scenarios: {len(SCENARIOS)}; mismatches: {failures}")
    return int(failures != 0)


if __name__ == "__main__":
    raise SystemExit(main())
