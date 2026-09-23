from app.schemas.associations import AssociationRule
from ml.associations.recommender import (
    recommend_for_context,
    prioritize_recommendations,
    ForgettingRiskProvider,
    MockForgettingRiskProvider,
)


def test_custom_forgetting_provider_conforms_to_interface():
    class AlwaysHighRisk(ForgettingRiskProvider):
        def get_forgetting_probability(self, user_id: str, task: str) -> float:
            return 0.99

    rule = AssociationRule(
        context="department",
        antecedents=[],
        consequents=["collect_form"],
        support=0.4,
        confidence=0.5,
        lift=1.5,
    )
    recs = recommend_for_context("u1", "department", [rule])
    prioritized = prioritize_recommendations("u1", recs, forgetting_provider=AlwaysHighRisk())
    assert prioritized[0].forgetting_probability == 0.99
    # High forgetting risk should push the combined score above the raw confidence.
    assert prioritized[0].priority_score > 0.5


def test_combined_pipeline_reorders_by_forgetting_risk():
    rules = [
        AssociationRule(
            context="department", antecedents=[], consequents=["collect_form"],
            support=0.4, confidence=0.9, lift=2.0,
        ),
        AssociationRule(
            context="department", antecedents=[], consequents=["submit_record"],
            support=0.4, confidence=0.55, lift=1.5,
        ),
    ]
    recs = recommend_for_context("u1", "department", rules)
    # collect_form should rank first on confidence alone.
    assert recs[0].task == "collect_form"

    provider = MockForgettingRiskProvider(
        fixed_values={"collect_form": 0.1, "submit_record": 0.95}
    )
    prioritized = prioritize_recommendations(
        "u1", recs, forgetting_provider=provider, association_weight=0.3, forgetting_weight=0.7
    )
    # With forgetting risk weighted heavily, submit_record should now outrank collect_form.
    assert prioritized[0].task == "submit_record"


def test_mock_provider_is_deterministic():
    provider = MockForgettingRiskProvider()
    p1 = provider.get_forgetting_probability("u1", "collect_form")
    p2 = provider.get_forgetting_probability("u1", "collect_form")
    assert p1 == p2
