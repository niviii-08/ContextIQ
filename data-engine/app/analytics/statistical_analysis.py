"""
Statistical Analysis for Behavioral Data
=========================================

Provides statistical analysis including distributions, correlations,
confidence indicators, and trend analysis without inventing statistical significance.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from scipy import stats


def compute_distribution_statistics(
    series: pd.Series,
    sample_size_threshold: int = 30
) -> Dict[str, any]:
    """
    Compute distribution statistics for a numerical series.
    
    Returns: mean, median, std, min, max, quartiles, sample size
    Includes confidence indicators based on sample size.
    """
    if series.empty or series.dropna().empty:
        return {"error": "Empty series"}
    
    clean_series = series.dropna()
    n = len(clean_series)
    
    stats_dict = {
        "count": n,
        "mean": float(clean_series.mean()),
        "median": float(clean_series.median()),
        "std": float(clean_series.std()) if n > 1 else 0.0,
        "min": float(clean_series.min()),
        "max": float(clean_series.max()),
        "q25": float(clean_series.quantile(0.25)),
        "q75": float(clean_series.quantile(0.75)),
        "iqr": float(clean_series.quantile(0.75) - clean_series.quantile(0.25)),
    }
    
    # Sample size confidence indicator
    if n >= sample_size_threshold:
        stats_dict["sample_confidence"] = "HIGH"
    elif n >= 10:
        stats_dict["sample_confidence"] = "MEDIUM"
    else:
        stats_dict["sample_confidence"] = "LOW"
    
    return stats_dict


def compute_correlation_matrix(
    df: pd.DataFrame,
    numeric_columns: List[str],
    method: str = "pearson"
) -> Dict[str, any]:
    """
    Compute correlation matrix for specified numeric columns.
    
    Returns: correlation matrix, sample sizes, confidence indicators
    Does NOT claim statistical significance - only reports correlations.
    """
    if df.empty or not numeric_columns:
        return {"error": "Insufficient data"}
    
    # Filter to available columns
    available_cols = [col for col in numeric_columns if col in df.columns]
    if len(available_cols) < 2:
        return {"error": "Need at least 2 numeric columns"}
    
    clean_df = df[available_cols].dropna()
    if clean_df.empty:
        return {"error": "No complete cases"}
    
    n = len(clean_df)
    
    # Compute correlation
    corr_matrix = clean_df.corr(method=method)
    
    # Convert to dict format
    correlations = {}
    for i, col1 in enumerate(available_cols):
        for j, col2 in enumerate(available_cols):
            if i < j:  # Only upper triangle
                corr_val = corr_matrix.iloc[i, j]
                correlations[f"{col1}_vs_{col2}"] = {
                    "correlation": round(float(corr_val), 4),
                    "sample_size": n,
                }
    
    # Sample size confidence
    if n >= 50:
        confidence = "HIGH"
    elif n >= 20:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    return {
        "correlations": correlations,
        "sample_size": n,
        "sample_confidence": confidence,
        "method": method,
    }


def compute_trend_analysis(
    series: pd.Series,
    dates: pd.Series,
    min_points: int = 5
) -> Dict[str, any]:
    """
    Compute trend analysis for time series data.
    
    Returns: slope, intercept, r_squared, trend direction, confidence
    Uses linear regression without claiming statistical significance.
    """
    if series.empty or dates.empty or len(series) != len(dates):
        return {"error": "Invalid input"}
    
    clean_df = pd.DataFrame({"date": dates, "value": series}).dropna()
    if len(clean_df) < min_points:
        return {"error": f"Insufficient data points (need {min_points}, have {len(clean_df)})"}
    
    # Convert dates to numeric (days since first date)
    clean_df["date_numeric"] = (clean_df["date"] - clean_df["date"].min()).dt.total_seconds() / 86400.0
    
    x = clean_df["date_numeric"].values
    y = clean_df["value"].values
    
    # Linear regression
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    
    # R-squared
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    # Trend direction
    if abs(slope) < 1e-10:
        direction = "STABLE"
    elif slope > 0:
        direction = "INCREASING"
    else:
        direction = "DECREASING"
    
    # Confidence based on sample size and R-squared
    n = len(clean_df)
    if n >= 20 and r_squared > 0.3:
        confidence = "HIGH"
    elif n >= 10 and r_squared > 0.1:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_squared),
        "trend_direction": direction,
        "sample_size": n,
        "confidence": confidence,
        "period_days": float(x.max() - x.min()),
    }


def compute_distribution_comparison(
    series1: pd.Series,
    series2: pd.Series,
    name1: str = "group1",
    name2: str = "group2"
) -> Dict[str, any]:
    """
    Compare distributions between two groups.
    
    Returns: descriptive statistics for each group, difference in means
    Does NOT claim statistical significance - only descriptive comparison.
    """
    stats1 = compute_distribution_statistics(series1)
    stats2 = compute_distribution_statistics(series2)
    
    if "error" in stats1 or "error" in stats2:
        return {"error": "Insufficient data for comparison"}
    
    mean_diff = stats1["mean"] - stats2["mean"]
    median_diff = stats1["median"] - stats2["median"]
    
    # Effect size (Cohen's d)
    pooled_std = np.sqrt((stats1["std"]**2 + stats2["std"]**2) / 2)
    cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0.0
    
    return {
        name1: stats1,
        name2: stats2,
        "mean_difference": round(float(mean_diff), 4),
        "median_difference": round(float(median_diff), 4),
        "cohens_d": round(float(cohens_d), 4),
        "effect_size_interpretation": _interpret_cohens_d(cohens_d),
    }


def _interpret_cohens_d(d: float) -> str:
    """Interpret Cohen's d effect size (conventional thresholds)."""
    abs_d = abs(d)
    if abs_d < 0.2:
        return "NEGLIGIBLE"
    elif abs_d < 0.5:
        return "SMALL"
    elif abs_d < 0.8:
        return "MEDIUM"
    else:
        return "LARGE"


def compute_percentile_ranks(
    series: pd.Series,
    value: float
) -> Dict[str, any]:
    """
    Compute percentile rank of a value within a distribution.
    
    Returns: percentile rank, interpretation
    """
    if series.empty:
        return {"error": "Empty series"}
    
    clean_series = series.dropna()
    n = len(clean_series)
    
    if n == 0:
        return {"error": "No valid data"}
    
    percentile = (clean_series < value).sum() / n * 100
    
    if percentile < 25:
        interpretation = "LOW"
    elif percentile < 50:
        interpretation = "BELOW_AVERAGE"
    elif percentile < 75:
        interpretation = "ABOVE_AVERAGE"
    else:
        interpretation = "HIGH"
    
    return {
        "value": value,
        "percentile_rank": round(percentile, 2),
        "interpretation": interpretation,
        "sample_size": n,
    }


def compute_moving_averages(
    series: pd.Series,
    dates: pd.Series,
    windows: List[int] = [7, 14, 30]
) -> Dict[str, any]:
    """
    Compute moving averages for time series data.
    
    Returns: moving averages for specified windows
    """
    if series.empty or dates.empty:
        return {"error": "Insufficient data"}
    
    df = pd.DataFrame({"date": dates, "value": series}).dropna()
    df = df.sort_values("date")
    
    result = {"original_data": len(df)}
    
    for window in windows:
        if len(df) >= window:
            ma = df["value"].rolling(window=window, min_periods=1).mean()
            result[f"ma_{window}"] = {
                "values": ma.tolist(),
                "dates": df["date"].dt.strftime("%Y-%m-%d").tolist(),
                "latest": round(float(ma.iloc[-1]), 4),
            }
        else:
            result[f"ma_{window}"] = {"error": f"Insufficient data for {window}-day window"}
    
    return result


def compute_outlier_detection(
    series: pd.Series,
    method: str = "iqr",
    iqr_multiplier: float = 1.5
) -> Dict[str, any]:
    """
    Detect outliers in a numerical series.
    
    Returns: outlier values, indices, and statistics
    Methods: 'iqr' (interquartile range) or 'zscore' (z-score)
    """
    if series.empty:
        return {"error": "Empty series"}
    
    clean_series = series.dropna()
    if clean_series.empty:
        return {"error": "No valid data"}
    
    if method == "iqr":
        q1 = clean_series.quantile(0.25)
        q3 = clean_series.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - iqr_multiplier * iqr
        upper_bound = q3 + iqr_multiplier * iqr
        
        outliers = clean_series[(clean_series < lower_bound) | (clean_series > upper_bound)]
        
    elif method == "zscore":
        mean = clean_series.mean()
        std = clean_series.std()
        
        if std == 0:
            return {"error": "Zero standard deviation"}
        
        z_scores = np.abs((clean_series - mean) / std)
        outliers = clean_series[z_scores > iqr_multiplier]
        
    else:
        return {"error": f"Unknown method: {method}"}
    
    outlier_indices = outliers.index.tolist()
    outlier_values = outliers.tolist()
    
    return {
        "method": method,
        "outlier_count": len(outliers),
        "outlier_percentage": round(len(outliers) / len(clean_series) * 100, 2),
        "outlier_values": [float(v) for v in outlier_values],
        "outlier_indices": outlier_indices,
        "total_values": len(clean_series),
    }


def compute_category_association_strength(
    df: pd.DataFrame,
    category_col: str,
    target_col: str
) -> Dict[str, any]:
    """
    Compute association strength between categorical variables.
    
    Returns: normalized mutual information approximation, contingency table
    Does NOT claim statistical significance - only descriptive association.
    """
    if df.empty or category_col not in df.columns or target_col not in df.columns:
        return {"error": "Invalid columns"}
    
    clean_df = df[[category_col, target_col]].dropna()
    if clean_df.empty:
        return {"error": "No valid data"}
    
    # Contingency table
    contingency = pd.crosstab(clean_df[category_col], clean_df[target_col])
    
    # Normalized association strength (Cramer's V approximation for binary target)
    n = len(clean_df)
    chi2 = 0.0
    
    for i in contingency.index:
        for j in contingency.columns:
            observed = contingency.loc[i, j]
            expected = (contingency.loc[i].sum() * contingency[j].sum()) / n
            if expected > 0:
                chi2 += (observed - expected) ** 2 / expected
    
    # Cramer's V
    min_dim = min(contingency.shape[0] - 1, contingency.shape[1] - 1)
    cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 and n > 0 else 0.0
    
    return {
        "association_strength": round(float(cramers_v), 4),
        "contingency_table": contingency.to_dict(),
        "sample_size": n,
        "interpretation": _interpret_association(cramers_v),
    }


def _interpret_association(v: float) -> str:
    """Interpret Cramer's V association strength."""
    if v < 0.1:
        return "NEGLIGIBLE"
    elif v < 0.3:
        return "WEAK"
    elif v < 0.5:
        return "MODERATE"
    else:
        return "STRONG"
