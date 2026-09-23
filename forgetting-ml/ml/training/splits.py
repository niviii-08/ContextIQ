"""
splits.py

Implements time-aware (chronological) splitting and time-series cross-validation.
Behavioural data is sequential per user: using a random shuffle split would
let the model train on a user's future behaviour and be evaluated on that
same user's past behaviour, which leaks information.

Strategy
--------
Global chronological split by date:
  - Train:      first ~70% of days
  - Validation: next ~15% of days
  - Test:       last ~15% of days

This means the model is always evaluated on behaviour that occurred AFTER
everything it was trained on, mirroring real deployment (predict tomorrow
using only data up to today).

Cross-validation:
  - Walk-forward (TimeSeriesSplit) across chronological windows on the
    training date range. This gives a more robust estimate of out-of-sample
    performance without violating the temporal ordering constraint.
"""

import sys
from pathlib import Path
from typing import List, Tuple, Generator

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from ml.training.config import SPLIT_CONFIG, CROSS_VALIDATION_CONFIG


def _assert_no_split_leakage(train_df, val_df, test_df, date_col="date") -> None:
    train_dates = set(train_df[date_col].unique())
    val_dates = set(val_df[date_col].unique())
    test_dates = set(test_df[date_col].unique())
    assert len(train_dates & val_dates) == 0, "Train/Val date overlap -> leakage"
    assert len(train_dates & test_dates) == 0, "Train/Test date overlap -> leakage"
    assert len(val_dates & test_dates) == 0, "Val/Test date overlap -> leakage"
    max_train = max(train_dates)
    min_val = min(val_dates)
    min_test = min(test_dates)
    assert max_train < min_val, f"Max train date {max_train} must be < min val date {min_val}"
    assert min_val < min_test, f"Min val date {min_val} must be < min test date {min_test}"

    train_users = set(train_df["user_id"].unique())
    val_users = set(val_df["user_id"].unique())
    test_users = set(test_df["user_id"].unique())
    shared_tv = train_users & val_users
    shared_tt = train_users & test_users
    assert len(shared_tv) > 0 and len(shared_tt) > 0, (
        "No user overlap between splits. This is not leakage (we want users to "
        "appear across time) but the synthetic generator may be misconfigured."
    )


def chronological_split(df: pd.DataFrame, date_col: str = "date",
                         train_frac: float = None, val_frac: float = None,
                         assert_no_leakage: bool = True):
    if train_frac is None:
        train_frac = SPLIT_CONFIG["train_frac"]
    if val_frac is None:
        val_frac = SPLIT_CONFIG["val_frac"]

    dates = sorted(df[date_col].unique())
    n = len(dates)
    train_end = int(n * train_frac)
    val_end = int(n * (train_frac + val_frac))

    train_dates = set(dates[:train_end])
    val_dates = set(dates[train_end:val_end])
    test_dates = set(dates[val_end:])

    train_df = df[df[date_col].isin(train_dates)].reset_index(drop=True)
    val_df = df[df[date_col].isin(val_dates)].reset_index(drop=True)
    test_df = df[df[date_col].isin(test_dates)].reset_index(drop=True)

    if assert_no_leakage:
        _assert_no_split_leakage(train_df, val_df, test_df, date_col)

    return train_df, val_df, test_df


def chronological_splits_summary(train_df, val_df, test_df, date_col="date") -> dict:
    def stats(df, name):
        return {
            "name": name,
            "n_rows": int(len(df)),
            "n_users": int(df["user_id"].nunique()),
            "date_min": df[date_col].min(),
            "date_max": df[date_col].max(),
            "forget_rate": float(df["forgotten"].mean()) if "forgotten" in df.columns else None,
        }
    return {
        "train": stats(train_df, "train"),
        "val": stats(val_df, "val"),
        "test": stats(test_df, "test"),
    }


def time_series_cv_splits(
    train_val_df: pd.DataFrame,
    date_col: str = "date",
    n_splits: int = None,
    gap: int = None,
) -> Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None]:
    if n_splits is None:
        n_splits = CROSS_VALIDATION_CONFIG["n_splits"]
    if gap is None:
        gap = CROSS_VALIDATION_CONFIG["gap"]

    dates = sorted(train_val_df[date_col].unique())
    n_dates = len(dates)

    if n_dates < n_splits + 1 + gap:
        raise ValueError(
            f"Not enough unique dates ({n_dates}) for {n_splits} CV splits with gap={gap}"
        )

    test_size = n_dates // (n_splits + 1)

    for i in range(n_splits):
        train_end_idx = test_size * (i + 1) - 1
        test_start_idx = train_end_idx + 1 + gap
        test_end_idx = test_start_idx + test_size
        if test_end_idx >= n_dates:
            test_end_idx = n_dates
            test_start_idx = max(test_start_idx, test_end_idx - test_size)
        train_dates = set(dates[:train_end_idx + 1])
        test_dates = set(dates[test_start_idx:test_end_idx])
        if len(train_dates) == 0 or len(test_dates) == 0:
            continue

        tr_df = train_val_df[train_val_df[date_col].isin(train_dates)].reset_index(drop=True)
        te_df = train_val_df[train_val_df[date_col].isin(test_dates)].reset_index(drop=True)
        if len(tr_df) == 0 or len(te_df) == 0:
            continue
        yield tr_df, te_df
