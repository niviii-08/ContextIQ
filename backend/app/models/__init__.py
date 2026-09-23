"""
Import every ORM model here so that `Base.metadata` is fully populated
whenever `app.models` is imported -- this is required for
`Base.metadata.create_all()` (dev/test bootstrapping) and for any future
Alembic `env.py` to autogenerate correctly.
"""
from app.models.user import User  # noqa: F401
from app.models.location import Location  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.task_event import TaskEvent  # noqa: F401
from app.models.interruption import Interruption  # noqa: F401
from app.models.context_session import ContextSession  # noqa: F401
from app.models.task_association import TaskAssociation  # noqa: F401
from app.models.prediction import Prediction  # noqa: F401
from app.models.recommendation import Recommendation  # noqa: F401
from app.models.recommendation_feedback import RecommendationFeedback  # noqa: F401
from app.models.behaviour_metric import BehaviourMetric  # noqa: F401

__all__ = [
    "User",
    "Location",
    "Task",
    "TaskEvent",
    "Interruption",
    "ContextSession",
    "TaskAssociation",
    "Prediction",
    "Recommendation",
    "RecommendationFeedback",
    "BehaviourMetric",
]
