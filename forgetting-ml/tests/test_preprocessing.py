import pandas as pd
import numpy as np

from ml.preprocessing.pipeline import build_preprocessor, get_output_feature_names
from ml.features.feature_spec import DEFAULT_SPEC


def _sample_df(n=20):
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "task_category": rng.choice(["Academic", "Work", "Personal"], n),
        "priority": rng.choice(["LOW", "MEDIUM", "HIGH"], n),
        "location": rng.choice(["Home", "Office"], n),
        "weekday": rng.integers(0, 7, n),
        "hour": rng.integers(0, 24, n),
        "deadline_distance_hours": rng.uniform(0, 100, n),
        "previous_completion_count": rng.integers(0, 50, n),
        "previous_forgetting_count": rng.integers(0, 20, n),
        "historical_completion_rate": rng.uniform(0, 1, n),
        "historical_forgetting_rate": rng.uniform(0, 1, n),
        "task_frequency": rng.uniform(0, 1, n),
        "tasks_today": rng.integers(0, 10, n),
        "interruptions_today": rng.integers(0, 10, n),
        "recent_context_switches": rng.integers(0, 10, n),
        "avg_interruption_duration": rng.uniform(0, 20, n),
        "avg_session_duration": rng.uniform(5, 60, n),
    })


def test_preprocessor_fits_and_transforms():
    df = _sample_df()
    pre = build_preprocessor(scale_numeric=True)
    X = pre.fit_transform(df[DEFAULT_SPEC.categorical + DEFAULT_SPEC.numeric])
    assert X.shape[0] == len(df)
    assert X.shape[1] > len(DEFAULT_SPEC.numeric)  # one-hot expands categorical cols


def test_preprocessor_handles_unknown_category():
    df = _sample_df()
    pre = build_preprocessor(scale_numeric=False)
    pre.fit(df[DEFAULT_SPEC.categorical + DEFAULT_SPEC.numeric])

    new_row = df.iloc[[0]].copy()
    new_row["task_category"] = "NeverSeenBefore"
    # Should not raise due to handle_unknown="ignore"
    X = pre.transform(new_row[DEFAULT_SPEC.categorical + DEFAULT_SPEC.numeric])
    assert X.shape[0] == 1


def test_output_feature_names_nonempty():
    df = _sample_df()
    pre = build_preprocessor(scale_numeric=False)
    pre.fit(df[DEFAULT_SPEC.categorical + DEFAULT_SPEC.numeric])
    names = get_output_feature_names(pre)
    assert len(names) > 0
    assert any("historical_forgetting_rate" in n for n in names)
