"""
Feature engineering — Phase 1: forget-risk features.

Reads the CSVs produced by scripts/generate_synthetic_data.py (or a real
export from Postgres in the same shape) and builds a single task-level
feature table suitable for training a forget-risk classifier.

Usage:
    python ml/features/build_features.py --data-dir data --out data/features_forget_risk.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def load_raw(data_dir: Path) -> dict[str, pd.DataFrame]:
    return {
        "tasks": pd.read_csv(data_dir / "tasks.csv", parse_dates=["due_at", "created_at", "completed_at"]),
        "events": pd.read_csv(data_dir / "task_events.csv", parse_dates=["occurred_at"]),
        "interruptions": pd.read_csv(data_dir / "interruptions.csv", parse_dates=["occurred_at"]),
        "locations": pd.read_csv(data_dir / "locations.csv"),
    }


def build_forget_risk_features(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    tasks = raw["tasks"].copy()
    events = raw["events"].copy()
    interruptions = raw["interruptions"].copy()
    locations = raw["locations"].copy()

    # --- time-based features from CREATED event ---
    created = events[events["event_type"] == "CREATED"][["task_id", "occurred_at"]].rename(
        columns={"occurred_at": "created_ts"}
    )
    started = events[events["event_type"] == "STARTED"][["task_id", "occurred_at"]].rename(
        columns={"occurred_at": "started_ts"}
    )

    df = tasks.merge(created, left_on="id", right_on="task_id", how="left")
    df = df.merge(started, on="task_id", how="left")

    df["created_hour"] = df["created_ts"].dt.hour
    df["is_late_night"] = (df["created_hour"] >= 21) | (df["created_hour"] <= 4)
    df["is_weekend"] = df["created_ts"].dt.dayofweek >= 5

    # --- context features ---
    df = df.merge(
        locations[["id", "location_type"]].rename(columns={"id": "context_location_id"}),
        on="context_location_id",
        how="left",
    )
    df["location_type"] = df["location_type"].fillna("NONE")

    # --- event-count features (context switching proxy) ---
    event_counts = events.groupby("task_id")["event_type"].count().rename("event_count")
    pause_counts = (
        events[events["event_type"].isin(["PAUSED", "RESUMED"])]
        .groupby("task_id")["event_type"]
        .count()
        .rename("pause_resume_count")
    )
    df = df.merge(event_counts, left_on="id", right_index=True, how="left")
    df = df.merge(pause_counts, left_on="id", right_index=True, how="left")
    df["event_count"] = df["event_count"].fillna(0)
    df["pause_resume_count"] = df["pause_resume_count"].fillna(0)

    # --- interruption features: interruptions in the 30 min window after task creation ---
    # (a simple, explainable proxy for "how noisy was the environment right after this
    # task was created" — richer session-based windows belong in context_sessions
    # once that table is populated by the aggregation job.)
    interruptions = interruptions.sort_values("occurred_at")
    df["nearby_interruptions"] = 0
    if not interruptions.empty and not df.empty:
        for idx, row in df.iterrows():
            if pd.isna(row["created_ts"]):
                continue
            window_start = row["created_ts"]
            window_end = window_start + pd.Timedelta(minutes=30)
            same_user = interruptions["user_id"] == row["user_id"]
            in_window = interruptions["occurred_at"].between(window_start, window_end)
            df.at[idx, "nearby_interruptions"] = int((same_user & in_window).sum())

    # --- target ---
    df["is_forgotten"] = (df["status"] == "FORGOTTEN").astype(int)

    feature_cols = [
        "id", "user_id", "title", "priority", "context_tag", "location_type",
        "created_hour", "is_late_night", "is_weekend", "event_count",
        "pause_resume_count", "nearby_interruptions", "estimated_minutes",
        "is_forgotten",
    ]
    return df[feature_cols]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build forget-risk feature table")
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[2] / "data")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    out_path = args.out or (args.data_dir / "features_forget_risk.csv")
    raw = load_raw(args.data_dir)
    features = build_forget_risk_features(raw)
    features.to_csv(out_path, index=False)
    print(f"Wrote {len(features)} rows to {out_path}")
    print(f"Base forget rate: {features['is_forgotten'].mean():.2%}")


if __name__ == "__main__":
    main()
