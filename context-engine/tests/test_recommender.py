from app.schemas.associations import AssociationRule
from ml.associations.recommender import (
    RecommendationQualityConfig,
    DismissalStore,
    recommend_for_context,
    prioritize_recommendations,
    MockForgettingRiskProvider,
)


def _rule(antecedents, consequents, support=0.4, confidence=0.8, lift=2.0, context="department"):
    return AssociationRule(
        context=context,
        antecedents=antecedents,
        consequents=consequents,
        support=support,
        confidence=confidence,
        lift=lift,
    )


def test_basic_recommendation_from_empty_antecedent_rule():
    rules = [_rule([], ["collect_form"], confidence=0.9, support=0.5, lift=1.5)]
    recs = recommend_for_context("u1", "department", rules)
    assert len(recs) == 1
    assert recs[0].task == "collect_form"


def test_antecedent_must_be_satisfied_by_completed_tasks():
    rules = [_rule(["collect_form"], ["submit_record"], confidence=0.8)]
    # Not yet completed collect_form -> rule not applicable.
    recs = recommend_for_context("u1", "department", rules, completed_tasks=[])
    assert recs == []
    # Completed collect_form -> rule becomes applicable.
    recs2 = recommend_for_context("u1", "department", rules, completed_tasks=["collect_form"])
    assert len(recs2) == 1
    assert recs2[0].task == "submit_record"


def test_completed_tasks_excluded_from_recommendations():
    rules = [_rule([], ["collect_form"], confidence=0.9)]
    recs = recommend_for_context("u1", "department", rules, completed_tasks=["collect_form"])
    assert recs == []


def test_duplicate_task_deduplicated_keeping_best_rule():
    rules = [
        _rule([], ["collect_form"], confidence=0.5, lift=1.2),
        _rule([], ["collect_form"], confidence=0.9, lift=3.0),
    ]
    recs = recommend_for_context("u1", "department", rules)
    assert len(recs) == 1
    assert recs[0].confidence == 0.9
    assert recs[0].lift == 3.0


def test_weak_rules_filtered_by_config_thresholds():
    rules = [_rule([], ["weak_task"], confidence=0.2, support=0.02, lift=0.9)]
    recs = recommend_for_context(
        "u1", "department", rules, config=RecommendationQualityConfig(min_confidence=0.5, min_support=0.05, min_lift=1.0)
    )
    assert recs == []


def test_cooldown_suppresses_recently_shown_recommendation():
    rules = [_rule([], ["collect_form"], confidence=0.9)]
    store = DismissalStore()
    config = RecommendationQualityConfig(cooldown_seconds=3600)

    recs1 = recommend_for_context("u1", "department", rules, dismissal_store=store, config=config)
    assert len(recs1) == 1

    # Immediately asking again should be suppressed by cooldown.
    recs2 = recommend_for_context("u1", "department", rules, dismissal_store=store, config=config)
    assert recs2 == []


def test_dismissal_suppresses_task():
    rules = [_rule([], ["collect_form"], confidence=0.9)]
    store = DismissalStore()
    store.record_dismissal("u1", "department", "collect_form", cooldown_seconds=3600)

    recs = recommend_for_context("u1", "department", rules, dismissal_store=store)
    assert recs == []


def test_max_recommendations_cap():
    rules = [_rule([], [f"task_{i}"], confidence=0.9 - i * 0.01) for i in range(10)]
    recs = recommend_for_context("u1", "department", rules, max_recommendations=3)
    assert len(recs) == 3


def test_mock_forgetting_provider_returns_probability_in_range():
    provider = MockForgettingRiskProvider()
    p = provider.get_forgetting_probability("u1", "collect_form")
    assert 0.3 <= p <= 0.9


def test_prioritize_recommendations_combines_scores():
    rules = [_rule([], ["collect_form"], confidence=0.6)]
    recs = recommend_for_context("u1", "department", rules)
    provider = MockForgettingRiskProvider(fixed_values={"collect_form": 0.9})
    prioritized = prioritize_recommendations(
        "u1", recs, forgetting_provider=provider, association_weight=0.5, forgetting_weight=0.5
    )
    assert len(prioritized) == 1
    assert prioritized[0].forgetting_probability == 0.9
    assert prioritized[0].priority_score == round(0.5 * 0.6 + 0.5 * 0.9, 4)


def test_prioritize_recommendations_without_provider_falls_back_to_confidence():
    rules = [_rule([], ["collect_form"], confidence=0.7)]
    recs = recommend_for_context("u1", "department", rules)
    prioritized = prioritize_recommendations("u1", recs, forgetting_provider=None)
    assert prioritized[0].priority_score == 0.7
    assert prioritized[0].forgetting_probability is None
