"""
Stage 1 — Event Validation
============================

Validates incoming raw DataFrames BEFORE they reach the cleaning or DB
write stages. Returns a ValidationReport describing every issue found
without modifying the data.

Rules enforced
--------------
Events (task_events):
  - Required fields present: user_id, task_id, event_type, event_time
  - event_type is a recognised value (case-insensitive)
  - event_time is a valid datetime, timezone-aware, not in the future,
    not before 2000-01-01
  - No exact duplicate rows: same (user_id, task_id, event_type, event_time)
  - No backwards sequences per task: completed/forgotten/cancelled must not
    precede any started/created event for the same task

Interruptions:
  - Required fields: user_id, interruption_type, start_time
  - interruption_type is a recognised value
  - end_time >= start_time where both are provided
  - duration_seconds >= 0 where provided

Tasks:
  - priority in [1, 5]
  - status is a recognised value
  - created_at <= started_at <= completed_at (where all provided)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ── canonical value sets ──────────────────────────────────────────────────────
VALID_EVENT_TYPES = frozenset([
    "created", "started", "paused", "resumed", "completed", "forgotten", "cancelled",
])
VALID_INTERRUPTION_TYPES = frozenset([
    "phone", "social_media", "message", "call", "search", "person", "food", "other",
])
VALID_TASK_STATUSES = frozenset([
    "created", "started", "paused", "resumed", "completed", "forgotten", "cancelled",
])
VALID_LOCATION_TYPES = frozenset([
    "HOME", "WORK", "GYM", "COMMUTE", "STUDY", "OTHER",
])

_EPOCH_MIN = datetime(2000, 1, 1, tzinfo=timezone.utc)


@dataclass
class ValidationIssue:
    stage: str          # "events" | "interruptions" | "tasks"
    severity: str       # "error" | "warning"
    rule: str           # machine-readable rule name
    row_index: Any      # original DataFrame index
    detail: str         # human description


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def is_clean(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        return (
            f"ValidationReport: {len(self.issues)} issues "
            f"({len(self.errors)} errors, {len(self.warnings)} warnings)"
        )

    def as_dataframe(self) -> pd.DataFrame:
        if not self.issues:
            return pd.DataFrame(columns=["stage", "severity", "rule", "row_index", "detail"])
        return pd.DataFrame([vars(i) for i in self.issues])


# ── helpers ───────────────────────────────────────────────────────────────────

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _to_utc(val) -> datetime | None:
    """Attempt to coerce a value to a UTC-aware datetime. Returns None on failure."""
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(val, pd.Timestamp):
        if pd.isna(val):
            return None
        val = val.to_pydatetime()
    if not isinstance(val, datetime):
        return None
    if val.tzinfo is None:
        val = val.replace(tzinfo=timezone.utc)
    return val.astimezone(timezone.utc)


# ── public validators ─────────────────────────────────────────────────────────

def validate_events(events_df: pd.DataFrame) -> ValidationReport:
    """Validate a task_events DataFrame. Returns a ValidationReport."""
    report = ValidationReport()
    if events_df.empty:
        logger.warning("validate_events: received empty DataFrame")
        return report

    now = _now_utc()
    required = ["user_id", "task_id", "event_type", "event_time"]

    for idx, row in events_df.iterrows():
        # R1 — required fields
        for col in required:
            if col not in events_df.columns or pd.isna(row.get(col, None)):
                report.issues.append(ValidationIssue(
                    stage="events", severity="error", rule="missing_required_field",
                    row_index=idx, detail=f"Missing required field: {col}",
                ))

        # R2 — event_type validity
        et = str(row.get("event_type", "")).lower().strip()
        if et not in VALID_EVENT_TYPES:
            report.issues.append(ValidationIssue(
                stage="events", severity="error", rule="invalid_event_type",
                row_index=idx, detail=f"Unrecognised event_type: {row.get('event_type')!r}",
            ))

        # R3 — timestamp validity
        ts = _to_utc(row.get("event_time"))
        if ts is None:
            report.issues.append(ValidationIssue(
                stage="events", severity="error", rule="invalid_timestamp",
                row_index=idx, detail=f"event_time cannot be parsed: {row.get('event_time')!r}",
            ))
        else:
            if ts > now:
                report.issues.append(ValidationIssue(
                    stage="events", severity="warning", rule="future_timestamp",
                    row_index=idx, detail=f"event_time {ts.isoformat()} is in the future",
                ))
            if ts < _EPOCH_MIN:
                report.issues.append(ValidationIssue(
                    stage="events", severity="error", rule="prehistoric_timestamp",
                    row_index=idx, detail=f"event_time {ts.isoformat()} is before 2000-01-01",
                ))

    # R4 — duplicate events
    key_cols = [c for c in ["user_id", "task_id", "event_type", "event_time"] if c in events_df.columns]
    dups = events_df.duplicated(subset=key_cols, keep="first")
    for idx in events_df[dups].index:
        report.issues.append(ValidationIssue(
            stage="events", severity="warning", rule="duplicate_event",
            row_index=idx, detail="Duplicate (user_id, task_id, event_type, event_time)",
        ))

    # R5 — backwards sequences per task
    if "task_id" in events_df.columns and "event_time" in events_df.columns:
        _validate_event_sequences(events_df, report)

    logger.info("validate_events: %s", report.summary())
    return report


def _validate_event_sequences(events_df: pd.DataFrame, report: ValidationReport) -> None:
    """Flag tasks where a terminal event precedes any open event."""
    terminal = frozenset(["completed", "forgotten", "cancelled"])
    open_ev = frozenset(["created", "started"])

    for task_id, group in events_df.groupby("task_id"):
        sorted_g = group.sort_values("event_time")
        types = [str(e).lower() for e in sorted_g["event_type"]]
        # Find first terminal index
        term_idx = next((i for i, t in enumerate(types) if t in terminal), None)
        if term_idx is None:
            continue
        # Any open event after terminal?
        for i, t in enumerate(types):
            if i > term_idx and t in open_ev:
                orig_idx = sorted_g.index[i]
                report.issues.append(ValidationIssue(
                    stage="events", severity="error", rule="impossible_sequence",
                    row_index=orig_idx,
                    detail=(
                        f"Task {task_id}: '{t}' event at position {i} follows "
                        f"terminal event '{types[term_idx]}' at position {term_idx}"
                    ),
                ))


def validate_interruptions(interruptions_df: pd.DataFrame) -> ValidationReport:
    """Validate an interruptions DataFrame. Returns a ValidationReport."""
    report = ValidationReport()
    if interruptions_df.empty:
        return report

    required = ["user_id", "interruption_type", "start_time"]
    now = _now_utc()

    for idx, row in interruptions_df.iterrows():
        # R1 — required fields
        for col in required:
            if col not in interruptions_df.columns or pd.isna(row.get(col, None)):
                report.issues.append(ValidationIssue(
                    stage="interruptions", severity="error", rule="missing_required_field",
                    row_index=idx, detail=f"Missing required field: {col}",
                ))

        # R2 — interruption_type validity
        it = str(row.get("interruption_type", "")).lower().strip()
        if it not in VALID_INTERRUPTION_TYPES:
            report.issues.append(ValidationIssue(
                stage="interruptions", severity="error", rule="invalid_interruption_type",
                row_index=idx, detail=f"Unrecognised interruption_type: {row.get('interruption_type')!r}",
            ))

        # R3 — start_time
        start = _to_utc(row.get("start_time"))
        if start is None:
            report.issues.append(ValidationIssue(
                stage="interruptions", severity="error", rule="invalid_timestamp",
                row_index=idx, detail="start_time cannot be parsed",
            ))
        else:
            if start > now:
                report.issues.append(ValidationIssue(
                    stage="interruptions", severity="warning", rule="future_timestamp",
                    row_index=idx, detail=f"start_time {start.isoformat()} is in the future",
                ))

        # R4 — end >= start
        end = _to_utc(row.get("end_time")) if "end_time" in interruptions_df.columns else None
        if start is not None and end is not None and end < start:
            report.issues.append(ValidationIssue(
                stage="interruptions", severity="error", rule="end_before_start",
                row_index=idx, detail=f"end_time {end.isoformat()} < start_time {start.isoformat()}",
            ))

        # R5 — duration non-negative
        dur = row.get("duration_seconds")
        if dur is not None and not pd.isna(dur) and float(dur) < 0:
            report.issues.append(ValidationIssue(
                stage="interruptions", severity="error", rule="negative_duration",
                row_index=idx, detail=f"duration_seconds={dur} is negative",
            ))

    logger.info("validate_interruptions: %s", report.summary())
    return report


def validate_tasks(tasks_df: pd.DataFrame) -> ValidationReport:
    """Validate a tasks DataFrame. Returns a ValidationReport."""
    report = ValidationReport()
    if tasks_df.empty:
        return report

    for idx, row in tasks_df.iterrows():
        # R1 — priority range
        priority = row.get("priority")
        if priority is not None and not pd.isna(priority):
            if not (1 <= int(priority) <= 5):
                report.issues.append(ValidationIssue(
                    stage="tasks", severity="error", rule="invalid_priority",
                    row_index=idx, detail=f"priority={priority} not in [1,5]",
                ))

        # R2 — status validity
        status = str(row.get("status", "")).lower().strip()
        if status and status not in VALID_TASK_STATUSES:
            report.issues.append(ValidationIssue(
                stage="tasks", severity="error", rule="invalid_status",
                row_index=idx, detail=f"Unrecognised status: {row.get('status')!r}",
            ))

        # R3 — timestamp ordering
        created = _to_utc(row.get("created_at"))
        started = _to_utc(row.get("started_at"))
        completed = _to_utc(row.get("completed_at"))

        if created and started and started < created:
            report.issues.append(ValidationIssue(
                stage="tasks", severity="error", rule="started_before_created",
                row_index=idx, detail=f"started_at {started} < created_at {created}",
            ))
        if started and completed and completed < started:
            report.issues.append(ValidationIssue(
                stage="tasks", severity="error", rule="completed_before_started",
                row_index=idx, detail=f"completed_at {completed} < started_at {started}",
            ))

    logger.info("validate_tasks: %s", report.summary())
    return report


def validate_all(
    events_df: pd.DataFrame,
    interruptions_df: pd.DataFrame,
    tasks_df: pd.DataFrame,
) -> ValidationReport:
    """Run all validators and merge results into one report."""
    combined = ValidationReport()
    for report in [
        validate_events(events_df),
        validate_interruptions(interruptions_df),
        validate_tasks(tasks_df),
    ]:
        combined.issues.extend(report.issues)
    logger.info("validate_all: %s", combined.summary())
    return combined
