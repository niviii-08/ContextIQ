from app.analytics import friction as f


def test_forgetting_score_scales_linearly():
    assert f.compute_forgetting_score(0.0) == 0.0
    assert f.compute_forgetting_score(0.5) == 50.0
    assert f.compute_forgetting_score(1.0) == 100.0


def test_interruption_score_saturates():
    # far above saturation point -> clamped to 100
    score = f.compute_interruption_score(interruption_count=1000, total_active_seconds=3600)
    assert score == 100.0


def test_interruption_score_zero_when_no_active_time():
    assert f.compute_interruption_score(interruption_count=5, total_active_seconds=0) == 0.0


def test_context_switch_score_zero_sessions():
    assert f.compute_context_switch_score(total_context_switches=10, total_sessions=0) == 0.0


def test_recovery_score_none_when_no_data():
    assert f.compute_recovery_score(None) == 0.0


def test_recovery_score_saturates_at_30_minutes():
    score = f.compute_recovery_score(average_resume_delay_seconds=60 * 60)  # 1 hour, above 30-min ceiling
    assert score == 100.0


def test_overall_score_is_weighted_average():
    overall = f.compute_overall_score(
        forgetting_score=100, interruption_score=0, context_switch_score=0, recovery_score=0
    )
    assert overall == 35.0  # matches WEIGHT_FORGETTING


def test_compute_friction_score_all_zero_when_no_friction():
    result = f.compute_friction_score(
        task_forgetting_rate=0.0,
        interruption_count=0,
        total_active_seconds=3600,
        total_context_switches=0,
        total_sessions=5,
        average_resume_delay_seconds=None,
    )
    assert result["overall_score"] == 0.0
    assert result["forgetting_score"] == 0.0


def test_compute_friction_score_bounded_0_to_100():
    result = f.compute_friction_score(
        task_forgetting_rate=1.0,
        interruption_count=10_000,
        total_active_seconds=1,
        total_context_switches=10_000,
        total_sessions=1,
        average_resume_delay_seconds=999_999,
    )
    for key in ["overall_score", "forgetting_score", "interruption_score", "context_switch_score", "recovery_score"]:
        assert 0.0 <= result[key] <= 100.0
