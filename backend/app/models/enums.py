"""
Enumerations shared across the ContextIQ data model.

These are implemented as Python `str` Enums and mapped to native Postgres
ENUM types via SQLAlchemy's `Enum(..., native_enum=True)`. Keeping them in
one module prevents drift between ORM models, Pydantic schemas, and
Alembic-style migration SQL.
"""
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FORGOTTEN = "FORGOTTEN"
    CANCELLED = "CANCELLED"


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TaskEventType(str, Enum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    PAUSED = "PAUSED"
    RESUMED = "RESUMED"
    COMPLETED = "COMPLETED"
    FORGOTTEN = "FORGOTTEN"
    CANCELLED = "CANCELLED"


class InterruptionType(str, Enum):
    PHONE = "PHONE"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    MESSAGE = "MESSAGE"
    CALL = "CALL"
    SEARCH = "SEARCH"
    PERSON = "PERSON"
    FOOD = "FOOD"
    OTHER = "OTHER"


class LocationType(str, Enum):
    HOME = "HOME"
    WORK = "WORK"
    GYM = "GYM"
    COMMUTE = "COMMUTE"
    STUDY = "STUDY"
    OTHER = "OTHER"


class AssociationType(str, Enum):
    OFTEN_FORGOTTEN_WITH = "OFTEN_FORGOTTEN_WITH"   # "one more thing" pattern
    SEQUENTIAL = "SEQUENTIAL"                        # task A usually precedes task B
    BLOCKS = "BLOCKS"                                 # task A blocks task B
    CONTEXT_LINKED = "CONTEXT_LINKED"                 # tasks share a context/location trigger


class PredictionType(str, Enum):
    FORGET_RISK = "FORGET_RISK"
    OPTIMAL_TIME_WINDOW = "OPTIMAL_TIME_WINDOW"
    CONTEXT_SWITCH_RISK = "CONTEXT_SWITCH_RISK"
    INTERRUPTION_RISK = "INTERRUPTION_RISK"
    ONE_MORE_THING = "ONE_MORE_THING"


class RecommendationType(str, Enum):
    REMINDER = "REMINDER"
    SCHEDULE_SHIFT = "SCHEDULE_SHIFT"
    BATCH_TASKS = "BATCH_TASKS"
    LOCATION_TRIGGER = "LOCATION_TRIGGER"
    BREAK_SUGGESTION = "BREAK_SUGGESTION"
    ONE_MORE_THING_NUDGE = "ONE_MORE_THING_NUDGE"


class RecommendationStatus(str, Enum):
    PENDING = "PENDING"
    SHOWN = "SHOWN"
    ACCEPTED = "ACCEPTED"
    DISMISSED = "DISMISSED"
    EXPIRED = "EXPIRED"


class RecommendationFeedbackAction(str, Enum):
    ACCEPTED = "ACCEPTED"
    DISMISSED = "DISMISSED"
    DEFERRED = "DEFERRED"


class BehaviourMetricType(str, Enum):
    FORGOTTEN_TASK_RATE = "FORGOTTEN_TASK_RATE"
    AVG_INTERRUPTIONS_PER_SESSION = "AVG_INTERRUPTIONS_PER_SESSION"
    CONTEXT_SWITCH_COUNT = "CONTEXT_SWITCH_COUNT"
    FOCUS_MINUTES = "FOCUS_MINUTES"
    TASK_COMPLETION_RATE = "TASK_COMPLETION_RATE"
    AVG_TASK_DELAY_MINUTES = "AVG_TASK_DELAY_MINUTES"
