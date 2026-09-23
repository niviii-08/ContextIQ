"""Shared pytest fixtures."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.events import RawEvent, EventType


@pytest.fixture
def simple_session_events() -> list[RawEvent]:
    """A single clean session: START -> INTERRUPTION -> RESUME -> COMPLETE."""
    t0 = datetime(2026, 1, 1, 9, 0, 0)
    return [
        RawEvent(
            user_id="u1",
            timestamp=t0,
            task_id="t1",
            task_category="programming",
            context="home_office",
            event_type=EventType.START,
        ),
        RawEvent(
            user_id="u1",
            timestamp=t0 + timedelta(seconds=60),
            task_id="t1",
            task_category="programming",
            context="home_office",
            event_type=EventType.INTERRUPTION,
            interruption_source="social_media",
        ),
        RawEvent(
            user_id="u1",
            timestamp=t0 + timedelta(seconds=120),
            task_id="t1",
            task_category="programming",
            context="home_office",
            event_type=EventType.RESUME,
        ),
        RawEvent(
            user_id="u1",
            timestamp=t0 + timedelta(seconds=240),
            task_id="t1",
            task_category="programming",
            context="home_office",
            event_type=EventType.COMPLETE,
        ),
    ]


@pytest.fixture
def department_transactions_raw_events() -> list[RawEvent]:
    """Multiple department visits with COMPLETE events, some tasks
    co-occurring frequently and some rarely, for association mining tests."""
    events: list[RawEvent] = []
    t = datetime(2026, 1, 1, 9, 0, 0)

    # 8 visits: collect_form + submit_record co-occur in 6/8; ask_faculty in 3/8.
    patterns = [
        ["collect_form", "submit_record", "ask_faculty"],
        ["collect_form", "submit_record"],
        ["collect_form", "submit_record", "ask_faculty"],
        ["collect_form", "submit_record"],
        ["collect_form", "submit_record", "ask_faculty"],
        ["collect_form", "submit_record"],
        ["collect_form"],
        ["ask_faculty"],
    ]

    for i, tasks in enumerate(patterns):
        visit_start = t + timedelta(days=i)
        for j, task in enumerate(tasks):
            events.append(
                RawEvent(
                    user_id="u1",
                    timestamp=visit_start + timedelta(minutes=j * 5),
                    task_id=f"{task}_{i}_{j}",
                    task_category="admin",
                    context="department",
                    event_type=EventType.COMPLETE,
                )
            )
    return events
