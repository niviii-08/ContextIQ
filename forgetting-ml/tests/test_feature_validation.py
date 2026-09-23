import pytest
from pydantic import ValidationError

from app.schemas import TaskFeatures


def test_valid_payload_parses(sample_task_payload):
    task = TaskFeatures(**sample_task_payload)
    assert task.task_category == "Academic"


def test_invalid_category_rejected(sample_task_payload):
    payload = dict(sample_task_payload)
    payload["task_category"] = "NotACategory"
    with pytest.raises(ValidationError):
        TaskFeatures(**payload)


def test_invalid_priority_rejected(sample_task_payload):
    payload = dict(sample_task_payload)
    payload["priority"] = "URGENT"
    with pytest.raises(ValidationError):
        TaskFeatures(**payload)


def test_negative_counts_rejected(sample_task_payload):
    payload = dict(sample_task_payload)
    payload["previous_completion_count"] = -1
    with pytest.raises(ValidationError):
        TaskFeatures(**payload)


def test_rate_out_of_range_rejected(sample_task_payload):
    payload = dict(sample_task_payload)
    payload["historical_completion_rate"] = 1.5
    with pytest.raises(ValidationError):
        TaskFeatures(**payload)


def test_weekday_out_of_range_rejected(sample_task_payload):
    payload = dict(sample_task_payload)
    payload["weekday"] = 7
    with pytest.raises(ValidationError):
        TaskFeatures(**payload)
