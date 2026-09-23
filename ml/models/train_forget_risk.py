"""
Train a forget-risk classifier — Phase 1 ML model.

Reads the feature table from ml/features/build_features.py and trains a
gradient-boosted classifier (XGBoost) predicting P(task gets forgotten).
Saves the fitted model + a feature importance report.

Usage:
    python ml/features/build_features.py
    python ml/models/train_forget_risk.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

CATEGORICAL = ["priority", "location_type", "context_tag"]
NUMERIC = [
    "created_hour", "is_late_night", "is_weekend", "event_count",
    "pause_resume_count", "nearby_interruptions", "estimated_minutes",
]
TARGET = "is_forgotten"


def train(features_path: Path, model_dir: Path) -> None:
    df = pd.read_csv(features_path)
    df["estimated_minutes"] = df["estimated_minutes"].fillna(df["estimated_minutes"].median())
    df["context_tag"] = df["context_tag"].fillna("none")

    X = df[CATEGORICAL + NUMERIC]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    preprocessor = ColumnTransformer(
        transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)],
        remainder="passthrough",
    )

    model = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            (
                "classifier",
                XGBClassifier(
                    n_estimators=200,
                    max_depth=4,
                    learning_rate=0.08,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    eval_metric="logloss",
                    random_state=42,
                ),
            ),
        ]
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    report = classification_report(y_test, y_pred, output_dict=True)
    try:
        auc = roc_auc_score(y_test, y_proba)
    except ValueError:
        auc = None  # only one class present in a tiny demo split

    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "forget_risk_xgb.joblib"
    joblib.dump(model, model_path)

    metrics = {"roc_auc": auc, "classification_report": report, "n_train": len(X_train), "n_test": len(X_test)}
    with open(model_dir / "forget_risk_xgb_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2, default=float)

    print(f"Model saved to {model_path}")
    print(f"ROC-AUC: {auc}")
    print(json.dumps(report, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the forget-risk classifier")
    parser.add_argument(
        "--features", type=Path,
        default=Path(__file__).resolve().parents[2] / "data" / "features_forget_risk.csv",
    )
    parser.add_argument(
        "--model-dir", type=Path,
        default=Path(__file__).resolve().parent / "artifacts",
    )
    args = parser.parse_args()
    train(args.features, args.model_dir)


if __name__ == "__main__":
    main()
