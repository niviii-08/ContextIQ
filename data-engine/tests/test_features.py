from datetime import datetime, timedelta, timezone

import pandas as pd

from app.models.task import TaskStatus
from app.utils import features as feat


def _tasks_df():
    return pd.DataFrame(
        [
            {
                "id": 1,
                "category": "email",
                "location_id": "loc-1",
                "priority": 2,
                "status": TaskStatus.FORGOTTEN.value,
                "created_at": pd.Timestamp("2026-01-01 09:00", tz="UTC"),
                "deadline_at": pd.NaT,
            },
            {
                "id": 2,
                "category": "email",
                "location_id": "loc-1",
                "priority": 3,
                "status": TaskStatus.COMPLETED.value,
                "created_at": pd.Timestamp("2026-01-02 09:00", tz="UTC"),
                "deadline_at": pd.NaT,
            },
            {
                # This task is created AFTER as_of in the leakage test below.
                "id": 3,
                "category": "email",
                "location_id": "loc-1",
                "priority": 1,
                "status": TaskStatus.FORGOTTEN.value,
                "created_at": pd.Timestamp("2026-01-10 09:00", tz="UTC"),
                "deadline_at": pd.NaT,
            },
        ]
    )


def test_task_features_exclude_future_tasks():
    tasks_df = _tasks_df()
    events_df = pd.DataFrame(columns=["event_time", "event_type"])
    interruptions_df = pd.DataFrame(columns=["start_time", "duration_seconds"])

    as_of = datetime(2026, 1, 3, tzinfo=timezone.utc)  # strictly before task id=3
    task_row = {"category": "email", "location_id": "loc-1", "priority": 5, "created_at": as_of, "deadline_at": None}

    features = feat.generate_task_features(
        task_row=task_row, tasks_df=tasks_df, events_df=events_df, interruptions_df=interruptions_df, as_of=as_of
    )

    # Only tasks 1 and 2 (both created before as_of) should be visible.
    assert features["task_frequency"] == 2
    assert features["previous_forgetting_count"] == 1
    assert features["previous_completion_count"] == 1


def test_task_features_never_see_own_outcome():
    """A task's own outcome must never leak into its own features — this
    is enforced structurally because as_of == the task's own created_at
    means the strict '<' filter excludes the task itself."""
    tasks_df = _tasks_df()
    events_df = pd.DataFrame(columns=["event_time", "event_type"])
    interruptions_df = pd.DataFrame(columns=["start_time", "duration_seconds"])

    # as_of == task 1's own created_at -> task 1 must be excluded from its own history
    as_of = pd.Timestamp("2026-01-01 09:00", tz="UTC").to_pydatetime()
    task_row = {"category": "email", "location_id": "loc-1", "priority": 2, "created_at": as_of, "deadline_at": None}

    features = feat.generate_task_features(
        task_row=task_row, tasks_df=tasks_df, events_df=events_df, interruptions_df=interruptions_df, as_of=as_of
    )
    assert features["task_frequency"] == 0
    assert features["previous_forgetting_count"] == 0


def test_task_features_naive_and_aware_as_of_both_work():
    """The feature engine must not crash regardless of whether `as_of` is
    timezone-naive or timezone-aware relative to the DataFrame columns."""
    tasks_df = _tasks_df()
    events_df = pd.DataFrame(columns=["event_time", "event_type"])
    interruptions_df = pd.DataFrame(columns=["start_time", "duration_seconds"])

    naive_as_of = datetime(2026, 1, 3)  # no tzinfo
    task_row = {"category": "email", "location_id": "loc-1", "priority": 2, "created_at": naive_as_of, "deadline_at": None}

    features = feat.generate_task_features(
        task_row=task_row,
        tasks_df=tasks_df,
        events_df=events_df,
        interruptions_df=interruptions_df,
        as_of=naive_as_of,
    )
    assert features["task_frequency"] == 2


def test_user_features_empty_history_returns_none_rates():
    tasks_df = pd.DataFrame(columns=["created_at", "status"])
    interruptions_df = pd.DataFrame(columns=["start_time", "duration_seconds"])
    sessions_df = pd.DataFrame(columns=["session_start", "focused_time_seconds", "context_switch_count"])

    result = feat.generate_user_features(
        tasks_df=tasks_df, interruptions_df=interruptions_df, sessions_df=sessions_df, as_of=datetime.now(timezone.utc)
    )
    assert result["completion_rate"] is None
    assert result["total_tasks"] == 0


def test_context_features_scoped_to_location():
    tasks_df = _tasks_df()
    interruptions_df = pd.DataFrame(columns=["location_id", "start_time", "duration_seconds"])
    as_of = datetime(2026, 2, 1, tzinfo=timezone.utc)

    result = feat.generate_context_features(
        location_id="loc-1", tasks_df=tasks_df, interruptions_df=interruptions_df, as_of=as_of
    )
    assert result["location_task_count"] == 3
