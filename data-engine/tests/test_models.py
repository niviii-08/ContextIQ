import uuid
from datetime import datetime, timezone

from app.models.task import Task, TaskStatus
from app.models.task_event import TaskEvent, TaskEventType
from app.models.interruption import Interruption, InterruptionType


def test_user_created(sample_user):
    assert sample_user.id is not None
    assert sample_user.email == "test@example.com"


def test_location_belongs_to_user(sample_location, sample_user):
    assert sample_location.user_id == sample_user.id


def test_task_creation_defaults(db_session, sample_user):
    task = Task(user_id=sample_user.id, title="Write report", category="deep_work")
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    assert task.status == TaskStatus.CREATED
    assert task.priority == 3
    assert task.id is not None


def test_task_priority_constraint(db_session, sample_user):
    """priority must be within 1-5 per CHECK constraint."""
    import pytest
    from sqlalchemy.exc import IntegrityError

    task = Task(user_id=sample_user.id, title="Bad priority", priority=99)
    db_session.add(task)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_task_event_lifecycle(db_session, sample_user):
    task = Task(user_id=sample_user.id, title="Task with events")
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    event = TaskEvent(
        user_id=sample_user.id,
        task_id=task.id,
        event_type=TaskEventType.STARTED,
        event_time=datetime.now(timezone.utc),
    )
    db_session.add(event)
    db_session.commit()

    assert len(task.events) == 1
    assert task.events[0].event_type == TaskEventType.STARTED


def test_interruption_without_task(db_session, sample_user):
    """Interruptions may exist without an associated task (idle browsing)."""
    interruption = Interruption(
        user_id=sample_user.id,
        interruption_type=InterruptionType.SOCIAL_MEDIA,
        start_time=datetime.now(timezone.utc),
        duration_seconds=45,
    )
    db_session.add(interruption)
    db_session.commit()
    db_session.refresh(interruption)

    assert interruption.task_id is None
    assert interruption.duration_seconds == 45


def test_cascade_delete_user_removes_tasks(db_session, sample_user):
    task = Task(user_id=sample_user.id, title="To be cascade-deleted")
    db_session.add(task)
    db_session.commit()
    task_id = task.id

    db_session.delete(sample_user)
    db_session.commit()

    remaining = db_session.get(Task, task_id)
    assert remaining is None
