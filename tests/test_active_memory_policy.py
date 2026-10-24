from agm.active_memory_policy import MemoryProposal, evaluate_memory_proposal


def test_write_requires_exact_user_quote_and_complete_fields():
    proposal = MemoryProposal(
        action="write", evidence_quote="I prefer concise answers",
        entity="user", attribute="style", value="concise",
    )
    assert evaluate_memory_proposal(
        proposal, current_user_message="I prefer concise answers."
    ).eligible
    assert not evaluate_memory_proposal(
        proposal, current_user_message="Please be concise."
    ).eligible


def test_correction_requires_explicit_correction_language():
    base = dict(
        action="correct", evidence_quote="my timezone is UTC+5:30",
        entity="user", attribute="timezone", value="UTC+5:30",
    )
    assert evaluate_memory_proposal(
        MemoryProposal(**base),
        current_user_message="Actually, my timezone is UTC+5:30",
    ).eligible
    assert not evaluate_memory_proposal(
        MemoryProposal(**base),
        current_user_message="My timezone is UTC+5:30",
    ).eligible


def test_history_requires_explicit_recall_intent():
    proposal = MemoryProposal(action="history")
    assert evaluate_memory_proposal(
        proposal, current_user_message="What did I say about my project?"
    ).eligible
    assert not evaluate_memory_proposal(
        proposal, current_user_message="Help me plan my project."
    ).eligible


def test_delete_requires_explicit_request_and_target():
    proposal = MemoryProposal(action="delete", entity="old address")
    assert evaluate_memory_proposal(
        proposal, current_user_message="Please forget my old address."
    ).eligible
    assert not evaluate_memory_proposal(
        proposal, current_user_message="I moved from my old address."
    ).eligible
    assert not evaluate_memory_proposal(
        MemoryProposal(action="delete"),
        current_user_message="Forget that.",
    ).eligible
