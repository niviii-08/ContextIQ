"""
Stage 7 — Model Training and Evaluation
=========================================

Trains and evaluates forgetting prediction models on the ML-ready
Parquet dataset produced in Stage 6.

Models trained
--------------
1. Logistic Regression (baseline — linear, fast, interpretable)
2. Random Forest       (ensemble — handles non-linearities, feature importance)

Preprocessing pipeline
----------------------
- Numeric features: median imputation + standard scaling
- No categorical features in the numeric feature set (task_location_pair
  is a string key kept for analysis but excluded from training)

Evaluation metrics
------------------
- Accuracy, Precision, Recall, F1 (macro + weighted)
- ROC-AUC
- Confusion Matrix
- SHAP feature importance (summary for Random Forest)

Output files (data/ml/models/)
-------------------------------
  logistic_regression.joblib   Trained LR pipeline
  random_forest.joblib         Trained RF pipeline
  evaluation_report.json       All metrics for both models
  shap_importance.csv          Mean |SHAP| per feature (RF model)

IMPORTANT
---------
All models are trained on SYNTHETIC data. They are NOT suitable for
production use with real user data. Their purpose is to demonstrate
the end-to-end ML pipeline structure and feature engineering quality.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _load_data(ml_dir: Path) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """Load train/test feature matrices and label series."""
    train_X = pd.read_parquet(ml_dir / "train.parquet")
    train_y = pd.read_parquet(ml_dir / "train_labels.parquet").squeeze()
    test_X = pd.read_parquet(ml_dir / "test.parquet")
    test_y = pd.read_parquet(ml_dir / "test_labels.parquet").squeeze()
    return train_X, train_y, test_X, test_y


def _build_pipeline(model):
    """Wrap a sklearn estimator in an impute+scale pipeline."""
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.impute import SimpleImputer

    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", model),
    ])


def _evaluate(name: str, pipeline, test_X: pd.DataFrame, test_y: pd.Series) -> dict:
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score,
        f1_score, roc_auc_score, confusion_matrix,
    )
    preds = pipeline.predict(test_X)
    proba = None
    try:
        proba = pipeline.predict_proba(test_X)[:, 1]
    except AttributeError:
        pass

    cm = confusion_matrix(test_y, preds).tolist()
    result = {
        "model": name,
        "accuracy": round(float(accuracy_score(test_y, preds)), 4),
        "precision_macro": round(float(precision_score(test_y, preds, average="macro", zero_division=0)), 4),
        "recall_macro": round(float(recall_score(test_y, preds, average="macro", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(test_y, preds, average="macro", zero_division=0)), 4),
        "f1_weighted": round(float(f1_score(test_y, preds, average="weighted", zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(test_y, proba)), 4) if proba is not None else None,
        "confusion_matrix": cm,
    }
    logger.info(
        "%s → acc=%.3f, f1_w=%.3f, roc_auc=%s",
        name, result["accuracy"], result["f1_weighted"],
        f"{result['roc_auc']:.3f}" if result["roc_auc"] is not None else "N/A",
    )
    return result


def _shap_importance(pipeline, train_X: pd.DataFrame, feature_names: list[str], out_path: Path) -> None:
    """Compute mean absolute SHAP values for Random Forest. Saves CSV."""
    try:
        import shap
        # Transform data through imputer/scaler but not the model step
        X_transformed = pipeline[:-1].transform(train_X)
        explainer = shap.TreeExplainer(pipeline.named_steps["model"])
        # Use a subsample for speed (max 500 rows)
        n_sample = min(500, len(X_transformed))
        shap_values = explainer.shap_values(X_transformed[:n_sample])
        # shap_values may be a list (multi-class) or 2D array (binary)
        if isinstance(shap_values, list):
            vals = shap_values[1]  # positive class
        else:
            vals = shap_values
        mean_abs = np.abs(vals).mean(axis=0)
        importance_df = pd.DataFrame({
            "feature": feature_names,
            "mean_abs_shap": mean_abs.round(6),
        }).sort_values("mean_abs_shap", ascending=False)
        importance_df.to_csv(out_path, index=False)
        logger.info("SHAP importance saved to %s", out_path)
    except Exception as exc:
        logger.warning("SHAP computation skipped: %s", exc)


def train_and_evaluate(
    ml_dir: str | Path = "data/ml",
    models_dir: str | Path = "data/ml/models",
) -> dict:
    """
    Train both models, evaluate, and save artifacts.

    Returns
    -------
    dict with evaluation results for both models.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier

    ml_path = Path(ml_dir)
    models_path = Path(models_dir)
    models_path.mkdir(parents=True, exist_ok=True)

    train_X, train_y, test_X, test_y = _load_data(ml_path)
    feature_names = list(train_X.columns)

    logger.info(
        "train_and_evaluate: train=%d, test=%d, features=%d, "
        "train_positive=%.1f%%, test_positive=%.1f%%",
        len(train_X), len(test_X), len(feature_names),
        100 * float(train_y.mean()), 100 * float(test_y.mean()),
    )

    results = []

    # ── 1. Logistic Regression ────────────────────────────────────────────────
    lr = _build_pipeline(LogisticRegression(
        max_iter=1000, class_weight="balanced", random_state=42,
    ))
    lr.fit(train_X, train_y)
    lr_result = _evaluate("LogisticRegression", lr, test_X, test_y)
    results.append(lr_result)
    joblib.dump(lr, models_path / "logistic_regression.joblib")
    logger.info("Logistic Regression model saved")

    # ── 2. Random Forest ──────────────────────────────────────────────────────
    rf = _build_pipeline(RandomForestClassifier(
        n_estimators=200, max_depth=8, class_weight="balanced",
        random_state=42, n_jobs=-1,
    ))
    rf.fit(train_X, train_y)
    rf_result = _evaluate("RandomForest", rf, test_X, test_y)
    results.append(rf_result)
    joblib.dump(rf, models_path / "random_forest.joblib")
    logger.info("Random Forest model saved")

    # SHAP importance for RF
    _shap_importance(rf, train_X, feature_names, models_path / "shap_importance.csv")

    # ── Save evaluation report ────────────────────────────────────────────────
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "All models trained on SYNTHETIC data. Not for production use.",
        "feature_names": feature_names,
        "n_train": len(train_X),
        "n_test": len(test_X),
        "models": results,
    }
    report_path = models_path / "evaluation_report.json"
    report_path.write_text(json.dumps(report, indent=2))
    logger.info("Evaluation report saved to %s", report_path)

    # ── Print summary table ───────────────────────────────────────────────────
    try:
        from tabulate import tabulate
        table_data = [
            [r["model"], r["accuracy"], r["f1_weighted"], r["roc_auc"] or "N/A"]
            for r in results
        ]
        print("\n" + tabulate(
            table_data,
            headers=["Model", "Accuracy", "F1 (weighted)", "ROC-AUC"],
            tablefmt="github",
            floatfmt=".4f",
        ))
    except ImportError:
        for r in results:
            print(f"  {r['model']}: acc={r['accuracy']:.4f} f1={r['f1_weighted']:.4f}")

    return report
