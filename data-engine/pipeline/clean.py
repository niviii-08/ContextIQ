"""
Stage 2 — Data Cleaning
========================

Operates on raw pandas DataFrames (as loaded from DB or CSV) and applies
a deterministic sequence of cleaning operations. Every operation is logged
and counted in a CleaningReport so callers can see exactly what changed.

Operations (in order applied)
------------------------------
1. Timezone normalization  — all datetime columns coerced to UTC-aware.
2. Duplicate removal       — exact duplicates on natural keys removed (first kept).
3. Duration imputation     — interruption.duration_seconds computed from
                             end_time - start_time when null.
4. End-time imputation     — interruption.end_time = start_time + duration
                             when end_time is null but duration is known.
5. Category normalization  — lowercase + strip + alias mapping on task categories.
6. Outlier flagging        — sessions/tasks with duration > 12 h flagged
                             `is_anomaly=True` (NOT removed — kept for inspection).
7. Priority clamping       — any priority outside [1,5] clamped (shouldn't
                             exist after validation, but defensive here).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import timezone

import pandas as pd

logger = logging.getLogger(__name__)

# Alias map for category normalization: raw value -> canonical value
CATEGORY_ALIASES: dict[str, str] = {
    "deep work": "deep_work",
    "deep-work": "deep_work",
    "deepwork": "deep_work",
    "emails": "email",
    "e-mail": "email",
    "meetings": "meeting",
    "admin work": "admin",
    "administration": "admin",
    "study": "learning",
    "studying": "learning",
    "chore": "chores",
    "housework": "chores",
    "plan": "planning",
    "plans": "planning",
    "create": "creative",
    "creativity": "creative",
}

# Datetime columns per frame type
_DATETIME_COLS_EVENTS = ["event_time", "created_at"]
_DATETIME_COLS_TASKS = [
    "created_at", "started_at", "completed_at",
    "forgotten_at", "cancelled_at", "deadline_at", "updated_at",
]
_DATETIME_COLS_INTERRUPTIONS = ["start_time", "end_time", "created_at"]

ANOMALY_DURATION_HOURS = 12.0  # sessions/tasks longer than this are flagged


@dataclass
class CleaningReport:
    tz_normalized: dict[str, int] = field(default_factory=dict)
    duplicates_removed: dict[str, int] = field(default_factory=dict)
    durations_imputed: int = 0
    end_times_imputed: int = 0
    categories_normalized: int = 0
    anomalies_flagged: int = 0
    priorities_clamped: int = 0

    def summary(self) -> str:
        return (
            f"CleaningReport: tz_normalized={self.tz_normalized}, "
            f"duplicates_removed={self.duplicates_removed}, "
            f"durations_imputed={self.durations_imputed}, "
            f"end_times_imputed={self.end_times_imputed}, "
            f"categories_normalized={self.categories_normalized}, "
            f"anomalies_flagged={self.anomalies_flagged}, "
            f"priorities_clamped={self.priorities_clamped}"
        )


# ── helpers ───────────────────────────────────────────────────────────────────

def _coerce_datetime_col(series: pd.Series) -> pd.Series:
    """Parse + coerce a datetime column to UTC-aware. Non-parseable values become NaT."""
    if pd.api.types.is_datetime64_any_dtype(series):
        if getattr(series.dt, "tz", None) is None:
            return series.dt.tz_localize("UTC")
        return series.dt.tz_convert("UTC")
    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    return parsed


def _normalize_datetimes(df: pd.DataFrame, cols: list[str], report: CleaningReport, label: str) -> pd.DataFrame:
    df = df.copy()
    changed = 0
    for col in cols:
        if col not in df.columns:
            continue
        before_nulls = df[col].isna().sum()
        df[col] = _coerce_datetime_col(df[col])
        after_nulls = df[col].isna().sum()
        col_changed = int(len(df)) - int(before_nulls)
        changed += max(0, col_changed - max(0, int(len(df)) - int(after_nulls)))
    report.tz_normalized[label] = changed
    return df


# ── public cleaning functions ─────────────────────────────────────────────────

def clean_events(events_df: pd.DataFrame, report: CleaningReport) -> pd.DataFrame:
    """Clean a task_events DataFrame in-place (returns new copy)."""
    df = events_df.copy()
    initial_len = len(df)

    # 1. Timezone normalization
    df = _normalize_datetimes(df, _DATETIME_COLS_EVENTS, report, "events")

    # 2. Duplicate removal
    key = [c for c in ["user_id", "task_id", "event_type", "event_time"] if c in df.columns]
    before = len(df)
    df = df.drop_duplicates(subset=key, keep="first").reset_index(drop=True)
    removed = before - len(df)
    report.duplicates_removed["events"] = removed
    if removed:
        logger.info("clean_events: removed %d duplicate events", removed)

    # 3. Normalize event_type to lowercase
    if "event_type" in df.columns:
        df["event_type"] = df["event_type"].astype(str).str.lower().str.strip()

    logger.info(
        "clean_events: %d → %d rows (-%d removed)",
        initial_len, len(df), initial_len - len(df),
    )
    return df


def clean_interruptions(interruptions_df: pd.DataFrame, report: CleaningReport) -> pd.DataFrame:
    """Clean an interruptions DataFrame."""
    df = interruptions_df.copy()
    initial_len = len(df)

    # 1. Timezone normalization
    df = _normalize_datetimes(df, _DATETIME_COLS_INTERRUPTIONS, report, "interruptions")

    # 2. Duplicate removal
    key = [c for c in ["user_id", "task_id", "interruption_type", "start_time"] if c in df.columns]
    before = len(df)
    df = df.drop_duplicates(subset=key, keep="first").reset_index(drop=True)
    report.duplicates_removed["interruptions"] = before - len(df)

    # 3. Normalize interruption_type to lowercase
    if "interruption_type" in df.columns:
        df["interruption_type"] = df["interruption_type"].astype(str).str.lower().str.strip()

    # 4. Impute duration_seconds from end_time - start_time
    if "start_time" in df.columns and "end_time" in df.columns and "duration_seconds" in df.columns:
        mask = df["duration_seconds"].isna() & df["end_time"].notna() & df["start_time"].notna()
        if mask.any():
            df.loc[mask, "duration_seconds"] = (
                (df.loc[mask, "end_time"] - df.loc[mask, "start_time"])
                .dt.total_seconds()
                .clip(lower=0)
                .astype(float)
            )
            count = int(mask.sum())
            report.durations_imputed += count
            logger.info("clean_interruptions: imputed %d duration_seconds values", count)

    # 5. Impute end_time from start_time + duration
    if "start_time" in df.columns and "end_time" in df.columns and "duration_seconds" in df.columns:
        mask2 = df["end_time"].isna() & df["duration_seconds"].notna() & df["start_time"].notna()
        if mask2.any():
            df.loc[mask2, "end_time"] = df.loc[mask2, "start_time"] + pd.to_timedelta(
                df.loc[mask2, "duration_seconds"], unit="s"
            )
            count2 = int(mask2.sum())
            report.end_times_imputed += count2
            logger.info("clean_interruptions: imputed %d end_time values", count2)

    # 6. Flag anomalously long interruptions (> 12 h)
    if "duration_seconds" in df.columns:
        thresh_sec = ANOMALY_DURATION_HOURS * 3600
        mask3 = df["duration_seconds"].notna() & (df["duration_seconds"] > thresh_sec)
        if mask3.any():
            if "is_anomaly" not in df.columns:
                df["is_anomaly"] = False
            df.loc[mask3, "is_anomaly"] = True
            n = int(mask3.sum())
            report.anomalies_flagged += n
            logger.warning("clean_interruptions: flagged %d anomalously long interruptions", n)

    logger.info("clean_interruptions: %d → %d rows", initial_len, len(df))
    return df


def clean_tasks(tasks_df: pd.DataFrame, report: CleaningReport) -> pd.DataFrame:
    """Clean a tasks DataFrame."""
    df = tasks_df.copy()
    initial_len = len(df)

    # 1. Timezone normalization
    df = _normalize_datetimes(df, _DATETIME_COLS_TASKS, report, "tasks")

    # 2. Duplicate removal on id
    if "id" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["id"], keep="first").reset_index(drop=True)
        report.duplicates_removed["tasks"] = before - len(df)

    # 3. Normalize status to lowercase
    if "status" in df.columns:
        df["status"] = df["status"].astype(str).str.lower().str.strip()

    # 4. Normalize category
    if "category" in df.columns:
        normalized = df["category"].astype(str).str.lower().str.strip()
        mapped = normalized.map(lambda c: CATEGORY_ALIASES.get(c, c))
        changed = int((mapped != normalized).sum())
        df["category"] = mapped
        report.categories_normalized += changed
        if changed:
            logger.info("clean_tasks: normalized %d category values", changed)

    # 5. Clamp priority to [1, 5]
    if "priority" in df.columns:
        before_p = df["priority"].copy()
        df["priority"] = df["priority"].clip(lower=1, upper=5)
        clamped = int((df["priority"] != before_p).sum())
        report.priorities_clamped += clamped

    # 6. Flag anomalous tasks (time to complete > 12 h)
    if "started_at" in df.columns and "completed_at" in df.columns:
        mask = df["started_at"].notna() & df["completed_at"].notna()
        durations_h = pd.Series(float("nan"), index=df.index, dtype=float)
        durations_h.loc[mask] = (
            (df.loc[mask, "completed_at"] - df.loc[mask, "started_at"])
            .dt.total_seconds() / 3600.0
        )
        anomaly_mask = mask & (durations_h > ANOMALY_DURATION_HOURS)
        if anomaly_mask.any():
            if "is_anomaly" not in df.columns:
                df["is_anomaly"] = False
            df.loc[anomaly_mask, "is_anomaly"] = True
            n = int(anomaly_mask.sum())
            report.anomalies_flagged += n
            logger.warning("clean_tasks: flagged %d anomalously long tasks", n)

    logger.info("clean_tasks: %d → %d rows", initial_len, len(df))
    return df


def clean_all(
    events_df: pd.DataFrame,
    interruptions_df: pd.DataFrame,
    tasks_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, CleaningReport]:
    """Run all cleaners and return (events, interruptions, tasks, report)."""
    report = CleaningReport()
    events_clean = clean_events(events_df, report)
    interruptions_clean = clean_interruptions(interruptions_df, report)
    tasks_clean = clean_tasks(tasks_df, report)
    logger.info("clean_all: %s", report.summary())
    return events_clean, interruptions_clean, tasks_clean, report
