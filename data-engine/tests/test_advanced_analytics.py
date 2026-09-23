"""
Tests for advanced analytics components including derived metrics, insights, and statistical analysis.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.analytics import derived_metrics as dm
from app.analytics import insights as ins
from app.analytics import statistical_analysis as sa


# Fixtures for test data

@pytest.fixture
def sample_tasks_df():
    """Create sample tasks DataFrame for testing."""
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=100, freq='H')
    return pd.DataFrame({
        "id": range(1, 101),
        "location_id": [1, 2, 3] * 33 + [1],
        "title": [f"Task {i}" for i in range(1, 101)],
        "category": ["Academic", "Work", "Personal"] * 33 + ["Academic"],
        "priority": ["HIGH", "MEDIUM", "LOW"] * 33 + ["HIGH"],
        "status": ["completed"] * 70 + ["forgotten"] * 20 + ["cancelled"] * 10,
        "deadline_at": [datetime.now() + timedelta(days=i) for i in range(100)],
        "created_at": dates,
        "started_at": dates,
        "completed_at": dates + timedelta(hours=1),
    })


@pytest.fixture
def sample_sessions_df():
    """Create sample sessions DataFrame for testing."""
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=50, freq='H')
    return pd.DataFrame({
        "id": range(1, 51),
        "task_id": range(1, 51),
        "location_id": [1, 2, 3] * 16 + [1, 2],
        "session_start": dates,
        "session_end": dates + timedelta(minutes=30),
        "focused_time_seconds": [1800] * 50,
        "interruption_time_seconds": [300] * 50,
        "resume_delay_seconds": [60, 120, 180] * 16 + [60, 120],
        "context_switch_count": [1, 2, 0] * 16 + [1, 2],
        "interruption_count": [2, 3, 1] * 16 + [2, 3],
    })


@pytest.fixture
def sample_interruptions_df():
    """Create sample interruptions DataFrame for testing."""
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='H')
    return pd.DataFrame({
        "id": range(1, 31),
        "task_id": range(1, 31),
        "location_id": [1, 2, 3] * 10,
        "interruption_type": ["phone", "email", "notification"] * 10,
        "start_time": dates,
        "end_time": dates + timedelta(minutes=5),
        "duration_seconds": [300] * 30,
    })


@pytest.fixture
def sample_location_labels():
    """Create sample location labels."""
    return {1: "Home", 2: "Office", 3: "Campus"}


# Derived Metrics Tests

def test_compute_forget_risk(sample_tasks_df, sample_sessions_df, sample_interruptions_df):
    """Test forget risk metric computation."""
    result = dm.compute_forget_risk(sample_tasks_df, sample_sessions_df, sample_interruptions_df)
    
    assert "forget_risk" in result
    assert 0.0 <= result["forget_risk"] <= 1.0
    assert "components" in result
    assert "recent_forgetting_rate" in result["components"]
    assert "interruption_density" in result["components"]


def test_compute_context_switch_rate(sample_sessions_df):
    """Test context switch rate computation."""
    result = dm.compute_context_switch_rate(sample_sessions_df)
    
    assert "context_switch_rate" in result
    assert "total_switches" in result
    assert "active_hours" in result
    assert result["total_switches"] >= 0
    assert result["active_hours"] >= 0


def test_compute_interruption_rate(sample_interruptions_df, sample_sessions_df):
    """Test interruption rate computation."""
    result = dm.compute_interruption_rate(sample_interruptions_df, sample_sessions_df)
    
    assert "interruption_rate" in result
    assert "total_interruptions" in result
    assert "active_hours" in result
    assert result["total_interruptions"] == len(sample_interruptions_df)


def test_compute_recovery_time(sample_sessions_df):
    """Test recovery time computation."""
    result = dm.compute_recovery_time(sample_sessions_df)
    
    assert "recovery_time_seconds" in result
    assert "recovery_time_minutes" in result
    assert "sample_size" in result
    assert result["recovery_time_seconds"] >= 0


def test_compute_behavioral_friction_score(sample_tasks_df, sample_sessions_df, sample_interruptions_df):
    """Test behavioral friction score computation."""
    result = dm.compute_behavioral_friction_score(sample_tasks_df, sample_sessions_df, sample_interruptions_df)
    
    assert "friction_score" in result
    assert 0.0 <= result["friction_score"] <= 100.0
    assert "components" in result
    assert "forgetting_component" in result["components"]
    assert "interruption_component" in result["components"]


def test_compute_completion_reliability(sample_tasks_df):
    """Test completion reliability computation."""
    result = dm.compute_completion_reliability(sample_tasks_df)
    
    assert "completion_reliability" in result
    assert 0.0 <= result["completion_reliability"] <= 1.0
    assert "mean_daily_rate" in result
    assert "std_daily_rate" in result


def test_compute_context_consistency(sample_tasks_df, sample_location_labels):
    """Test context consistency computation."""
    result = dm.compute_context_consistency(sample_tasks_df, sample_location_labels)
    
    assert "context_consistency" in result
    assert 0.0 <= result["context_consistency"] <= 1.0
    assert "category_scores" in result


def test_compute_repetition_strength(sample_tasks_df):
    """Test repetition strength computation."""
    result = dm.compute_repetition_strength(sample_tasks_df)
    
    assert "repetition_strength" in result
    assert 0.0 <= result["repetition_strength"] <= 1.0
    assert "category_strengths" in result


def test_compute_time_lost_to_interruptions(sample_interruptions_df, sample_sessions_df):
    """Test time lost to interruptions computation."""
    result = dm.compute_time_lost_to_interruptions(sample_interruptions_df, sample_sessions_df)
    
    assert "time_lost_hours" in result
    assert "interruption_hours" in result
    assert "switch_overhead_hours" in result
    assert result["time_lost_hours"] >= 0


def test_derived_metrics_empty_data():
    """Test derived metrics with empty data."""
    empty_df = pd.DataFrame()
    
    result = dm.compute_forget_risk(empty_df, empty_df, empty_df)
    assert result["forget_risk"] == 0.0
    
    result = dm.compute_context_switch_rate(empty_df)
    assert result["context_switch_rate"] == 0.0


# Insights Tests

def test_generate_forgetting_timing_insight(sample_tasks_df, sample_sessions_df):
    """Test forgetting timing insight generation."""
    result = ins.generate_forgetting_timing_insight(sample_tasks_df, sample_sessions_df)
    
    assert "insight_type" in result
    assert result["insight_type"] == "forgetting_timing"
    assert "message" in result
    assert "evidence" in result
    assert "risk_level" in result
    assert "recommendation" in result


def test_generate_context_forgetting_insight(sample_tasks_df, sample_location_labels):
    """Test context forgetting insight generation."""
    result = ins.generate_context_forgetting_insight(sample_tasks_df, sample_location_labels)
    
    assert "insight_type" in result
    assert result["insight_type"] == "context_forgetting"
    assert "evidence" in result
    assert "high_risk_categories" in result["evidence"]


def test_generate_category_friction_insight(sample_tasks_df, sample_sessions_df, sample_interruptions_df):
    """Test category friction insight generation."""
    result = ins.generate_category_friction_insight(sample_tasks_df, sample_sessions_df, sample_interruptions_df)
    
    assert "insight_type" in result
    assert result["insight_type"] == "category_friction"
    assert "category_metrics" in result["evidence"]


def test_generate_context_switch_timing_insight(sample_sessions_df):
    """Test context switch timing insight generation."""
    result = ins.generate_context_switch_timing_insight(sample_sessions_df)
    
    assert "insight_type" in result
    assert result["insight_type"] == "context_switch_timing"
    assert "peak_weekday" in result["evidence"] or "peak_hour" in result["evidence"]


def test_generate_interruption_cost_insight(sample_interruptions_df, sample_sessions_df):
    """Test interruption cost insight generation."""
    result = ins.generate_interruption_cost_insight(sample_interruptions_df, sample_sessions_df)
    
    assert "insight_type" in result
    assert result["insight_type"] == "interruption_cost"
    assert "time_lost_hours" in result["evidence"]


def test_generate_all_insights(sample_tasks_df, sample_sessions_df, sample_interruptions_df, sample_location_labels):
    """Test generation of all insights."""
    result = ins.generate_all_insights(sample_tasks_df, sample_sessions_df, sample_interruptions_df, sample_location_labels)
    
    assert isinstance(result, list)
    assert len(result) == 10  # 10 insights expected
    
    # Check each insight has required fields
    for insight in result:
        if "error" not in insight:
            assert "insight_type" in insight
            assert "message" in insight
            assert "evidence" in insight
            assert "risk_level" in insight
            assert "recommendation" in insight


def test_insights_empty_data():
    """Test insights with empty data."""
    empty_df = pd.DataFrame()
    empty_labels = {}
    
    result = ins.generate_forgetting_timing_insight(empty_df, empty_df)
    assert "message" in result or "error" in result


# Statistical Analysis Tests

def test_compute_distribution_statistics():
    """Test distribution statistics computation."""
    series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    result = sa.compute_distribution_statistics(series)
    
    assert "count" in result
    assert "mean" in result
    assert "median" in result
    assert "std" in result
    assert "min" in result
    assert "max" in result
    assert "q25" in result
    assert "q75" in result
    assert "sample_confidence" in result
    assert result["count"] == 10
    assert result["mean"] == 5.5


def test_compute_distribution_statistics_empty():
    """Test distribution statistics with empty series."""
    series = pd.Series()
    result = sa.compute_distribution_statistics(series)
    
    assert "error" in result


def test_compute_correlation_matrix():
    """Test correlation matrix computation."""
    df = pd.DataFrame({
        "a": [1, 2, 3, 4, 5],
        "b": [2, 4, 6, 8, 10],
        "c": [1, 3, 2, 4, 3],
    })
    result = sa.compute_correlation_matrix(df, ["a", "b", "c"])
    
    assert "correlations" in result
    assert "sample_size" in result
    assert "sample_confidence" in result
    assert "method" in result
    assert result["sample_size"] == 5


def test_compute_correlation_matrix_insufficient_data():
    """Test correlation matrix with insufficient data."""
    df = pd.DataFrame({"a": [1]})
    result = sa.compute_correlation_matrix(df, ["a"])
    
    assert "error" in result


def test_compute_trend_analysis():
    """Test trend analysis computation."""
    dates = pd.date_range(start=datetime.now() - timedelta(days=10), periods=10, freq='D')
    values = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    result = sa.compute_trend_analysis(values, dates)
    
    assert "slope" in result
    assert "r_squared" in result
    assert "trend_direction" in result
    assert "confidence" in result
    assert "sample_size" in result
    assert result["trend_direction"] == "INCREASING"


def test_compute_trend_analysis_insufficient_data():
    """Test trend analysis with insufficient data."""
    dates = pd.date_range(start=datetime.now() - timedelta(days=2), periods=2, freq='D')
    values = pd.Series([1, 2])
    result = sa.compute_trend_analysis(values, dates)
    
    assert "error" in result


def test_compute_distribution_comparison():
    """Test distribution comparison."""
    series1 = pd.Series([1, 2, 3, 4, 5])
    series2 = pd.Series([2, 3, 4, 5, 6])
    result = sa.compute_distribution_comparison(series1, series2)
    
    assert "group1" in result
    assert "group2" in result
    assert "mean_difference" in result
    assert "cohens_d" in result
    assert "effect_size_interpretation" in result


def test_compute_percentile_ranks():
    """Test percentile rank computation."""
    series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    result = sa.compute_percentile_ranks(series, 5)
    
    assert "percentile_rank" in result
    assert "interpretation" in result
    assert "sample_size" in result
    assert 0 <= result["percentile_rank"] <= 100


def test_compute_moving_averages():
    """Test moving averages computation."""
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D')
    values = pd.Series(range(30))
    result = sa.compute_moving_averages(values, dates, windows=[7, 14])
    
    assert "ma_7" in result
    assert "ma_14" in result
    assert "latest" in result["ma_7"]


def test_compute_outlier_detection_iqr():
    """Test outlier detection using IQR method."""
    series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 100])  # 100 is outlier
    result = sa.compute_outlier_detection(series, method="iqr")
    
    assert "outlier_count" in result
    assert "outlier_percentage" in result
    assert "outlier_values" in result
    assert result["outlier_count"] >= 1


def test_compute_outlier_detection_zscore():
    """Test outlier detection using z-score method."""
    series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 100])
    result = sa.compute_outlier_detection(series, method="zscore")
    
    assert "outlier_count" in result
    assert "method" in result
    assert result["method"] == "zscore"


def test_compute_category_association_strength():
    """Test category association strength computation."""
    df = pd.DataFrame({
        "category": ["A", "A", "B", "B", "A", "B"],
        "location": ["X", "X", "Y", "Y", "X", "Y"],
    })
    result = sa.compute_category_association_strength(df, "category", "location")
    
    assert "association_strength" in result
    assert "contingency_table" in result
    assert "sample_size" in result
    assert "interpretation" in result
    assert 0 <= result["association_strength"] <= 1


# Edge Cases and Error Handling

def test_derived_metrics_with_nan_values():
    """Test derived metrics handle NaN values gracefully."""
    tasks_df = pd.DataFrame({
        "status": ["completed", "forgotten", None],
        "created_at": [datetime.now()] * 3,
    })
    sessions_df = pd.DataFrame({
        "focused_time_seconds": [1800, None, 1200],
        "interruption_time_seconds": [300, 200, None],
    })
    
    result = dm.compute_behavioral_friction_score(tasks_df, sessions_df, pd.DataFrame())
    assert "friction_score" in result


def test_insights_with_mixed_data():
    """Test insights handle mixed data quality."""
    tasks_df = pd.DataFrame({
        "status": ["completed", "forgotten", "created"],
        "category": ["A", "B", None],
        "created_at": [datetime.now()] * 3,
    })
    
    result = ins.generate_forgetting_timing_insight(tasks_df, pd.DataFrame())
    assert "insight_type" in result


def test_statistical_analysis_with_single_value():
    """Test statistical analysis with single value."""
    series = pd.Series([5])
    result = sa.compute_distribution_statistics(series)
    
    assert "count" in result
    assert result["count"] == 1
    assert result["std"] == 0.0


def test_statistical_analysis_with_constant_values():
    """Test statistical analysis with constant values."""
    series = pd.Series([5, 5, 5, 5, 5])
    result = sa.compute_distribution_statistics(series)
    
    assert "std" in result
    assert result["std"] == 0.0
    assert result["mean"] == 5.0
