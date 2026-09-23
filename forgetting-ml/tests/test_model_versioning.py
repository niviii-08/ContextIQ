import json
from pathlib import Path

import joblib

from ml.training.config import MODEL_VERSION

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts"


def test_model_bundle_exists():
    assert (ARTIFACTS_DIR / "model_bundle.joblib").exists()


def test_metrics_file_exists_and_has_version():
    metrics_path = ARTIFACTS_DIR / "metrics.json"
    assert metrics_path.exists()
    with open(metrics_path) as f:
        metrics = json.load(f)
    assert "model_version" in metrics
    assert metrics["model_version"] == MODEL_VERSION
    assert "selected_model" in metrics
    assert "final_selected_metrics" in metrics


def test_bundle_contains_required_keys():
    bundle = joblib.load(ARTIFACTS_DIR / "model_bundle.joblib")
    required_keys = {
        "model", "raw_model", "preprocessor", "model_name", "model_version",
        "threshold", "calibrated", "feature_names_raw", "feature_names_transformed",
        "categorical_features", "numeric_features",
    }
    assert required_keys.issubset(bundle.keys())


def test_report_figures_exist():
    for fname in [
        "confusion_matrix.png", "roc_curve.png", "precision_recall_curve.png",
        "feature_importance.png", "calibration_plot.png",
    ]:
        assert (ARTIFACTS_DIR / fname).exists(), f"Missing {fname}"
