import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_LOCAL_DEPS = ROOT / "pydeps"
if _LOCAL_DEPS.exists():
    sys.path.insert(0, str(_LOCAL_DEPS))

import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="session")
def sample_task_payload():
    return {
        "task_id": "Lab Record",
        "task_category": "Academic",
        "priority": "HIGH",
        "location": "Campus",
        "weekday": 2,
        "hour": 14,
        "deadline_distance_hours": 18.0,
        "previous_completion_count": 12,
        "previous_forgetting_count": 8,
        "historical_completion_rate": 0.4,
        "historical_forgetting_rate": 0.55,
        "task_frequency": 0.3,
        "tasks_today": 5,
        "interruptions_today": 4,
        "recent_context_switches": 6,
        "avg_interruption_duration": 8.5,
        "avg_session_duration": 22.0,
    }


@pytest.fixture(scope="session")
def high_risk_payload():
    return {
        "task_id": "high-risk-sample",
        "task_category": "Household",
        "priority": "LOW",
        "location": "Other",
        "weekday": 6,
        "hour": 22,
        "deadline_distance_hours": 2.0,
        "previous_completion_count": 3,
        "previous_forgetting_count": 40,
        "historical_completion_rate": 0.07,
        "historical_forgetting_rate": 0.93,
        "task_frequency": 0.02,
        "tasks_today": 10,
        "interruptions_today": 15,
        "recent_context_switches": 18,
        "avg_interruption_duration": 25.0,
        "avg_session_duration": 5.0,
    }


@pytest.fixture(scope="session")
def low_risk_payload():
    return {
        "task_id": "low-risk-sample",
        "task_category": "Work",
        "priority": "HIGH",
        "location": "Office",
        "weekday": 1,
        "hour": 9,
        "deadline_distance_hours": 120.0,
        "previous_completion_count": 200,
        "previous_forgetting_count": 2,
        "historical_completion_rate": 0.99,
        "historical_forgetting_rate": 0.01,
        "task_frequency": 0.4,
        "tasks_today": 3,
        "interruptions_today": 0,
        "recent_context_switches": 0,
        "avg_interruption_duration": 1.0,
        "avg_session_duration": 60.0,
    }
