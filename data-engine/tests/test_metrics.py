import pandas as pd
import pytest

from app.analytics import metrics as m
from app.models.task import TaskStatus


def _tasks_df(rows):
    return pd.DataFrame(rows)


def test_task_completion_rate_basic():
    df = _tasks_df(
        [
            {"status": TaskStatus.COMPLETED.value, "category": "a", "location_id": None, "created_at": pd.Timestamp("2026-01-01")},
            {"status": TaskStatus.FORGOTTEN.value, "category": "a", "location_id": None, "created_at": pd.Timestamp("2026-01-02")},
            {"status": TaskStatus.CREATED.value, "category": "a", "location_id": None, "created_at": pd.Timestamp("2026-01-03")},
        ]
    )
    # only resolved statuses (completed/forgotten/cancelled) count; "created" is excluded
    assert m.task_completion_rate(df) == 0.5
    assert m.task_forgetting_rate(df) == 0.5


def test_task_completion_rate_empty():
    df = pd.DataFrame(columns=["status"])
    assert m.task_completion_rate(df) == 0.0
    assert m.task_forgetting_rate(df) == 0.0


def test_average_task_duration_minutes():
    df = _tasks_df(
        [
            {
                "status": TaskStatus.COMPLETED.value,
                "started_at": pd.Timestamp("2026-01-01 09:00"),
                "completed_at": pd.Timestamp("2026-01-01 09:30"),
            },
            {
                "status": TaskStatus.COMPLETED.value,
                "started_at": pd.Timestamp("2026-01-01 10:00"),
                "completed_at": pd.Timestamp("2026-01-01 10:10"),
            },
        ]
    )
    assert m.average_task_duration_minutes(df) == 20.0


def test_average_task_duration_minutes_no_completed_tasks():
    df = _tasks_df([{"status": TaskStatus.CREATED.value, "started_at": None, "completed_at": None}])
    assert m.average_task_duration_minutes(df) is None


def test_tasks_per_category():
    df = _tasks_df([{"category": "email"}, {"category": "email"}, {"category": "chores"}])
    result = m.tasks_per_category(df)
    assert result["email"] == 2
    assert result["chores"] == 1


def test_interruption_metrics():
    df = pd.DataFrame(
        {
            "duration_seconds": [60, 120, 30],
            "interruption_type": ["phone", "message", "phone"],
            "start_time": pd.to_datetime(["2026-01-05 09:00", "2026-01-05 10:00", "2026-01-06 09:00"]),
        }
    )
    assert m.interruption_count(df) == 3
    assert m.interruption_duration_minutes_total(df) == pytest.approx(210 / 60.0)
    assert m.interruption_by_category(df)["phone"] == 2


def test_interruption_metrics_empty():
    df = pd.DataFrame(columns=["duration_seconds", "interruption_type", "start_time"])
    assert m.interruption_count(df) == 0
    assert m.interruption_duration_minutes_total(df) == 0.0
    assert m.interruption_duration_minutes_avg(df) is None


def test_context_switching_by_task_category():
    sessions = pd.DataFrame({"task_id": [1, 2], "context_switch_count": [2, 3], "location_id": [None, None]})
    tasks = pd.DataFrame({"id": [1, 2], "category": ["email", "deep_work"]})
    result = m.context_switching_by_task_category(sessions, tasks)
    assert result == {"deep_work": 3, "email": 2}


def test_forgetting_by_category():
    df = _tasks_df(
        [
            {"status": TaskStatus.FORGOTTEN.value, "category": "email"},
            {"status": TaskStatus.COMPLETED.value, "category": "email"},
            {"status": TaskStatus.COMPLETED.value, "category": "chores"},
        ]
    )
    result = m.forgetting_by_category(df)
    assert result["email"] == 0.5
    assert result["chores"] == 0.0
