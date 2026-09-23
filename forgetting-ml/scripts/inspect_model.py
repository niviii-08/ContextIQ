"""
inspect_model.py

A recruiter-friendly command-line tool to inspect trained model artifacts.
This provides an easy way to understand what's in the model bundle without
needing to write code.

Usage:
    python scripts/inspect_model.py                    # Summary overview
    python scripts/inspect_model.py --features          # Feature details
    python scripts/inspect_model.py --metrics           # Performance metrics
    python scripts/inspect_model.py --preprocessing     # Preprocessing details
    python scripts/inspect_model.py --full              # Everything
"""

import argparse
import json
import sys
from pathlib import Path

import joblib

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts"


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_key_value(key: str, value: any, indent: int = 0):
    prefix = "  " * indent
    if isinstance(value, (dict, list)):
        print(f"{prefix}{key}:")
        if isinstance(value, dict):
            for k, v in value.items():
                print_key_value(k, v, indent + 1)
        else:
            for i, item in enumerate(value):
                print_key_value(f"[{i}]", item, indent + 1)
    else:
        print(f"{prefix}{key}: {value}")


def inspect_bundle_summary(bundle_path: Path):
    """Print a high-level summary of the model bundle."""
    print_section("MODEL BUNDLE SUMMARY")
    
    bundle = joblib.load(bundle_path)
    
    print_key_value("Model Name", bundle.get("model_name"))
    print_key_value("Model Version", bundle.get("model_version"))
    print_key_value("Calibrated", bundle.get("calibrated"))
    print_key_value("Calibration Method", bundle.get("calibration_method"))
    print_key_value("Decision Threshold", bundle.get("threshold"))
    
    print(f"\nModel Type: {bundle.get('model_name')}")
    print(f"Number of raw features: {len(bundle.get('feature_names_raw', []))}")
    print(f"Number of transformed features: {len(bundle.get('feature_names_transformed', []))}")
    print(f"Categorical features: {len(bundle.get('categorical_features', []))}")
    print(f"Numeric features: {len(bundle.get('numeric_features', []))}")


def inspect_features(bundle_path: Path, metadata_path: Path):
    """Print detailed feature information."""
    print_section("FEATURE DETAILS")
    
    bundle = joblib.load(bundle_path)
    
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    print("\nRaw Features:")
    print("  Categorical:")
    for feat in bundle.get("categorical_features", []):
        print(f"    - {feat}")
    
    print("  Numeric:")
    for feat in bundle.get("numeric_features", []):
        print(f"    - {feat}")
    
    print(f"\nTransformed Features (total: {len(bundle.get('feature_names_transformed', []))}):")
    for feat in bundle.get("feature_names_transformed", [])[:10]:
        print(f"    - {feat}")
    if len(bundle.get("feature_names_transformed", [])) > 10:
        print(f"    ... and {len(bundle.get('feature_names_transformed', [])) - 10} more")
    
    print("\nFeature Descriptions:")
    descriptions = metadata.get("feature_descriptions", {})
    for feat, desc in descriptions.items():
        print(f"  {feat}: {desc}")


def inspect_preprocessing(bundle_path: Path, metadata_path: Path):
    """Print preprocessing pipeline details."""
    print_section("PREPROCESSING PIPELINE")
    
    bundle = joblib.load(bundle_path)
    
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    preprocessor_meta = metadata.get("preprocessor", {})
    
    print("Numeric Imputation (median values):")
    for feat, val in preprocessor_meta.get("numeric_impute_medians", {}).items():
        print(f"  {feat}: {val:.4f}")
    
    print("\nNumeric Standardization (if applied):")
    scaler_means = preprocessor_meta.get("numeric_standard_scaler_means", {})
    if scaler_means:
        for feat, val in scaler_means.items():
            print(f"  {feat}: mean={val:.4f}")
    
    print("\nCategorical Imputation (most frequent):")
    feat = preprocessor_meta.get("categorical_impute_most_frequent", {})
    for feat, val in feat.items():
        print(f"  {feat}: {val}")
    
    print("\nOne-Hot Encoding Categories:")
    categories = preprocessor_meta.get("categorical_onehot_categories", {})
    for feat, cats in categories.items():
        print(f"  {feat}: {', '.join(cats)}")


def inspect_metrics(metrics_path: Path):
    """Print performance metrics."""
    print_section("PERFORMANCE METRICS")
    
    with open(metrics_path) as f:
        metrics = json.load(f)
    
    print("Dataset Information:")
    print_key_value("Model Version", metrics.get("model_version"))
    print_key_value("Dataset Version", metrics.get("dataset_version"))
    print_key_value("Dataset Fingerprint", metrics.get("dataset_fingerprint"))
    
    print("\nClass Balance:")
    for cls, rate in metrics.get("class_balance", {}).items():
        print(f"  Class {cls}: {rate:.2%}")
    
    print("\nSelected Model:")
    print_key_value("Model", metrics.get("selected_model"))
    
    final_metrics = metrics.get("final_selected_metrics", {})
    print("\nFinal Model Performance (Test Set):")
    print_key_value("Accuracy", final_metrics.get("accuracy"))
    print_key_value("Precision", final_metrics.get("precision"))
    print_key_value("Recall", final_metrics.get("recall"))
    print_key_value("F1 Score", final_metrics.get("f1"))
    print_key_value("ROC-AUC", final_metrics.get("roc_auc"))
    print_key_value("PR-AUC", final_metrics.get("pr_auc"))
    print_key_value("Brier Score", final_metrics.get("brier_score"))
    print_key_value("Decision Threshold", final_metrics.get("threshold"))
    
    print("\nCalibration:")
    print_key_value("Calibration Applied", final_metrics.get("calibration_applied"))
    print_key_value("Calibration Method", final_metrics.get("calibration_method"))
    
    print("\nAll Candidate Models (Test Set):")
    candidates = metrics.get("candidate_metrics_test", {})
    print(f"{'Model':<25} {'PR-AUC':<10} {'ROC-AUC':<10} {'F1':<10} {'Accuracy':<10}")
    print("-" * 65)
    for name, m in candidates.items():
        marker = "*" if name == metrics.get("selected_model") else ""
        print(f"{name:<25} {m.get('pr_auc', 0):<10.4f} {m.get('roc_auc', 0):<10.4f} "
              f"{m.get('f1', 0):<10.4f} {m.get('accuracy', 0):<10.4f} {marker}")
    
    print("\nCross-Validation Summary:")
    cv = metrics.get("time_series_cv", {})
    for model_name, cv_summary in cv.items():
        print(f"\n{model_name}:")
        if "pr_auc" in cv_summary:
            pra = cv_summary["pr_auc"]
            print(f"  PR-AUC: {pra['mean']:.4f} ± {pra['std']:.4f} (n={pra['n_folds']})")
        if "roc_auc" in cv_summary:
            roca = cv_summary["roc_auc"]
            print(f"  ROC-AUC: {roca['mean']:.4f} ± {roca['std']:.4f}")


def inspect_all(bundle_path: Path, metadata_path: Path, metrics_path: Path):
    """Print all inspection information."""
    inspect_bundle_summary(bundle_path)
    inspect_features(bundle_path, metadata_path)
    inspect_preprocessing(bundle_path, metadata_path)
    inspect_metrics(metrics_path)
    
    print_section("ARTIFACT INVENTORY")
    print("Available artifacts in artifacts/:")
    for artifact in ARTIFACTS_DIR.iterdir():
        if artifact.is_file():
            size_kb = artifact.stat().st_size / 1024
            print(f"  {artifact.name} ({size_kb:.1f} KB)")


def main():
    parser = argparse.ArgumentParser(description="Inspect trained model artifacts")
    parser.add_argument("--features", action="store_true", help="Show feature details")
    parser.add_argument("--metrics", action="store_true", help="Show performance metrics")
    parser.add_argument("--preprocessing", action="store_true", help="Show preprocessing details")
    parser.add_argument("--full", action="store_true", help="Show all information")
    
    args = parser.parse_args()
    
    bundle_path = ARTIFACTS_DIR / "model_bundle.joblib"
    metadata_path = ARTIFACTS_DIR / "feature_metadata.json"
    metrics_path = ARTIFACTS_DIR / "metrics.json"
    
    if not bundle_path.exists():
        print(f"Error: Model bundle not found at {bundle_path}")
        print("Run `python -m ml.training.train` first.")
        sys.exit(1)
    
    if args.full:
        inspect_all(bundle_path, metadata_path, metrics_path)
    elif args.features:
        if not metadata_path.exists():
            print(f"Error: Feature metadata not found at {metadata_path}")
            sys.exit(1)
        inspect_features(bundle_path, metadata_path)
    elif args.metrics:
        if not metrics_path.exists():
            print(f"Error: Metrics not found at {metrics_path}")
            sys.exit(1)
        inspect_metrics(metrics_path)
    elif args.preprocessing:
        if not metadata_path.exists():
            print(f"Error: Feature metadata not found at {metadata_path}")
            sys.exit(1)
        inspect_preprocessing(bundle_path, metadata_path)
    else:
        inspect_bundle_summary(bundle_path)


if __name__ == "__main__":
    main()
