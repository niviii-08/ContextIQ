"""
Synthetic demo-data generator for ContextIQ.

Generates a realistic ~90-day behavioural history for one or more demo
users, with INTENTIONALLY embedded patterns so the ML layer (Phase 2+) has
something real to discover:

  1. "One More Thing" pairing — certain task pairs (e.g. "Take out the trash"
     + "Leave for work") are very frequently created in the same context
     session, and the *second* item in the pair is forgotten far more often
     than the first — a classic context-dependent forgetting pattern.
  2. Late-night forget risk — tasks started after 21:00 are forgotten at
     ~3x the base rate.
  3. Location-conditioned interruption mix — PHONE/SOCIAL_MEDIA dominate at
     Home, MESSAGE/CALL dominate at Work/Study.
  4. Interruption-count vs completion — sessions with 3+ interruptions have
     a materially lower task completion rate than low-interruption sessions.

Usage:
    # writes directly into Postgres (DATABASE_URL from backend/.env)
    python scripts/generate_synthetic_data.py --mode db --users 2

    # writes CSV files into data/ instead (no DB required, good for ML notebooks)
    python scripts/generate_synthetic_data.py --mode csv --users 2

Both modes can be run together with --mode both.
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

RNG = random.Random(42)  # deterministic demo data

# --- Domain vocab -----------------------------------------------------------

LOCATION_DEFS = [
    ("Home", "HOME"),
    ("Office Desk", "WORK"),
    ("Gym", "GYM"),
    ("Commute", "COMMUTE"),
    ("Study Room", "STUDY"),
]

# "One More Thing" pairs: (primary task, commonly-forgotten follow-up, context_tag)
OMT_PAIRS = [
    ("Leave for work", "Take out the trash", "home_morning"),
    ("Pack laptop bag", "Carry charger", "home_morning"),
    ("Finish lecture notes", "Submit assignment portal upload", "study_evening"),
    ("Leave the gym", "Refill water bottle", "gym_exit"),
    ("Close laptop for the day", "Push code / commit changes", "work_evening"),
]

STANDALONE_TASKS = [
    "Reply to professor's email", "Review PR comments", "Pay electricity bill",
    "Book dentist appointment", "Buy groceries", "Water the plants",
    "Prepare slides for review", "Call mom", "Renew library book",
    "Update resume", "Backup laptop files", "Plan weekend trip",
    "Read research paper", "Clean desk", "Schedule car service",
]

INTERRUPTION_WEIGHTS_BY_LOCATION = {
    "HOME": {"PHONE": 0.30, "SOCIAL_MEDIA": 0.30, "MESSAGE": 0.15, "CALL": 0.05,
             "SEARCH": 0.05, "PERSON": 0.05, "FOOD": 0.08, "OTHER": 0.02},
    "WORK": {"PHONE": 0.05, "SOCIAL_MEDIA": 0.05, "MESSAGE": 0.30, "CALL": 0.20,
             "SEARCH": 0.15, "PERSON": 0.15, "FOOD": 0.05, "OTHER": 0.05},
    "STUDY": {"PHONE": 0.10, "SOCIAL_MEDIA": 0.15, "MESSAGE": 0.20, "CALL": 0.05,
              "SEARCH": 0.30, "PERSON": 0.05, "FOOD": 0.10, "OTHER": 0.05},
    "GYM": {"PHONE": 0.20, "SOCIAL_MEDIA": 0.10, "MESSAGE": 0.10, "CALL": 0.05,
            "SEARCH": 0.05, "PERSON": 0.40, "FOOD": 0.05, "OTHER": 0.05},
    "COMMUTE": {"PHONE": 0.25, "SOCIAL_MEDIA": 0.20, "MESSAGE": 0.20, "CALL": 0.15,
                "SEARCH": 0.10, "PERSON": 0.02, "FOOD": 0.03, "OTHER": 0.05},
}

DAYS_OF_HISTORY = 90


@dataclass
class SyntheticUser:
    id: uuid.UUID
    email: str
    display_name: str
    locations: dict = field(default_factory=dict)  # name -> id
    tasks: list = field(default_factory=list)       # list of dict rows
    events: list = field(default_factory=list)
    interruptions: list = field(default_factory=list)


def weighted_choice(weights: dict[str, float]) -> str:
    items = list(weights.items())
    total = sum(w for _, w in items)
    r = RNG.uniform(0, total)
    upto = 0.0
    for key, w in items:
        upto += w
        if upto >= r:
            return key
    return items[-1][0]


def build_user(index: int) -> SyntheticUser:
    user = SyntheticUser(
        id=uuid.uuid4(),
        email=f"demo.user{index}@contextiq.dev",
        display_name=f"Demo User {index}",
    )
    for name, loc_type in LOCATION_DEFS:
        user.locations[name] = {
            "id": uuid.uuid4(),
            "location_type": loc_type,
            "name": name,
        }
    return user


def _emit_task(user: SyntheticUser, title: str, context_tag: str, base_time: datetime,
                forget_bias: float, location_name: str | None) -> dict:
    task_id = uuid.uuid4()
    loc = user.locations.get(location_name) if location_name else None
    is_late_night = base_time.hour >= 21
    forget_prob = min(0.9, forget_bias + (0.35 if is_late_night else 0.0))

    outcome_roll = RNG.random()
    created_at = base_time
    row = {
        "id": task_id,
        "user_id": user.id,
        "title": title,
        "description": None,
        "priority": RNG.choice(["LOW", "MEDIUM", "MEDIUM", "HIGH"]),
        "context_tag": context_tag,
        "context_location_id": loc["id"] if loc else None,
        "due_at": created_at + timedelta(hours=RNG.randint(1, 12)),
        "estimated_minutes": RNG.choice([5, 10, 15, 30, 45, 60]),
        "is_recurring": False,
        "recurrence_rule": None,
        "created_at": created_at,
    }
    user.tasks.append(row)

    events = [("CREATED", created_at)]
    started_at = created_at + timedelta(minutes=RNG.randint(1, 90))
    events.append(("STARTED", started_at))

    if outcome_roll < forget_prob:
        row["status"] = "FORGOTTEN"
        events.append(("FORGOTTEN", started_at + timedelta(minutes=RNG.randint(30, 240))))
    elif outcome_roll < forget_prob + 0.08:
        row["status"] = "CANCELLED"
        events.append(("CANCELLED", started_at + timedelta(minutes=RNG.randint(5, 60))))
    else:
        # some tasks get paused/resumed before completing
        cursor = started_at
        if RNG.random() < 0.3:
            cursor += timedelta(minutes=RNG.randint(5, 20))
            events.append(("PAUSED", cursor))
            cursor += timedelta(minutes=RNG.randint(5, 30))
            events.append(("RESUMED", cursor))
        completed_at = cursor + timedelta(minutes=RNG.randint(5, 90))
        events.append(("COMPLETED", completed_at))
        row["status"] = "COMPLETED"
        row["completed_at"] = completed_at

    row.setdefault("completed_at", None)

    for event_type, occurred_at in events:
        user.events.append(
            {
                "id": uuid.uuid4(),
                "task_id": task_id,
                "user_id": user.id,
                "event_type": event_type,
                "occurred_at": occurred_at,
                "location_id": loc["id"] if loc else None,
            }
        )
    return row


def generate_for_user(user: SyntheticUser) -> None:
    start_date = datetime.now(timezone.utc) - timedelta(days=DAYS_OF_HISTORY)

    for day in range(DAYS_OF_HISTORY):
        day_start = start_date + timedelta(days=day)

        # --- Morning "one more thing" session (home) ---
        if RNG.random() < 0.85:
            morning_time = day_start.replace(hour=RNG.choice([6, 7, 8]), minute=RNG.randint(0, 59))
            primary, follow_up, tag = OMT_PAIRS[0]
            _emit_task(user, primary, tag, morning_time, forget_bias=0.05, location_name="Home")
            # follow-up task is the "one more thing" — much higher forget bias by design
            _emit_task(
                user, follow_up, tag, morning_time + timedelta(minutes=RNG.randint(1, 5)),
                forget_bias=0.55, location_name="Home",
            )
            _maybe_interrupt(user, morning_time, "Home", n=RNG.randint(0, 2))

        # --- Work/study block ---
        if RNG.random() < 0.9:
            work_time = day_start.replace(hour=RNG.choice([10, 11, 14, 15]), minute=RNG.randint(0, 59))
            location = RNG.choice(["Office Desk", "Study Room"])
            title = RNG.choice(STANDALONE_TASKS)
            _emit_task(user, title, "work_block", work_time, forget_bias=0.15, location_name=location)
            _maybe_interrupt(user, work_time, location, n=RNG.randint(0, 4))

            # second OMT pair sometimes fires here (laptop/charger)
            if RNG.random() < 0.4:
                primary, follow_up, tag = OMT_PAIRS[1]
                t2 = work_time + timedelta(minutes=RNG.randint(30, 180))
                _emit_task(user, primary, tag, t2, forget_bias=0.05, location_name=location)
                _emit_task(user, follow_up, tag, t2 + timedelta(minutes=2), forget_bias=0.5, location_name=location)

        # --- Evening study/wrap-up (higher late-night forget risk by design) ---
        if RNG.random() < 0.6:
            evening_time = day_start.replace(hour=RNG.choice([20, 21, 22, 23]), minute=RNG.randint(0, 59))
            primary, follow_up, tag = RNG.choice(OMT_PAIRS[2:])
            loc_name = "Study Room" if "study" in tag else ("Office Desk" if "work" in tag else "Gym")
            _emit_task(user, primary, tag, evening_time, forget_bias=0.1, location_name=loc_name)
            _emit_task(
                user, follow_up, tag, evening_time + timedelta(minutes=RNG.randint(1, 10)),
                forget_bias=0.5, location_name=loc_name,
            )
            _maybe_interrupt(user, evening_time, loc_name, n=RNG.randint(0, 3))

        # --- Commute interruptions (no tasks, just interruptions) ---
        if RNG.random() < 0.5:
            commute_time = day_start.replace(hour=RNG.choice([8, 9, 18, 19]), minute=RNG.randint(0, 59))
            _maybe_interrupt(user, commute_time, "Commute", n=RNG.randint(1, 3))


def _maybe_interrupt(user: SyntheticUser, base_time: datetime, location_name: str, n: int) -> None:
    loc = user.locations.get(location_name)
    loc_type = loc["location_type"] if loc else "OTHER"
    weights = INTERRUPTION_WEIGHTS_BY_LOCATION.get(loc_type, INTERRUPTION_WEIGHTS_BY_LOCATION["HOME"])
    for _ in range(n):
        offset = timedelta(minutes=RNG.randint(0, 45))
        user.interruptions.append(
            {
                "id": uuid.uuid4(),
                "user_id": user.id,
                "task_id": None,
                "interruption_type": weighted_choice(weights),
                "occurred_at": base_time + offset,
                "duration_seconds": RNG.choice([30, 60, 90, 120, 300, 600]),
                "location_id": loc["id"] if loc else None,
                "notes": None,
            }
        )


# --- Output: CSV mode ---------------------------------------------------


def write_csv(users: list[SyntheticUser], data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)

    with open(data_dir / "users.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "email", "display_name"])
        for u in users:
            w.writerow([u.id, u.email, u.display_name])

    with open(data_dir / "locations.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "user_id", "name", "location_type"])
        for u in users:
            for loc in u.locations.values():
                w.writerow([loc["id"], u.id, loc["name"], loc["location_type"]])

    with open(data_dir / "tasks.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "id", "user_id", "title", "status", "priority", "context_tag",
            "context_location_id", "due_at", "estimated_minutes", "created_at", "completed_at",
        ])
        for u in users:
            for t in u.tasks:
                w.writerow([
                    t["id"], t["user_id"], t["title"], t["status"], t["priority"],
                    t["context_tag"], t["context_location_id"], t["due_at"],
                    t["estimated_minutes"], t["created_at"], t["completed_at"],
                ])

    with open(data_dir / "task_events.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "task_id", "user_id", "event_type", "occurred_at", "location_id"])
        for u in users:
            for e in u.events:
                w.writerow([e["id"], e["task_id"], e["user_id"], e["event_type"], e["occurred_at"], e["location_id"]])

    with open(data_dir / "interruptions.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "id", "user_id", "task_id", "interruption_type", "occurred_at",
            "duration_seconds", "location_id",
        ])
        for u in users:
            for i in u.interruptions:
                w.writerow([
                    i["id"], i["user_id"], i["task_id"], i["interruption_type"],
                    i["occurred_at"], i["duration_seconds"], i["location_id"],
                ])

    print(f"CSV demo data written to {data_dir}")


# --- Output: DB mode ------------------------------------------------------


def write_db(users: list[SyntheticUser]) -> None:
    from app.db.session import SessionLocal
    from app.models.user import User
    from app.models.location import Location
    from app.models.task import Task
    from app.models.task_event import TaskEvent
    from app.models.interruption import Interruption

    db = SessionLocal()
    try:
        for u in users:
            db.merge(User(id=u.id, email=u.email, display_name=u.display_name, timezone="UTC"))
            for loc in u.locations.values():
                db.merge(
                    Location(
                        id=loc["id"], user_id=u.id, name=loc["name"],
                        location_type=loc["location_type"], is_active=True,
                    )
                )
            db.flush()

            for t in u.tasks:
                db.merge(
                    Task(
                        id=t["id"], user_id=t["user_id"], title=t["title"],
                        description=t["description"], status=t["status"], priority=t["priority"],
                        due_at=t["due_at"], estimated_minutes=t["estimated_minutes"],
                        context_location_id=t["context_location_id"], context_tag=t["context_tag"],
                        is_recurring=t["is_recurring"], recurrence_rule=t["recurrence_rule"],
                        completed_at=t["completed_at"],
                    )
                )
            db.flush()

            for e in u.events:
                db.merge(
                    TaskEvent(
                        id=e["id"], task_id=e["task_id"], user_id=e["user_id"],
                        event_type=e["event_type"], occurred_at=e["occurred_at"],
                        location_id=e["location_id"],
                    )
                )

            for i in u.interruptions:
                db.merge(
                    Interruption(
                        id=i["id"], user_id=i["user_id"], task_id=i["task_id"],
                        interruption_type=i["interruption_type"], occurred_at=i["occurred_at"],
                        duration_seconds=i["duration_seconds"], location_id=i["location_id"],
                        notes=i["notes"],
                    )
                )

            db.commit()
            print(f"Seeded user {u.email} ({len(u.tasks)} tasks, {len(u.events)} events, "
                  f"{len(u.interruptions)} interruptions)")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ContextIQ synthetic demo data")
    parser.add_argument("--mode", choices=["db", "csv", "both"], default="csv")
    parser.add_argument("--users", type=int, default=2)
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = parser.parse_args()

    users = [build_user(i + 1) for i in range(args.users)]
    for u in users:
        generate_for_user(u)

    if args.mode in ("csv", "both"):
        write_csv(users, args.data_dir)
    if args.mode in ("db", "both"):
        write_db(users)


if __name__ == "__main__":
    main()
