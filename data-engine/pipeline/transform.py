"""
Stage 3 — Transformation
=========================

Enriches cleaned DataFrames with derived columns needed for downstream
feature engineering and analytics. All operations are deterministic and
produce the same output for the same input.

Derived columns added
---------------------
events_df:
  - event_hour          int       hour-of-day (0-23) of event_time
  - event_weekday       str       day name ("Monday"...)
  - event_weekday_num   int       0=Monday...6=Sunday
  - is_late_night       bool      event_hour >= 21
  - inter_event_gap_s   float     seconds since previous event on same task
                                  (NaN for first event per task)
  - session_index       int       which session within this task (0-based)

tasks_df:
  - task_age_at_start_h float     hours between created_at and started_at
  - task_duration_h     float     hours between started_at and completed_at
  - deadline_distance_h float     hours between created_at and deadline_at
  - task_location_pair  str       "<category>@<location_type>" context key
  - is_late_night_start bool      started_at.hour >= 21

interruptions_df:
  - interruption_hour   int       hour-of-day of start_time
  - interruption_density float    1/duration in minutes (higher=shorter burst)

All columns are added non-destructively (originals preserved).
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ── events transformation ─────────────────────────────────────────────────────

def transform_events(events_df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns to a cleaned task_events DataFrame."""
    if events_df.empty:
        return events_df

    df = events_df.copy()

    if "event_time" in df.columns and pd.api.types.is_datetime64_any_dtype(df["event_time"]):
        df["event_hour"] = df["event_time"].dt.hour
        df["event_weekday"] = df["event_time"].dt.day_name()
        df["event_weekday_num"] = df["event_time"].dt.dayofweek
        df["is_late_night"] = df["event_hour"] >= 21

    # inter-event gap within each task (sorted chronologically)
    if "task_id" in df.columns and "event_time" in df.columns:
        df = df.sort_values(["task_id", "event_time"]).copy()
        df["inter_event_gap_s"] = (
            df.groupby("task_id")["event_time"]
            .diff()
            .dt.total_seconds()
        )

    # session_index: increment each time we see a "started" or "resumed" event
    if "task_id" in df.columns and "event_type" in df.columns:
        open_types = {"started", "resumed"}
        df["_is_open"] = df["event_type"].isin(open_types).astype(int)
        df["session_index"] = df.groupby("task_id")["_is_open"].cumsum() - df["_is_open"]
        df = df.drop(columns=["_is_open"])

    logger.info(
        "transform_events: added derived columns to %d events", len(df)
    )
    return df


# ── tasks transformation ──────────────────────────────────────────────────────

def transform_tasks(tasks_df: pd.DataFrame, locations_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Add derived columns to a cleaned tasks DataFrame."""
    if tasks_df.empty:
        return tasks_df

    df = tasks_df.copy()

    # Task age at start
    if "created_at" in df.columns and "started_at" in df.columns:
        df["task_age_at_start_h"] = (
            (df["started_at"] - df["created_at"])
            .dt.total_seconds()
            .div(3600.0)
            .round(3)
        )

    # Task duration
    if "started_at" in df.columns and "completed_at" in df.columns:
        df["task_duration_h"] = (
            (df["completed_at"] - df["started_at"])
            .dt.total_seconds()
            .div(3600.0)
            .round(3)
        )

    # Deadline distance
    if "created_at" in df.columns and "deadline_at" in df.columns:
        df["deadline_distance_h"] = (
            (df["deadline_at"] - df["created_at"])
            .dt.total_seconds()
            .div(3600.0)
            .round(3)
        )

    # Late-night start flag
    if "started_at" in df.columns and pd.api.types.is_datetime64_any_dtype(df["started_at"]):
        df["is_late_night_start"] = df["started_at"].dt.hour >= 21

    # Context pair: category@location_type
    if "category" in df.columns and "location_id" in df.columns and locations_df is not None:
        loc_type_map = (
            locations_df.set_index("id")["location_type"].to_dict()
            if "id" in locations_df.columns and "location_type" in locations_df.columns
            else {}
        )
        df["location_type"] = df["location_id"].map(loc_type_map).fillna("UNKNOWN")
        df["task_location_pair"] = df["category"].astype(str) + "@" + df["location_type"].astype(str)
    else:
        df["task_location_pair"] = df.get("category", pd.Series(["unknown"] * len(df))).astype(str) + "@UNKNOWN"

    # is_repeated_context: user has this task_location_pair in their history
    if "user_id" in df.columns and "task_location_pair" in df.columns and "created_at" in df.columns:
        df = df.sort_values(["user_id", "created_at"]).copy()
        df["_pair_count"] = df.groupby(["user_id", "task_location_pair"]).cumcount()
        df["is_repeated_context"] = df["_pair_count"] > 0
        df = df.drop(columns=["_pair_count"])

    logger.info("transform_tasks: enriched %d task rows", len(df))
    return df


# ── interruptions transformation ──────────────────────────────────────────────

def transform_interruptions(interruptions_df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns to a cleaned interruptions DataFrame."""
    if interruptions_df.empty:
        return interruptions_df

    df = interruptions_df.copy()

    if "start_time" in df.columns and pd.api.types.is_datetime64_any_dtype(df["start_time"]):
        df["interruption_hour"] = df["start_time"].dt.hour
        df["interruption_weekday"] = df["start_time"].dt.day_name()

    # Interruption density: inverse of duration in minutes (a 10s interruption
    # is "denser"/more disruptive per unit of perceived interruption than a 5-min one)
    if "duration_seconds" in df.columns:
        dur_min = df["duration_seconds"].div(60.0).replace(0, np.nan)
        df["interruption_density"] = (1.0 / dur_min).round(4)

    logger.info("transform_interruptions: enriched %d interruption rows", len(df))
    return df


def transform_all(
    events_df: pd.DataFrame,
    interruptions_df: pd.DataFrame,
    tasks_df: pd.DataFrame,
    locations_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Apply all transformations. Returns (events, interruptions, tasks)."""
    events_t = transform_events(events_df)
    interruptions_t = transform_interruptions(interruptions_df)
    tasks_t = transform_tasks(tasks_df, locations_df=locations_df)
    logger.info("transform_all: complete")
    return events_t, interruptions_t, tasks_t
