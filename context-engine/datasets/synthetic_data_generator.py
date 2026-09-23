"""
Synthetic event data generator.

Produces realistic event sequences containing deliberately strong (but
not perfect) task associations within contexts, plus plausible
interruption/switch patterns, so that System A and System B have
meaningful signal to discover.

This is synthetic/test data only — it does not represent real users.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from app.schemas.events import RawEvent, EventType

# Context -> canonical task set with per-task inclusion probability.
# Not every visit includes every task, which is required for
# meaningful support/confidence/lift.
CONTEXT_TASK_PROFILES: dict[str, dict[str, float]] = {
    "department": {
        "collect_form": 0.9,
        "submit_record": 0.75,
        "ask_faculty": 0.55,
        "pay_fee": 0.2,
    },
    "library": {
        "borrow_book": 0.8,
        "study": 0.7,
        "return_book": 0.5,
        "print_document": 0.15,
    },
    "gym": {
        "warm_up": 0.85,
        "strength_training": 0.6,
        "cardio": 0.55,
        "stretch": 0.4,
    },
    "home_office": {
        "check_email": 0.9,
        "attend_standup": 0.4,
        "write_code": 0.7,
        "review_pr": 0.3,
    },
}

TASK_CATEGORY_MAP = {
    "collect_form": "admin",
    "submit_record": "admin",
    "ask_faculty": "admin",
    "pay_fee": "admin",
    "borrow_book": "study",
    "study": "study",
    "return_book": "study",
    "print_document": "study",
    "warm_up": "fitness",
    "strength_training": "fitness",
    "cardio": "fitness",
    "stretch": "fitness",
    "check_email": "programming",
    "attend_standup": "programming",
    "write_code": "programming",
    "review_pr": "programming",
}

INTERRUPTION_SOURCES = ["social_media", "phone_call", "colleague", "notification", "email"]


def _rand_bool(p: float, rng: random.Random) -> bool:
    return rng.random() < p


def generate_visit_events(
    user_id: str,
    context: str,
    start_time: datetime,
    rng: random.Random,
    interruption_prob: float = 0.35,
    switch_prob: float = 0.2,
) -> list[RawEvent]:
    """Generate the event stream for a single visit to a context, where
    each candidate task for that context is independently included
    according to its configured probability."""
    profile = CONTEXT_TASK_PROFILES[context]
    events: list[RawEvent] = []
    t = start_time

    tasks_this_visit = [task for task, p in profile.items() if _rand_bool(p, rng)]
    if not tasks_this_visit:
        # Ensure at least one task occurs so the visit isn't empty.
        tasks_this_visit = [rng.choice(list(profile.keys()))]

    for task in tasks_this_visit:
        # task_id is the stable task identifier (e.g. "collect_form"), consistent
        # across occurrences, so that association mining can recognize repeated
        # co-occurrence of the same task across many visits. A separate internal
        # visit_id (not part of the event schema) is implied by timestamp grouping.
        task_id = task
        category = TASK_CATEGORY_MAP.get(task, "general")

        events.append(
            RawEvent(
                user_id=user_id,
                timestamp=t,
                task_id=task_id,
                task_category=category,
                context=context,
                event_type=EventType.START,
            )
        )
        t += timedelta(seconds=rng.randint(20, 120))

        if _rand_bool(interruption_prob, rng):
            events.append(
                RawEvent(
                    user_id=user_id,
                    timestamp=t,
                    task_id=task_id,
                    task_category=category,
                    context=context,
                    event_type=EventType.INTERRUPTION,
                    interruption_source=rng.choice(INTERRUPTION_SOURCES),
                )
            )
            # Short interruptions sometimes have long resume delays (for the
            # pattern-discovery module to find).
            if _rand_bool(0.3, rng):
                interruption_len = rng.randint(5, 25)  # short interruption
                t += timedelta(seconds=interruption_len)
                resume_delay_extra = rng.randint(60, 240)  # but long resume delay
                t += timedelta(seconds=resume_delay_extra)
            else:
                t += timedelta(seconds=rng.randint(30, 300))

            events.append(
                RawEvent(
                    user_id=user_id,
                    timestamp=t,
                    task_id=task_id,
                    task_category=category,
                    context=context,
                    event_type=EventType.RESUME,
                )
            )
            t += timedelta(seconds=rng.randint(10, 60))

        if _rand_bool(switch_prob, rng):
            events.append(
                RawEvent(
                    user_id=user_id,
                    timestamp=t,
                    task_id=task_id,
                    task_category=category,
                    context=context,
                    event_type=EventType.TASK_SWITCH,
                )
            )
            t += timedelta(seconds=rng.randint(10, 90))

        t += timedelta(seconds=rng.randint(20, 180))
        events.append(
            RawEvent(
                user_id=user_id,
                timestamp=t,
                task_id=task_id,
                task_category=category,
                context=context,
                event_type=EventType.COMPLETE,
            )
        )
        t += timedelta(seconds=rng.randint(10, 60))

    return events


def generate_dataset(
    num_users: int = 20,
    visits_per_user: int = 15,
    seed: int = 7,
    start_date: datetime | None = None,
) -> list[RawEvent]:
    """Generate a full synthetic dataset across many users and visits."""
    rng = random.Random(seed)
    start_date = start_date or datetime(2026, 1, 1, 8, 0, 0)

    all_events: list[RawEvent] = []
    contexts = list(CONTEXT_TASK_PROFILES.keys())

    for u in range(num_users):
        user_id = f"user_{u:03d}"
        current_time = start_date + timedelta(days=rng.randint(0, 5), hours=rng.randint(0, 10))

        # Give each user a preferred context bias so patterns are user-specific.
        preferred_context = rng.choice(contexts)
        weights = [3 if c == preferred_context else 1 for c in contexts]

        for _ in range(visits_per_user):
            context = rng.choices(contexts, weights=weights, k=1)[0]
            visit_events = generate_visit_events(user_id, context, current_time, rng)
            all_events.extend(visit_events)
            # Advance time to the next visit.
            current_time = (visit_events[-1].timestamp if visit_events else current_time) + timedelta(
                hours=rng.uniform(2, 30)
            )

    all_events.sort(key=lambda e: (e.user_id, e.timestamp))
    return all_events
