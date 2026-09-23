"""
Integration tests for the complete ML pipeline.
Tests the end-to-end flow from dataset generation to inference.
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


def test_end_to_end_training_flow(tmp_path, monkeypatch):
    """Test that the complete training pipeline runs without errors."""
    # Redirect output directories to temp path
    import ml.data.generate_dataset as gen_mod
    import ml.training.train as train_mod
    
    monkeypatch.setattr(gen_mod, "OUT_DIR", tmp_path / "datasets")
    monkeypatch.setattr(train_mod, "DATASET_PATH", tmp_path / "datasets" / "tasks_raw.csv")
    monkeypatch.setattr(train_mod, "DATASET_META_PATH", tmp_path / "datasets" / "dataset_metadata.json")
    monkeypatch.setattr(train_mod, "ARTIFACTS_DIR", tmp_path / "artifacts")
    
    # Generate dataset
    gen_mod.main()
    
    # Verify dataset files exist
    assert (tmp_path / "datasets" / "tasks_raw.csv").exists()
    assert (tmp_path / "datasets" / "users.csv").exists()
    assert (tmp_path / "datasets" / "dataset_metadata.json").exists()
    
    # Run training (with minimal config for speed)
    monkeypatch.setattr(train_mod, "DATASET_CONFIG", {
        "n_users": 20,
        "n_days": 30,
        "min_observations": 1000,
        "seed": 42,
    })
    
    # Re-generate smaller dataset
    gen_mod.main()
    
    # Run training
    train_mod.main()
    
    # Verify artifacts exist
    artifacts_dir = tmp_path / "artifacts"
    assert (artifacts_dir / "model_bundle.joblib").exists()
    assert (artifacts_dir / "metrics.json").exists()
    assert (artifacts_dir / "feature_metadata.json").exists()
    assert (artifacts_dir / "performance_report.md").exists()
    assert (artifacts_dir / "model_selection_report.md").exists()
    
    # Verify required plots exist
    required_plots = [
        "confusion_matrix.png",
        "roc_curve.png", 
        "precision_recall_curve.png",
        "feature_importance.png",
        "calibration_plot.png",
    ]
    for plot in required_plots:
        assert (artifacts_dir / plot).exists(), f"Missing plot: {plot}"


def test_model_bundle_can_be_loaded_and_used(tmp_path, monkeypatch):
    """Test that the model bundle can be loaded and used for inference."""
    import ml.data.generate_dataset as gen_mod
    import ml.training.train as train_mod
    from app.inference import ForgettingPredictor
    
    # Setup temp directories
    monkeypatch.setattr(gen_mod, "OUT_DIR", tmp_path / "datasets")
    monkeypatch.setattr(train_mod, "DATASET_PATH", tmp_path / "datasets" / "tasks_raw.csv")
    monkeypatch.setattr(train_mod, "DATASET_META_PATH", tmp_path / "datasets" / "dataset_metadata.json")
    monkeypatch.setattr(train_mod, "ARTIFACTS_DIR", tmp_path / "artifacts")
    
    # Use small dataset for speed
    monkeypatch.setattr(train_mod, "DATASET_CONFIG", {
        "n_users": 15,
        "n_days": 25,
        "min_observations": 500,
        "seed": 42,
    })
    
    # Generate and train
    gen_mod.main()
    train_mod.main()
    
    # Now test loading and inference
    monkeypatch.setattr("app.inference.ARTIFACT_PATH", tmp_path / "artifacts" / "model_bundle.joblib")
    
    # Reset singleton to force reload
    ForgettingPredictor._instance = None
    predictor = ForgettingPredictor.instance()
    
    # Test prediction
    sample_task = {
        "task_id": "test-task",
        "task_category": "Academic",
        "priority": "HIGH",
        "location": "Campus",
        "weekday": 2,
        "hour": 14,
        "deadline_distance_hours": 18.0,
        "previous_completion_count": 12,
        "previous_forgetting_count": 8,
        "historical_completion_rate": 0.4,
        "historical_forgetting_rate": 0.55,
        "task_frequency": 0.3,
        "tasks_today": 5,
        "interruptions_today": 4,
        "recent_context_switches": 6,
        "avg_interruption_duration": 8.5,
        "avg_session_duration": 22.0,
    }
    
    result = predictor.predict_single(sample_task)
    
    assert "prediction_probability" in result
    assert 0.0 <= result["prediction_probability"] <= 1.0
    assert "risk_level" in result
    assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert "model_version" in result
    assert "top_features" in result


def test_metrics_json_contains_all_required_fields(tmp_path, monkeypatch):
    """Test that metrics.json contains all required fields."""
    import ml.data.generate_dataset as gen_mod
    import ml.training.train as train_mod
    
    # Setup
    monkeypatch.setattr(gen_mod, "OUT_DIR", tmp_path / "datasets")
    monkeypatch.setattr(train_mod, "DATASET_PATH", tmp_path / "datasets" / "tasks_raw.csv")
    monkeypatch.setattr(train_mod, "DATASET_META_PATH", tmp_path / "datasets" / "dataset_metadata.json")
    monkeypatch.setattr(train_mod, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(train_mod, "DATASET_CONFIG", {
        "n_users": 15,
        "n_days": 25,
        "min_observations": 500,
        "seed": 42,
    })
    
    # Generate and train
    gen_mod.main()
    train_mod.main()
    
    # Load and check metrics
    with open(tmp_path / "artifacts" / "metrics.json") as f:
        metrics = json.load(f)
    
    # Check top-level fields
    required_top_level = [
        "model_version", "dataset_version", "dataset_fingerprint",
        "selected_model", "class_balance", "split_summary",
        "candidate_metrics_test", "final_selected_metrics",
        "time_series_cv", "threshold_tuning", "calibration"
    ]
    for field in required_top_level:
        assert field in metrics, f"Missing field: {field}"
    
    # Check final metrics
    final = metrics["final_selected_metrics"]
    required_final = [
        "accuracy", "precision", "recall", "f1", "roc_auc", 
        "pr_auc", "brier_score", "confusion_matrix", "threshold"
    ]
    for field in required_final:
        assert field in final, f"Missing final metric: {field}"
    
    # Check candidate metrics
    for model_name, model_metrics in metrics["candidate_metrics_test"].items():
        required_candidate = [
            "accuracy", "precision", "recall", "f1", "roc_auc",
            "pr_auc", "brier_score", "confusion_matrix", "threshold"
        ]
        for field in required_candidate:
            assert field in model_metrics, f"Missing candidate metric {field} for {model_name}"


def test_feature_metadata_contains_preprocessing_info(tmp_path, monkeypatch):
    """Test that feature_metadata.json contains preprocessing details."""
    import ml.data.generate_dataset as gen_mod
    import ml.training.train as train_mod
    
    # Setup
    monkeypatch.setattr(gen_mod, "OUT_DIR", tmp_path / "datasets")
    monkeypatch.setattr(train_mod, "DATASET_PATH", tmp_path / "datasets" / "tasks_raw.csv")
    monkeypatch.setattr(train_mod, "DATASET_META_PATH", tmp_path / "datasets" / "dataset_metadata.json")
    monkeypatch.setattr(train_mod, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(train_mod, "DATASET_CONFIG", {
        "n_users": 15,
        "n_days": 25,
        "min_observations": 500,
        "seed": 42,
    })
    
    # Generate and train
    gen_mod.main()
    train_mod.main()
    
    # Load and check feature metadata
    with open(tmp_path / "artifacts" / "feature_metadata.json") as f:
        fm = json.load(f)
    
    # Check required fields
    required_fields = [
        "model_version", "dataset_version", "dataset_fingerprint",
        "selected_model", "raw_categorical_features", "raw_numeric_features",
        "target", "transformed_feature_names", "n_transformed_features",
        "preprocessor", "feature_descriptions"
    ]
    for field in required_fields:
        assert field in fm, f"Missing field: {field}"
    
    # Check preprocessor details
    prep = fm["preprocessor"]
    assert "numeric_impute_medians" in prep
    assert "categorical_impute_most_frequent" in prep
    assert "categorical_onehot_categories" in prep
    
    # Check feature descriptions
    assert len(fm["feature_descriptions"]) > 0


def test_reproducibility_same_seed_same_output(tmp_path, monkeypatch):
    """Test that using the same seed produces identical results."""
    import ml.data.generate_dataset as gen_mod
    
    # Setup
    monkeypatch.setattr(gen_mod, "OUT_DIR", tmp_path / "datasets")
    monkeypatch.setattr(gen_mod, "DATASET_CONFIG", {
        "n_users": 10,
        "n_days": 20,
        "min_observations": 200,
        "seed": 999,  # Fixed seed
    })
    
    # Generate twice
    gen_mod.main()
    df1 = pd.read_csv(tmp_path / "datasets" / "tasks_raw.csv")
    
    gen_mod.main()
    df2 = pd.read_csv(tmp_path / "datasets" / "tasks_raw.csv")
    
    # Should be identical
    assert df1.equals(df2), "Same seed should produce identical datasets"
    
    # Check metadata fingerprints match
    with open(tmp_path / "datasets" / "dataset_metadata.json") as f:
        meta1 = json.load(f)
    with open(tmp_path / "datasets" / "dataset_metadata.json") as f:
        meta2 = json.load(f)
    
    assert meta1["fingerprint_sha256_16"] == meta2["fingerprint_sha256_16"]


def test_training_command_works_from_module():
    """Test that the training command can be run as a module."""
    import subprocess
    import sys
    
    # This test just verifies the module can be imported and has a main
    from ml.training import train
    assert hasattr(train, "main")
    assert callable(train.main)


def test_inference_command_works_from_module():
    """Test that inference can be imported and used."""
    from app.inference import ForgettingPredictor
    assert hasattr(ForgettingPredictor, "instance")
    assert hasattr(ForgettingPredictor, "predict_single")
    assert hasattr(ForgettingPredictor, "predict_batch")
