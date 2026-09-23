"""
Stage 6 — ML Dataset Export
=============================

Produces train/test splits from the feature matrix (Stage 5) and saves
them as Parquet files alongside a JSON feature schema.

Split strategy: TEMPORAL (not random)
--------------------------------------
The data is sorted by task created_at. The first (1 - test_fraction) of
tasks form the training set; the remaining form the test set.

Why temporal, not random?
  Using a random split with time-series behavioural data introduces leakage:
  a training example at time T+1 may have features computed using data from
  T+5 (if that test example is in the future). Temporal split guarantees
  the training set''s latest created_at < test set''s earliest created_at.

Outputs
-------
  data/ml/
    train.parquet          Feature matrix (train set, no target)
    train_labels.parquet   Target column only (train set)
    test.parquet           Feature matrix (test set, no target)
    test_labels.parquet    Target column only (test set)
    feature_schema.json    Column names, types, null rates, value ranges
    split_summary.json     Temporal boundaries, class balance, record counts
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Columns that are identifiers / metadata — excluded from the ML feature matrix
_META_COLS = {"task_id", "user_id", "created_at", "status", "will_forget", "task_location_pair"}

# Numeric feature columns (used for training)
_NUMERIC_FEATURES = [
    "previous_forgetting_count",
    "previous_completion_count",
    "completion_rate",
    "category_forgetting_rate",
    "location_forgetting_rate",
    "weekday_forgetting_rate",
    "hour_forgetting_rate",
    "task_frequency",
    "days_since_last_similar",
    "deadline_distance_hours",
    "priority",
    "tasks_today",
    "interruptions_today",
    "recent_context_switches",
    "avg_interruption_duration_s",
    "recovery_time_s",
    "daily_friction_score",
    "repeated_context_count",
    "forgetting_streak",
    "avg_session_duration_7d_s",
    "context_switch_rate_7d",
    "is_late_night",
    "is_repeated_context",
]

TARGET_COL = "will_forget"


def _build_feature_schema(train_df: pd.DataFrame) -> dict:
    """Describe each feature column: dtype, null_rate, min, max, mean."""
    schema = {}
    for col in train_df.columns:
        series = train_df[col]
        null_rate = round(float(series.isna().mean()), 4)
        entry: dict = {
            "dtype": str(series.dtype),
            "null_rate": null_rate,
        }
        if pd.api.types.is_numeric_dtype(series):
            vals = series.dropna()
            if not vals.empty:
                entry["min"] = float(vals.min())
                entry["max"] = float(vals.max())
                entry["mean"] = round(float(vals.mean()), 4)
        schema[col] = entry
    return schema


def export_ml_datasets(
    feature_df: pd.DataFrame,
    output_dir: str | Path = "data/ml",
    test_fraction: float = 0.2,
) -> dict:
    """
    Export train/test Parquet files and feature schema.

    Parameters
    ----------
    feature_df   : Output of pipeline/features.py generate_feature_matrix()
    output_dir   : Where to write files (default: data/ml/)
    test_fraction: Fraction of (chronologically later) tasks used as test set

    Returns
    -------
    dict with keys: train_path, test_path, n_train, n_test, n_features,
                    train_positive_rate, test_positive_rate, split_date
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if feature_df.empty:
        logger.error("export_ml_datasets: feature_df is empty — nothing to export")
        return {}

    # Sort chronologically for temporal split
    df = feature_df.copy()
    if "created_at" in df.columns:
        df = df.sort_values("created_at").reset_index(drop=True)

    n = len(df)
    split_idx = int(n * (1 - test_fraction))
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    split_date = None
    if "created_at" in test_df.columns and not test_df.empty:
        split_ts = test_df["created_at"].iloc[0]
        if hasattr(split_ts, "isoformat"):
            split_date = split_ts.isoformat()

    # Select feature columns (numeric only for ML)
    avail_features = [c for c in _NUMERIC_FEATURES if c in df.columns]
    missing_features = [c for c in _NUMERIC_FEATURES if c not in df.columns]
    if missing_features:
        logger.warning("export_ml_datasets: missing features (will be skipped): %s", missing_features)

    train_X = train_df[avail_features]
    train_y = train_df[[TARGET_COL]] if TARGET_COL in train_df.columns else pd.DataFrame()
    test_X = test_df[avail_features]
    test_y = test_df[[TARGET_COL]] if TARGET_COL in test_df.columns else pd.DataFrame()

    # Save Parquet
    train_path = out / "train.parquet"
    test_path = out / "test.parquet"
    train_X.to_parquet(train_path, index=False)
    train_y.to_parquet(out / "train_labels.parquet", index=False)
    test_X.to_parquet(test_path, index=False)
    test_y.to_parquet(out / "test_labels.parquet", index=False)
    logger.info("export_ml_datasets: saved train.parquet (%d rows) and test.parquet (%d rows)", len(train_X), len(test_X))

    # Feature schema
    schema = _build_feature_schema(train_X)
    schema_path = out / "feature_schema.json"
    schema_path.write_text(json.dumps(schema, indent=2))

    # Summary
    train_pos = float(train_y[TARGET_COL].mean()) if not train_y.empty else 0.0
    test_pos = float(test_y[TARGET_COL].mean()) if not test_y.empty else 0.0

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "All data is SYNTHETIC — generated for development/demo purposes only.",
        "n_train": len(train_X),
        "n_test": len(test_X),
        "n_features": len(avail_features),
        "feature_names": avail_features,
        "target_column": TARGET_COL,
        "split_strategy": "temporal",
        "test_fraction": test_fraction,
        "split_date": split_date,
        "train_positive_rate": round(train_pos, 4),
        "test_positive_rate": round(test_pos, 4),
        "missing_features": missing_features,
    }
    (out / "split_summary.json").write_text(json.dumps(summary, indent=2))

    logger.info(
        "export_ml_datasets: train positive rate=%.1f%%, test positive rate=%.1f%%",
        100 * train_pos, 100 * test_pos,
    )
    return summary
