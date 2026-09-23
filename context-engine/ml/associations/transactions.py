"""
Transaction generator.

Converts raw event histories into context-based "transactions" — i.e.
baskets of distinct task_ids completed together during a single visit
to a given context. These transactions are the input to association
rule mining (Apriori / FP-Growth).

Definition of a "visit"
------------------------
A visit to a context, for a given user, is defined as a maximal run of
events sharing the same (user_id, context) where the gap between
consecutive events does not exceed `session_gap_minutes`. This lets a
user's natural comings-and-goings (e.g. one trip to the department
covering several tasks) be captured as a single transaction, while a
later, separate trip becomes a new transaction.

Only COMPLETE events contribute tasks to a transaction (a task must
have actually been completed to count as "occurring" in that visit).
"""

from __future__ import annotations

import uuid

import pandas as pd

from app.schemas.events import RawEvent, EventType
from app.schemas.associations import ContextTransaction


def generate_transactions(
    events: list[RawEvent], session_gap_minutes: float = 60.0
) -> list[ContextTransaction]:
    if not events:
        return []

    rows = []
    for e in events:
        rows.append(
            {
                "user_id": e.user_id,
                "timestamp": pd.to_datetime(e.timestamp),
                "task_id": e.task_id,
                "context": e.context,
                "event_type": e.event_type.value if hasattr(e.event_type, "value") else e.event_type,
            }
        )
    df = pd.DataFrame(rows)
    df = df[df["event_type"] == EventType.COMPLETE.value]
    if df.empty:
        return []

    df = df.sort_values(["user_id", "context", "timestamp"]).reset_index(drop=True)

    transactions: list[ContextTransaction] = []

    for (user_id, context), group in df.groupby(["user_id", "context"]):
        group = group.sort_values("timestamp").reset_index(drop=True)
        gap_seconds = session_gap_minutes * 60.0

        current_tasks: list[str] = []
        current_start_ts = None
        last_ts = None

        def flush():
            nonlocal current_tasks, current_start_ts
            if current_tasks:
                transactions.append(
                    ContextTransaction(
                        transaction_id=str(uuid.uuid4()),
                        user_id=user_id,
                        context=context,
                        tasks=list(dict.fromkeys(current_tasks)),  # de-dup, preserve order
                        timestamp=str(current_start_ts) if current_start_ts is not None else None,
                    )
                )
            current_tasks = []
            current_start_ts = None

        for _, row in group.iterrows():
            ts = row["timestamp"]
            if last_ts is not None and (ts - last_ts).total_seconds() > gap_seconds:
                flush()
            if current_start_ts is None:
                current_start_ts = ts
            current_tasks.append(row["task_id"])
            last_ts = ts

        flush()

    return transactions


def transactions_to_basket_list(transactions: list[ContextTransaction]) -> list[list[str]]:
    """Extract just the list-of-tasks baskets, useful as direct input to
    mlxtend's TransactionEncoder."""
    return [t.tasks for t in transactions]
