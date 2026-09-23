"""
feedback_store.py
==================
Simple persistence layer for user feedback on insights/recommendations.

The interface (FeedbackStore) is intentionally minimal so it can later be
backed by a real database (Postgres, DynamoDB, etc.) without changing
callers. InMemoryFeedbackStore is the default, dependency-free
implementation used for local runs and tests.
"""

from __future__ import annotations

import abc
import uuid
from typing import Dict, List

from app.schemas import FeedbackEntry


class FeedbackStore(abc.ABC):
    @abc.abstractmethod
    def save(self, entry: FeedbackEntry) -> str:
        """Persist a feedback entry and return its stored id."""
        raise NotImplementedError

    @abc.abstractmethod
    def list_for_user(self, user_id: str) -> List[FeedbackEntry]:
        raise NotImplementedError


class InMemoryFeedbackStore(FeedbackStore):
    """Process-local store. Data does not survive a restart.

    Swap for a database-backed implementation (e.g. SQLAlchemy, boto3/DynamoDB)
    by implementing the same `FeedbackStore` interface.
    """

    def __init__(self):
        self._entries: Dict[str, FeedbackEntry] = {}

    def save(self, entry: FeedbackEntry) -> str:
        entry_id = str(uuid.uuid4())
        self._entries[entry_id] = entry
        return entry_id

    def list_for_user(self, user_id: str) -> List[FeedbackEntry]:
        return [e for e in self._entries.values() if e.user_id == user_id]


# Module-level singleton used by the API layer for simplicity in this
# standalone module. A real deployment should inject a store instance
# (e.g. via FastAPI dependency injection) backed by a real database.
default_store = InMemoryFeedbackStore()
