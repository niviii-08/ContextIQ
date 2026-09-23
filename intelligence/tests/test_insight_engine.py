from app.insight_engine import generate_insights
from app.schemas import InsightType


def test_generates_frequent_forgetting_insight(sample_bundle):
    insights = generate_insights(sample_bundle)
    types = [i.type for i in insights]
    assert InsightType.FREQUENT_FORGETTING in types


def test_generates_context_switching_insight(sample_bundle):
    insights = generate_insights(sample_bundle)
    types = [i.type for i in insights]
    assert InsightType.REPEATED_CONTEXT_SWITCHING in types


def test_generates_high_interruption_insight(sample_bundle):
    insights = generate_insights(sample_bundle)
    types = [i.type for i in insights]
    assert InsightType.HIGH_INTERRUPTION_COST in types


def test_generates_association_insight(sample_bundle):
    insights = generate_insights(sample_bundle)
    types = [i.type for i in insights]
    assert InsightType.REPEATED_CONTEXTUAL_ASSOCIATION in types


def test_generates_friction_trend_insight(sample_bundle):
    insights = generate_insights(sample_bundle)
    types = [i.type for i in insights]
    assert InsightType.INCREASING_FRICTION in types


def test_no_insights_for_empty_bundle(empty_bundle):
    insights = generate_insights(empty_bundle)
    assert insights == []


def test_evidence_values_trace_to_input(sample_bundle):
    """Every evidence value in a forgetting insight must match the source
    ForgettingPrediction exactly — never invented."""
    insights = generate_insights(sample_bundle)
    forgetting_insights = [i for i in insights if i.type == InsightType.FREQUENT_FORGETTING]
    assert forgetting_insights
    for ins in forgetting_insights:
        for ev in ins.evidence:
            if ev.field == "previous_forgetting_count":
                assert ev.value == "4"
            if ev.field == "probability":
                assert ev.value == "0.82"


def test_low_probability_task_not_flagged_high_risk(sample_bundle):
    insights = generate_insights(sample_bundle)
    titles = [i.title for i in insights]
    assert not any("Submit Timesheet" in t and "High forgetting risk" in t for t in titles)
