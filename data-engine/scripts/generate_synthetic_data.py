"""
Synthetic Behavioural Dataset Generator
==========================================

Generates a reproducible synthetic dataset of users, locations, tasks,
task_events, and interruptions with REAL temporal sequences (not
independent random rows) — each task is simulated as an actual lifecycle
of events over time, and each user follows one of several distinct
behavioural personas so the resulting dataset has meaningful, learnable
structure for downstream ML work.

Usage:
    python scripts/generate_synthetic_data.py --users 50 --days 60
    python scripts/generate_synthetic_data.py --users 50 --days 60 --seed 42 --db

By default this script writes CSV files to data/synthetic/ (fast, no DB
required). Pass --db to also (or only, with --db-only) load the generated
data directly into the configured database via the ORM models.
"""
from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CATEGORIES = ["deep_work", "email", "meeting", "admin", "learning", "chores", "planning", "creative"]
LOCATIONS = ["Home Office", "Coworking Space", "Cafe", "Living Room", "Office Desk", "Commute"]
INTERRUPTION_TYPES = ["phone", "social_media", "message", "call", "search", "person", "food", "other"]

WORK_HOUR_WEIGHTS = {
    # rough shape of a working day: low overnight, ramps up 8-11, dips at
    # lunch, ramps again 13-17, tapers evening. Index = hour of day (0-23).
    0: 0.01, 1: 0.005, 2: 0.005, 3: 0.005, 4: 0.005, 5: 0.01,
    6: 0.02, 7: 0.03, 8: 0.06, 9: 0.08, 10: 0.09, 11: 0.08,
    12: 0.04, 13: 0.06, 14: 0.08, 15: 0.08, 16: 0.07, 17: 0.05,
    18: 0.03, 19: 0.02, 20: 0.02, 21: 0.015, 22: 0.01, 23: 0.005,
}
_HOURS = list(WORK_HOUR_WEIGHTS.keys())
_HOUR_PROBS = np.array(list(WORK_HOUR_WEIGHTS.values()))
_HOUR_PROBS = _HOUR_PROBS / _HOUR_PROBS.sum()


@dataclass
class Persona:
    name: str
    forgetting_prob: float          # chance a started task is later forgotten instead of completed
    cancel_prob: float              # chance a task is cancelled outright
    interruption_rate: float        # expected interruptions per active hour
    context_switch_bias: float      # chance a pause->resume gap is "long" (real context switch)
    preferred_locations: list[str]
    location_forgetting_boost: dict = field(default_factory=dict)  # location -> extra forgetting prob
    tasks_per_day_lambda: float = 4.0
    avg_task_minutes: float = 35.0


PERSONAS: list[Persona] = [
    Persona(
        name="frequent_forgetter",
        forgetting_prob=0.42,
        cancel_prob=0.05,
        interruption_rate=1.2,
        context_switch_bias=0.35,
        preferred_locations=["Home Office", "Living Room"],
        tasks_per_day_lambda=5.0,
    ),
    Persona(
        name="frequent_interrupter",
        forgetting_prob=0.15,
        cancel_prob=0.05,
        interruption_rate=3.5,
        context_switch_bias=0.5,
        preferred_locations=["Cafe", "Coworking Space"],
        tasks_per_day_lambda=4.5,
    ),
    Persona(
        name="location_dependent_forgetter",
        forgetting_prob=0.12,
        cancel_prob=0.04,
        interruption_rate=1.0,
        context_switch_bias=0.3,
        preferred_locations=["Commute", "Cafe", "Home Office"],
        location_forgetting_boost={"Commute": 0.45, "Cafe": 0.15},
        tasks_per_day_lambda=4.0,
    ),
    Persona(
        name="high_focus_user",
        forgetting_prob=0.05,
        cancel_prob=0.02,
        interruption_rate=0.4,
        context_switch_bias=0.1,
        preferred_locations=["Home Office", "Office Desk"],
        tasks_per_day_lambda=3.5,
        avg_task_minutes=55.0,
    ),
    Persona(
        name="high_context_switch_user",
        forgetting_prob=0.18,
        cancel_prob=0.06,
        interruption_rate=1.8,
        context_switch_bias=0.7,
        preferred_locations=["Office Desk", "Coworking Space", "Cafe"],
        tasks_per_day_lambda=6.0,
        avg_task_minutes=25.0,
    ),
]


def weighted_hour(rng: random.Random) -> int:
    return rng.choices(_HOURS, weights=_HOUR_PROBS.tolist(), k=1)[0]


class SyntheticDataGenerator:
    def __init__(self, num_users: int, num_days: int, seed: int):
        self.num_users = num_users
        self.num_days = num_days
        self.seed = seed
        self.rng = random.Random(seed)

        self.start_date = datetime.now(timezone.utc) - timedelta(days=num_days)

        self.users: list[dict] = []
        self.locations: list[dict] = []
        self.tasks: list[dict] = []
        self.task_events: list[dict] = []
        self.interruptions: list[dict] = []

    # -- setup ------------------------------------------------------------

    def _make_users_and_locations(self):
        for i in range(self.num_users):
            persona = PERSONAS[i % len(PERSONAS)]
            user_id = str(uuid4())
            self.users.append(
                {
                    "id": user_id,
                    "email": f"user{i+1}@example.com",
                    "display_name": f"Synthetic User {i+1}",
                    "timezone": "UTC",
                    "persona": persona.name,
                    "created_at": self.start_date,
                }
            )
            user_locations = {}
            for label in persona.preferred_locations:
                loc_id = str(uuid4())
                user_locations[label] = loc_id
                self.locations.append(
                    {
                        "id": loc_id,
                        "user_id": user_id,
                        "name": label,
                        "location_type": "OTHER",
                        "latitude": None,
                        "longitude": None,
                        "created_at": self.start_date,
                        "updated_at": self.start_date,
                    }
                )
            # store mapping for later use
            self._user_location_map = getattr(self, "_user_location_map", {})
            self._user_location_map[user_id] = user_locations

    # -- core simulation ----------------------------------------------------

    def _simulate_user(self, user: dict, persona: Persona):
        user_id = user["id"]
        user_locations = self._user_location_map[user_id]

        for day_offset in range(self.num_days):
            day = self.start_date + timedelta(days=day_offset)
            n_tasks = max(0, int(np.random.poisson(persona.tasks_per_day_lambda)))

            for _ in range(n_tasks):
                self._simulate_task(user_id, persona, user_locations, day)

    def _simulate_task(self, user_id: str, persona: Persona, user_locations: dict, day: datetime):
        category = self.rng.choice(CATEGORIES)
        location_label = self.rng.choice(persona.preferred_locations)
        location_id = user_locations[location_label]

        hour = weighted_hour(self.rng)
        minute = self.rng.randint(0, 59)
        created_at = day.replace(hour=hour, minute=minute, second=0, microsecond=0)

        task_id = str(uuid4())
        priority = self.rng.randint(1, 5)
        deadline_at = None
        if self.rng.random() < 0.4:
            deadline_at = created_at + timedelta(hours=self.rng.randint(2, 72))

        self.tasks.append(
            {
                "id": task_id,
                "user_id": user_id,
                "location_id": location_id,
                "title": f"{category.replace('_', ' ').title()} task {task_id[:8]}",
                "category": category,
                "priority": priority,
                "status": "created",  # will be overwritten below
                "deadline_at": deadline_at,
                "created_at": created_at,
            }
        )
        self.task_events.append(self._event(user_id, task_id, "created", created_at, location_id))

        # Determine outcome for this task lifecycle.
        forgetting_prob = persona.forgetting_prob + persona.location_forgetting_boost.get(location_label, 0.0)
        forgetting_prob = min(0.9, forgetting_prob)
        roll = self.rng.random()

        current_time = created_at + timedelta(minutes=self.rng.randint(1, 30))

        if roll < persona.cancel_prob:
            # created -> cancelled, no real work session.
            self.task_events.append(self._event(user_id, task_id, "cancelled", current_time, location_id))
            self._set_task_terminal(task_id, "cancelled", cancelled_at=current_time)
            return

        if roll < persona.cancel_prob + forgetting_prob:
            # created -> (maybe started) -> forgotten (no completion, task
            # trails off; simulate 0-2 short work sessions before it's dropped).
            n_sessions = self.rng.randint(0, 2)
            t = current_time
            started_at = None
            for s in range(n_sessions):
                self.task_events.append(self._event(user_id, task_id, "started", t, location_id))
                if started_at is None:
                    started_at = t
                session_minutes = max(3, int(np.random.exponential(persona.avg_task_minutes / 2)))
                self._simulate_interruptions_during(user_id, task_id, persona, location_id, t, session_minutes)
                t = t + timedelta(minutes=session_minutes)
                self.task_events.append(self._event(user_id, task_id, "paused", t, location_id))
                gap_hours = self.rng.uniform(1, 48)
                t = t + timedelta(hours=gap_hours)

            forgotten_at = t
            self.task_events.append(self._event(user_id, task_id, "forgotten", forgotten_at, location_id))
            self._set_task_terminal(task_id, "forgotten", started_at=started_at, forgotten_at=forgotten_at)
            return

        # Otherwise: completed, with 1-3 work sessions (some with a genuine
        # pause/resume in the middle, governed by context_switch_bias).
        n_sessions = self.rng.randint(1, 3)
        t = current_time
        started_at = None
        for s in range(n_sessions):
            self.task_events.append(self._event(user_id, task_id, "started" if s == 0 else "resumed", t, location_id))
            if started_at is None:
                started_at = t
            session_minutes = max(5, int(np.random.exponential(persona.avg_task_minutes)))
            self._simulate_interruptions_during(user_id, task_id, persona, location_id, t, session_minutes)
            t = t + timedelta(minutes=session_minutes)

            is_last = s == n_sessions - 1
            if is_last:
                self.task_events.append(self._event(user_id, task_id, "completed", t, location_id))
                self._set_task_terminal(task_id, "completed", started_at=started_at, completed_at=t)
            else:
                self.task_events.append(self._event(user_id, task_id, "paused", t, location_id))
                # Gap length reflects context_switch_bias: biased personas
                # take longer, more disruptive breaks more often.
                if self.rng.random() < persona.context_switch_bias:
                    gap_minutes = self.rng.uniform(20, 240)  # a "real" context switch
                else:
                    gap_minutes = self.rng.uniform(1, 15)  # a quick breather
                t = t + timedelta(minutes=gap_minutes)

    def _simulate_interruptions_during(self, user_id, task_id, persona: Persona, location_id, session_start, session_minutes):
        expected = persona.interruption_rate * (session_minutes / 60.0)
        n_interruptions = np.random.poisson(max(0.0, expected))
        for _ in range(n_interruptions):
            offset_minutes = self.rng.uniform(0, max(1, session_minutes))
            start = session_start + timedelta(minutes=offset_minutes)
            duration = max(5, int(np.random.exponential(90)))  # seconds
            end = start + timedelta(seconds=duration)
            i_type = self.rng.choice(INTERRUPTION_TYPES)
            self.interruptions.append(
                {
                    "id": str(uuid4()),
                    "user_id": user_id,
                    "task_id": task_id,
                    "location_id": location_id,
                    "interruption_type": i_type,
                    "source_label": None,
                    "start_time": start,
                    "end_time": end,
                    "duration_seconds": duration,
                }
            )

    def _event(self, user_id, task_id, event_type, event_time, location_id):
        return {
            "id": str(uuid4()),
            "user_id": user_id,
            "task_id": task_id,
            "location_id": location_id,
            "event_type": event_type,
            "event_time": event_time,
            "event_metadata": None,
        }

    def _set_task_terminal(self, task_id: str, status: str, **timestamps):
        for t in self.tasks:
            if t["id"] == task_id:
                t["status"] = status
                t.update(timestamps)
                break

    # -- entrypoint -----------------------------------------------------

    def generate(self) -> dict[str, pd.DataFrame]:
        # Seed immediately before generation (not in __init__) so that
        # constructing multiple generator instances ahead of time can never
        # cause one generator's draws to perturb another's reproducibility.
        random.seed(self.seed)
        self.rng = random.Random(self.seed)
        np.random.seed(self.seed)

        self._make_users_and_locations()
        persona_by_name = {p.name: p for p in PERSONAS}
        for user in self.users:
            persona = persona_by_name[user["persona"]]
            self._simulate_user(user, persona)

        return {
            "users": pd.DataFrame(self.users),
            "locations": pd.DataFrame(self.locations),
            "tasks": pd.DataFrame(self.tasks),
            "task_events": pd.DataFrame(self.task_events),
            "interruptions": pd.DataFrame(self.interruptions),
        }


def write_csv(frames: dict[str, pd.DataFrame], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, df in frames.items():
        path = out_dir / f"{name}.csv"
        df.to_csv(path, index=False)
        print(f"Wrote {len(df):>7} rows -> {path}")


def load_into_db(frames: dict[str, pd.DataFrame]) -> None:
    from app.database.base import Base
    from app.database.session import engine, session_scope
    from app.models.user import User
    from app.models.location import Location
    from app.models.task import Task, TaskStatus
    from app.models.task_event import TaskEvent, TaskEventType
    from app.models.interruption import Interruption, InterruptionType

    Base.metadata.create_all(bind=engine)

    with session_scope() as db:
        for _, row in frames["users"].iterrows():
            db.add(
                User(
                    id=row["id"],
                    email=row["email"],
                    display_name=row["display_name"],
                    timezone=row["timezone"],
                    created_at=row["created_at"],
                )
            )
        db.flush()

        for _, row in frames["locations"].iterrows():
            db.add(
                Location(
                    id=row["id"],
                    user_id=row["user_id"],
                    name=row["name"],
                    location_type=row["location_type"],
                    latitude=row["latitude"],
                    longitude=row["longitude"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        db.flush()

        for _, row in frames["tasks"].iterrows():
            db.add(
                Task(
                    id=row["id"],
                    user_id=row["user_id"],
                    location_id=row["location_id"],
                    title=row["title"],
                    category=row["category"],
                    priority=int(row["priority"]),
                    status=TaskStatus(row["status"]),
                    deadline_at=row["deadline_at"] if pd.notna(row["deadline_at"]) else None,
                    created_at=row["created_at"],
                    started_at=row.get("started_at") if pd.notna(row.get("started_at")) else None,
                    completed_at=row.get("completed_at") if pd.notna(row.get("completed_at")) else None,
                    forgotten_at=row.get("forgotten_at") if pd.notna(row.get("forgotten_at")) else None,
                    cancelled_at=row.get("cancelled_at") if pd.notna(row.get("cancelled_at")) else None,
                )
            )
        db.flush()

        for _, row in frames["task_events"].iterrows():
            db.add(
                TaskEvent(
                    id=row["id"],
                    user_id=row["user_id"],
                    task_id=row["task_id"],
                    location_id=row["location_id"] if pd.notna(row["location_id"]) else None,
                    event_type=TaskEventType(row["event_type"]),
                    event_time=row["event_time"],
                    event_metadata=None,
                )
            )
        db.flush()

        for _, row in frames["interruptions"].iterrows():
            db.add(
                Interruption(
                    id=row["id"],
                    user_id=row["user_id"],
                    task_id=row["task_id"] if pd.notna(row["task_id"]) else None,
                    location_id=row["location_id"] if pd.notna(row["location_id"]) else None,
                    interruption_type=InterruptionType(row["interruption_type"]),
                    source_label=row["source_label"],
                    start_time=row["start_time"],
                    end_time=row["end_time"] if pd.notna(row["end_time"]) else None,
                    duration_seconds=int(row["duration_seconds"]) if pd.notna(row["duration_seconds"]) else None,
                )
            )

    print("Synthetic dataset loaded into database successfully.")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic ContextIQ behavioural data")
    parser.add_argument("--users", type=int, default=50)
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, default="data/synthetic")
    parser.add_argument("--db", action="store_true", help="Also load the generated data into the database")
    parser.add_argument("--db-only", action="store_true", help="Load into DB only, skip CSV output")
    args = parser.parse_args()

    generator = SyntheticDataGenerator(num_users=args.users, num_days=args.days, seed=args.seed)
    frames = generator.generate()

    total_events = len(frames["task_events"]) + len(frames["interruptions"])
    print(f"Generated: {len(frames['users'])} users, {len(frames['tasks'])} tasks, "
          f"{len(frames['task_events'])} task_events, {len(frames['interruptions'])} interruptions "
          f"(total raw events: {total_events})")

    if not args.db_only:
        write_csv(frames, Path(args.out))

    if args.db or args.db_only:
        load_into_db(frames)


if __name__ == "__main__":
    main()
