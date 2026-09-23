from app.analytics import compute_trend_slope, metrics_to_dataframe, summarize_metric_series
from app.schemas import BehaviourMetric


def test_compute_trend_slope_increasing():
    slope = compute_trend_slope([1.0, 2.0, 3.0, 4.0])
    assert slope == 1.0


def test_compute_trend_slope_decreasing():
    slope = compute_trend_slope([4.0, 3.0, 2.0, 1.0])
    assert slope == -1.0


def test_compute_trend_slope_flat():
    slope = compute_trend_slope([2.0, 2.0, 2.0])
    assert slope == 0.0


def test_compute_trend_slope_insufficient_data():
    assert compute_trend_slope([]) is None
    assert compute_trend_slope([1.0]) is None


def test_metrics_to_dataframe_empty():
    df = metrics_to_dataframe([])
    assert df.empty
    assert list(df.columns) == ["metric_name", "value", "period"]


def test_metrics_to_dataframe_preserves_values():
    metrics = [
        BehaviourMetric(metric_name="friction_score", value=0.3, period="p1"),
        BehaviourMetric(metric_name="friction_score", value=0.5, period="p2"),
    ]
    df = metrics_to_dataframe(metrics)
    assert len(df) == 2
    assert df.iloc[0]["value"] == 0.3
    assert df.iloc[1]["period"] == "p2"


def test_summarize_metric_series_computes_expected_stats():
    metrics = [
        BehaviourMetric(metric_name="friction_score", value=0.2, period="p1"),
        BehaviourMetric(metric_name="friction_score", value=0.4, period="p2"),
        BehaviourMetric(metric_name="friction_score", value=0.6, period="p3"),
    ]
    summary = summarize_metric_series(metrics, "friction_score")
    assert summary["count"] == 3
    assert summary["mean"] == 0.4
    assert summary["min"] == 0.2
    assert summary["max"] == 0.6
    assert summary["slope"] == 0.2


def test_summarize_metric_series_missing_metric_returns_nulls():
    summary = summarize_metric_series([], "friction_score")
    assert summary["count"] == 0
    assert summary["mean"] is None
    assert summary["slope"] is None
