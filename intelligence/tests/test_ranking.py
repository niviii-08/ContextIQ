from app.insight_engine import generate_insights
from app.ranking import rank_insights
from app.schemas import Priority


def test_ranked_insights_sorted_descending(sample_bundle):
    insights = generate_insights(sample_bundle)
    ranked = rank_insights(insights)
    scores = [r.rank_score for r in ranked]
    assert scores == sorted(scores, reverse=True)


def test_rank_position_is_sequential(sample_bundle):
    insights = generate_insights(sample_bundle)
    ranked = rank_insights(insights)
    positions = [r.rank_position for r in ranked]
    assert positions == list(range(1, len(ranked) + 1))


def test_high_confidence_forgetting_insight_ranks_high(sample_bundle):
    insights = generate_insights(sample_bundle)
    ranked = rank_insights(insights)
    high_risk = [r for r in ranked if "Lab Record" in r.title]
    assert high_risk
    assert all(r.priority in (Priority.HIGH, Priority.MEDIUM) for r in high_risk)


def test_upstream_high_priority_never_downgraded_below_medium(sample_bundle):
    insights = generate_insights(sample_bundle)
    ranked = rank_insights(insights)
    for r in ranked:
        if r.priority == Priority.HIGH or "High forgetting risk" in r.title:
            assert r.priority in (Priority.HIGH, Priority.MEDIUM)


def test_empty_insight_list_ranks_to_empty():
    assert rank_insights([]) == []
