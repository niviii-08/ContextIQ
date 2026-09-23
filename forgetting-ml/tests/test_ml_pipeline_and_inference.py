"""
Tests for:
- Splitting logic (chronological, no leakage, CV splits)
- Preprocessing pipeline (consistency, unseen categories, missing values)
- Model loading + artifact inventory
- Predictions (shape, probability range, batch consistency)
- Invalid inputs (type, domain, missing features, NaN)
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.features.feature_spec import (
    DEFAULT_SPEC,
    CATEGORY_DOMAIN,
    PRIORITY_DOMAIN,
    LOCATION_DOMAIN,
)
from ml.preprocessing.pipeline import build_preprocessor, get_output_feature_names
from ml.training.splits import (
    chronological_split,
    chronological_splits_summary,
    time_series_cv_splits,
)

TINY_DATASET_PATH = ROOT / "datasets" / "tasks_raw.csv"


def _load_tiny_or_skip(n_rows=3000):
    if not TINY_DATASET_PATH.exists():
        pytest.skip("Dataset missing; run `python -m ml.data.generate_dataset` or training first.")
    df = pd.read_csv(TINY_DATASET_PATH)
    return df.head(n_rows)


# ---------- Splits ----------

def test_chronological_split_sizes_and_ratios():
    df = _load_tiny_or_skip()
    train, val, test = chronological_split(df, train_frac=0.7, val_frac=0.15)
    # Rows preserved
    assert len(train) + len(val) + len(test) == len(df)
    # Rows are non-empty
    assert len(train) > 0 and len(val) > 0 and len(test) > 0
    # Rough ratio (date-based, so not exact row counts)
    assert len(train) > len(val)
    assert len(train) > len(test)


def test_chronological_split_no_date_overlap():
    df = _load_tiny_or_skip()
    train, val, test = chronological_split(df)
    td = set(train["date"].unique())
    vd = set(val["date"].unique())
    ted = set(test["date"].unique())
    assert not (td & vd)
    assert not (td & ted)
    assert not (vd & ted)
    # Chronological ordering
    assert max(td) < min(vd)
    assert max(vd) < min(ted)


def test_chronological_split_users_appear_across_splits():
    df = _load_tiny_or_skip()
    train, val, test = chronological_split(df)
    tr_u = set(train["user_id"].unique())
    te_u = set(test["user_id"].unique())
    # It would be very unusual for zero overlap with 100 users over 95 days
    assert len(tr_u & te_u) >= 1


def test_chronological_splits_summary_keys():
    df = _load_tiny_or_skip()
    train, val, test = chronological_split(df)
    s = chronological_splits_summary(train, val, test)
    for k in ("train", "val", "test"):
        assert "n_rows" in s[k]
        assert "n_users" in s[k]
        assert "date_min" in s[k]
        assert "date_max" in s[k]
        assert s[k]["forget_rate"] is not None


def test_time_series_cv_splits_yield():
    df = _load_tiny_or_skip(5000)
    splits = list(time_series_cv_splits(df, n_splits=3))
    assert len(splits) >= 1
    for tr, te in splits:
        assert len(tr) > 0
        assert len(te) > 0
        tr_d = set(tr["date"].unique())
        te_d = set(te["date"].unique())
        assert not (tr_d & te_d)
        assert max(tr_d) < min(te_d)


# ---------- Preprocessing ----------

def _toy_df(n=200, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "task_category": rng.choice(CATEGORY_DOMAIN, size=n),
        "priority": rng.choice(PRIORITY_DOMAIN, size=n),
        "location": rng.choice(LOCATION_DOMAIN, size=n),
        "weekday": rng.integers(0, 7, size=n),
        "hour": rng.integers(6, 23, size=n),
        "deadline_distance_hours": rng.uniform(1, 200, size=n),
        "previous_completion_count": rng.integers(0, 200, size=n),
        "previous_forgetting_count": rng.integers(0, 50, size=n),
        "historical_completion_rate": rng.uniform(0, 1, size=n),
        "historical_forgetting_rate": rng.uniform(0, 1, size=n),
        "task_frequency": rng.uniform(0, 1, size=n),
        "tasks_today": rng.integers(1, 15, size=n),
        "interruptions_today": rng.integers(0, 20, size=n),
        "recent_context_switches": rng.integers(0, 30, size=n),
        "avg_interruption_duration": rng.uniform(1, 30, size=n),
        "avg_session_duration": rng.uniform(5, 90, size=n),
    })


def test_build_preprocessor_scaled_and_unscaled_output_shape():
    df = _toy_df()
    cols = DEFAULT_SPEC.categorical + DEFAULT_SPEC.numeric
    X = df[cols]
    p_sc = build_preprocessor(scale_numeric=True)
    p_us = build_preprocessor(scale_numeric=False)
    X_sc = p_sc.fit_transform(X)
    X_us = p_us.fit_transform(X)
    assert X_sc.shape[0] == len(df)
    assert X_us.shape[0] == len(df)
    assert X_sc.shape[1] == X_us.shape[1]
    assert X_sc.shape[1] == len(get_output_feature_names(p_sc))


def test_preprocessor_handles_unseen_categories():
    """One-hot encoder with handle_unknown='ignore' must not crash on new cats."""
    df_tr = _toy_df(100, seed=0)
    df_te = _toy_df(50, seed=7)
    cols = DEFAULT_SPEC.categorical + DEFAULT_SPEC.numeric
    df_te.at[0, "task_category"] = "CATEGORY_NEVER_SEEN_BEFORE"
    df_te.at[1, "priority"] = "WEIRD_PRIORITY"
    p = build_preprocessor(scale_numeric=False)
    p.fit(df_tr[cols])
    out = p.transform(df_te[cols])
    assert out.shape[0] == len(df_te)


def test_preprocessor_imputes_missing_numeric_values():
    df_tr = _toy_df(100, seed=0)
    df_te = _toy_df(30, seed=1)
    cols = DEFAULT_SPEC.categorical + DEFAULT_SPEC.numeric
    df_te.at[0, "deadline_distance_hours"] = np.nan
    df_te.at[1, "historical_completion_rate"] = np.nan
    p = build_preprocessor(scale_numeric=False)
    p.fit(df_tr[cols])
    out = p.transform(df_te[cols])
    assert np.isfinite(out.toarray() if hasattr(out, "toarray") else np.asarray(out)).all()


def test_preprocessor_imputes_missing_categorical_values():
    df_tr = _toy_df(100, seed=0)
    df_te = _toy_df(30, seed=1)
    cols = DEFAULT_SPEC.categorical + DEFAULT_SPEC.numeric
    df_te.at[0, "task_category"] = None
    df_te.at[1, "priority"] = np.nan
    p = build_preprocessor(scale_numeric=False)
    p.fit(df_tr[cols])
    out = p.transform(df_te[cols])
    arr = out.toarray() if hasattr(out, "toarray") else np.asarray(out)
    assert np.isfinite(arr).all()


# ---------- Inference / Model Loading ----------

def _artifact_path(name):
    return ROOT / "artifacts" / name


def _skip_without_artifacts():
    req = ["model_bundle.joblib", "metrics.json", "feature_metadata.json"]
    if not all(_artifact_path(r).exists() for r in req):
        pytest.skip("Training artifacts missing; run `python -m ml.training.train` first.")


@pytest.fixture(scope="module")
def predictor_or_skip():
    _skip_without_artifacts()
    from app.inference import ForgettingPredictor
    return ForgettingPredictor.instance()


def test_model_loading_and_bundle_fields(predictor_or_skip):
    p = predictor_or_skip
    assert p.model is not None
    assert p.preprocessor is not None
    assert p.model_name in ("dummy_most_frequent", "logistic_regression", "random_forest", "xgboost")
    assert p.model_version is not None
    assert isinstance(p.threshold, float)
    assert 0.0 < p.threshold < 1.0
    assert len(p.categorical_features) == 3
    assert len(p.numeric_features) >= 10
    assert len(p.feature_names_transformed) > 0


def test_predict_single_shape_and_probability_range(predictor_or_skip, sample_task_payload):
    r = predictor_or_skip.predict_single(sample_task_payload)
    assert "prediction_probability" in r
    assert "risk_level" in r
    assert "model_version" in r
    assert "top_features" in r
    assert 0.0 <= float(r["prediction_probability"]) <= 1.0
    assert r["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert isinstance(r["top_features"], list)


def test_probability_range_strict(predictor_or_skip, sample_task_payload):
    """Make sure probabilities are strictly within [0, 1] for many randomized inputs."""
    rng = np.random.default_rng(1)
    base = dict(sample_task_payload)
    for _ in range(50):
        payload = dict(base)
        payload["historical_completion_rate"] = float(rng.uniform(0, 1))
        payload["historical_forgetting_rate"] = float(rng.uniform(0, 1))
        payload["previous_forgetting_count"] = int(rng.integers(0, 80))
        payload["interruptions_today"] = int(rng.integers(0, 25))
        payload["deadline_distance_hours"] = float(rng.uniform(0.5, 500))
        payload["tasks_today"] = int(rng.integers(1, 20))
        payload["task_category"] = str(rng.choice(CATEGORY_DOMAIN))
        payload["priority"] = str(rng.choice(PRIORITY_DOMAIN))
        payload["location"] = str(rng.choice(LOCATION_DOMAIN))
        payload["weekday"] = int(rng.integers(0, 7))
        payload["hour"] = int(rng.integers(0, 24))
        r = predictor_or_skip.predict_single(payload)
        p = float(r["prediction_probability"])
        assert 0.0 <= p <= 1.0, f"prob out of range: {p}"


def test_batch_matches_single(predictor_or_skip, sample_task_payload, high_risk_payload, low_risk_payload):
    batch = predictor_or_skip.predict_batch(
        [sample_task_payload, high_risk_payload, low_risk_payload]
    )
    assert len(batch) == 3
    for i, pl in enumerate([sample_task_payload, high_risk_payload, low_risk_payload]):
        s = predictor_or_skip.predict_single(pl)
        assert batch[i]["prediction_probability"] == s["prediction_probability"]
        assert batch[i]["risk_level"] == s["risk_level"]


def test_risk_ordering_high_gt_low(predictor_or_skip, high_risk_payload, low_risk_payload):
    """A synthetic high-risk input should rank strictly riskier than low-risk."""
    h = predictor_or_skip.predict_single(high_risk_payload)
    l = predictor_or_skip.predict_single(low_risk_payload)
    # This ordering should be strongly directional (feature values are extreme
    # and align with the dataset generator's score function). A strict > is
    # acceptable here; a failure would indicate the model is degenerate.
    assert h["prediction_probability"] > l["prediction_probability"]


# ---------- Invalid input handling ----------

def test_missing_required_feature_raises(predictor_or_skip, sample_task_payload):
    bad = dict(sample_task_payload)
    del bad["historical_completion_rate"]
    with pytest.raises(ValueError, match="Missing required features"):
        predictor_or_skip.predict_single(bad)


def test_multiple_missing_features_raises(predictor_or_skip, sample_task_payload):
    bad = dict(sample_task_payload)
    for k in ("interruptions_today", "priority", "task_frequency"):
        del bad[k]
    with pytest.raises(ValueError):
        predictor_or_skip.predict_batch([bad])


def test_nan_feature_handled(predictor_or_skip, sample_task_payload):
    """Preprocessor imputes NaN; inference should still return a valid probability."""
    bad = dict(sample_task_payload)
    bad["deadline_distance_hours"] = float("nan")
    bad["historical_completion_rate"] = float("nan")
    r = predictor_or_skip.predict_single(bad)
    p = float(r["prediction_probability"])
    assert 0.0 <= p <= 1.0


def test_empty_batch_returns_empty(predictor_or_skip):
    assert predictor_or_skip.predict_batch([]) == []


def test_batch_handles_mixed_valid_invalid(predictor_or_skip, sample_task_payload):
    good = dict(sample_task_payload)
    bad = dict(sample_task_payload)
    del bad["historical_forgetting_rate"]
    with pytest.raises(ValueError):
        predictor_or_skip.predict_batch([good, bad])


# ---------- Artifacts sanity ----------

def test_artifacts_inventory_and_sanity():
    _skip_without_artifacts()
    with open(_artifact_path("metrics.json")) as f:
        m = json.load(f)
    with open(_artifact_path("feature_metadata.json")) as f:
        fm = json.load(f)
    required_plots = [
        "confusion_matrix.png",
        "roc_curve.png",
        "precision_recall_curve.png",
        "feature_importance.png",
        "calibration_plot.png",
        "shap_summary_bar.png",
        "shap_beeswarm.png",
        "shap_individual_waterfalls.png",
        "performance_report.md",
    ]
    for p in required_plots:
        assert _artifact_path(p).exists(), f"Missing artifact {p}"

    assert "final_selected_metrics" in m
    fin = m["final_selected_metrics"]
    for k in ("accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc", "brier_score", "confusion_matrix"):
        assert k in fin, f"missing {k} in final metrics"

    cm = fin["confusion_matrix"]
    assert isinstance(cm, list) and len(cm) == 2 and len(cm[0]) == 2

    # PR-AUC should be strictly better than the constant-classifier baseline (=pos_rate)
    assert "class_balance" in m
    pos_rate_key = "1" if "1" in m["class_balance"] else 1
    baseline = float(m["class_balance"].get(pos_rate_key, 0.5))
    assert float(fin["pr_auc"]) > baseline * 1.05, (
        f"Final PR-AUC {fin['pr_auc']} not meaningfully above baseline {baseline}"
    )

    # feature_metadata contents
    assert "preprocessor" in fm
    assert "raw_categorical_features" in fm
    assert "raw_numeric_features" in fm
    assert fm["selected_model"] == m["selected_model"]


def test_performance_report_md_has_expected_sections():
    rp = _artifact_path("performance_report.md")
    if not rp.exists():
        pytest.skip("performance_report.md missing")
    md = rp.read_text(encoding="utf-8")
    for h in (
        "# Forgetting-Risk Prediction",
        "## Which Metric Matters and Why",
        "## Candidate Models",
        "## Final Selected Model",
        "## Time-Series Cross-Validation",
        "## Target-Leakage Prevention",
        "## Artifact Inventory",
    ):
        assert h in md, f"Missing section in report: {h}"
