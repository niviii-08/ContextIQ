"""
analytics.py
============
Small deterministic statistics helpers built on pandas/numpy.

IMPORTANT: nothing here predicts anything. These are plain descriptive
statistics (slope of a best-fit line, simple aggregation) computed over
values that already exist in the structured input. This is data wrangling,
not machine learning — no model is fit to make a forecast, and no output of
this module is treated as a probability or prediction.
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np
import pandas as pd

from app.schemas import BehaviourMetric


def metrics_to_dataframe(metrics: List[BehaviourMetric]) -> pd.DataFrame:
    """Convert a flat list of BehaviourMetric into a tidy DataFrame.

    Columns: metric_name, value, period. Never invents rows — one row per
    input metric, verbatim.
    """
    if not metrics:
        return pd.DataFrame(columns=["metric_name", "value", "period"])
    return pd.DataFrame([m.model_dump() for m in metrics])


def compute_trend_slope(values: List[float]) -> Optional[float]:
    """Deterministic least-squares slope of `values` against their index
    (0, 1, 2, ...). Returns None if fewer than two points are available.

    This is descriptive statistics only (numpy.polyfit degree-1 fit over
    already-observed values) — not a forecast or prediction of future
    values.
    """
    if len(values) < 2:
        return None
    x = np.arange(len(values), dtype=float)
    y = np.asarray(values, dtype=float)
    slope, _intercept = np.polyfit(x, y, deg=1)
    return round(float(slope), 4)


def summarize_metric_series(metrics: List[BehaviourMetric], metric_name: str) -> dict:
    """Return count/mean/min/max/slope for a named metric series, computed
    directly from the input rows via pandas/numpy. All values are
    reproducible aggregates of the input — nothing is invented or forecast.
    """
    df = metrics_to_dataframe(metrics)
    if df.empty or metric_name not in set(df["metric_name"]):
        return {
            "metric_name": metric_name,
            "count": 0,
            "mean": None,
            "min": None,
            "max": None,
            "slope": None,
        }

    series = df[df["metric_name"] == metric_name]["value"]
    values = series.tolist()
    return {
        "metric_name": metric_name,
        "count": int(series.count()),
        "mean": round(float(series.mean()), 4),
        "min": round(float(series.min()), 4),
        "max": round(float(series.max()), 4),
        "slope": compute_trend_slope(values),
    }
