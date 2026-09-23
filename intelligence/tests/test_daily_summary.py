from app.daily_summary import generate_daily_summary


def test_daily_summary_highest_risk_task_matches_input(sample_bundle):
    summary = generate_daily_summary(sample_bundle)
    assert summary.highest_risk_task == "Lab Record"
    assert summary.highest_risk_probability == 0.82


def test_daily_summary_avoidable_friction_from_recovery_cost(sample_bundle):
    summary = generate_daily_summary(sample_bundle)
    # recovery_cost_minutes for the single context insight is 18.0
    assert summary.estimated_avoidable_friction_minutes == 18.0


def test_daily_summary_context_reminder_uses_strong_association(sample_bundle):
    summary = generate_daily_summary(sample_bundle)
    assert summary.context_reminder == "Department tasks are frequently forgotten"


def test_daily_summary_handles_empty_bundle(empty_bundle):
    summary = generate_daily_summary(empty_bundle)
    assert summary.highest_risk_task is None
    assert summary.estimated_avoidable_friction_minutes is None
    assert summary.top_insights == []
