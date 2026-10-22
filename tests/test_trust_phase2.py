from datetime import datetime, timedelta, timezone

import pytest

from agm.trust import age_factor, rank_score, tier_weight


def test_tier_weights_match_decision_d008():
    assert tier_weight("human_verified") == 1.0
    assert tier_weight("tool_verified") == 0.85
    assert tier_weight("trusted_agent") == 0.6
    assert tier_weight("untrusted") == 0.3


def test_age_factor_is_one_at_zero_age_and_half_after_ten_years():
    now = datetime(2030, 1, 1, tzinfo=timezone.utc)
    assert age_factor(now.isoformat(), now=now) == pytest.approx(1.0)
    ten_years_ago = now - timedelta(days=3650)
    assert age_factor(ten_years_ago.isoformat(), now=now) == pytest.approx(0.5)


def test_rank_score_matches_d008_weighted_sum():
    score = rank_score(
        similarity=0.8,
        confidence=0.7,
        trust=0.85,
        recency=0.9,
        decay_weight=0.6,
    )
    expected = 0.55 * 0.8 + 0.15 * 0.7 + 0.10 * 0.85 + 0.10 * 0.9 + 0.10 * 0.6
    assert score == pytest.approx(expected)
    assert 0.0 <= score <= 1.0
