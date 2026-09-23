"""
feature_spec.py

Single source of truth for the feature contract used across training and
inference. Both the training pipeline and the FastAPI inference layer
import from this module so they can never drift apart.
"""

from dataclasses import dataclass, field
from typing import List

# Categorical features (one-hot encoded)
CATEGORICAL_FEATURES: List[str] = [
    "task_category",
    "priority",
    "location",
]

# Numeric features (used as-is / scaled for linear model)
NUMERIC_FEATURES: List[str] = [
    "weekday",
    "hour",
    "deadline_distance_hours",
    "previous_completion_count",
    "previous_forgetting_count",
    "historical_completion_rate",
    "historical_forgetting_rate",
    "task_frequency",
    "tasks_today",
    "interruptions_today",
    "recent_context_switches",
    "avg_interruption_duration",
    "avg_session_duration",
]

ALL_RAW_FEATURES: List[str] = CATEGORICAL_FEATURES + NUMERIC_FEATURES

TARGET_COLUMN = "forgotten"

# Allowed value domains for categorical inputs - used for API validation
CATEGORY_DOMAIN = [
    "Academic", "Work", "Personal", "Health", "Household", "Social", "Finance",
]
PRIORITY_DOMAIN = ["LOW", "MEDIUM", "HIGH"]
LOCATION_DOMAIN = ["Home", "Campus", "Office", "Commute", "Gym", "Other"]

# Human-readable descriptions used by the explainability layer to translate
# a raw feature name + direction into a natural-language reason string.
FEATURE_DESCRIPTIONS = {
    "historical_forgetting_rate": "historical forgetting rate for this user",
    "historical_completion_rate": "historical completion rate for this user",
    "previous_forgetting_count": "number of previously forgotten tasks",
    "previous_completion_count": "number of previously completed tasks",
    "task_frequency": "how often this task category recurs for this user",
    "interruptions_today": "number of interruptions experienced today",
    "recent_context_switches": "recent context switches",
    "avg_interruption_duration": "average interruption duration",
    "avg_session_duration": "average focused session duration",
    "deadline_distance_hours": "time remaining until the task deadline",
    "tasks_today": "number of tasks scheduled today",
    "weekday": "day of the week",
    "hour": "hour of day the task was logged",
    "task_category": "task category",
    "priority": "task priority",
    "location": "task location context",
}


@dataclass(frozen=True)
class FeatureSpec:
    categorical: List[str] = field(default_factory=lambda: list(CATEGORICAL_FEATURES))
    numeric: List[str] = field(default_factory=lambda: list(NUMERIC_FEATURES))
    target: str = TARGET_COLUMN


DEFAULT_SPEC = FeatureSpec()
