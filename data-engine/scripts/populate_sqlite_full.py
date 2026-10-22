"""
Full SQLite Database Populator for ContextIQ Data Engine.

Generates and persists:
- Users (including primary demo user 11111111-1111-1111-1111-111111111111)
- Locations
- Tasks with realistic statuses and lifecycle timestamps
- Task events
- Interruptions
- Reconstructed Context Sessions
- Behaviour Metrics
"""
import os
import sys
from pathlib import Path
from uuid import UUID

os.environ["DATABASE_URL"] = "sqlite:///./contextiq.db"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from app.database.base import Base
from app.database.session import engine, session_scope
from app.models.user import User
from app.models.location import Location
from app.models.task import Task, TaskStatus
from app.models.task_event import TaskEvent, TaskEventType
from app.models.interruption import Interruption, InterruptionType
from app.models.context_session import ContextSession
from scripts.generate_synthetic_data import SyntheticDataGenerator
from pipeline.reconstruct import reconstruct_sessions
from pipeline.populate_analytics import populate_analytics_tables

DEMO_USER_ID = "11111111-1111-1111-1111-111111111111"

def main():
    print(f"Creating tables against: {engine.url}")
    Base.metadata.create_all(bind=engine)

    print("Generating synthetic dataset (20 users, 60 days)...")
    gen = SyntheticDataGenerator(num_users=20, num_days=60, seed=42)
    frames = gen.generate()

    # Ensure user 0 is the fixed demo user
    old_id = frames["users"].iloc[0]["id"]
    frames["users"].loc[0, "id"] = DEMO_USER_ID
    frames["users"].loc[0, "email"] = "seed.demo@contextiq.dev"
    frames["users"].loc[0, "display_name"] = "Seed Demo User"

    # Remap foreign keys for user 0
    for key in ["locations", "tasks", "task_events", "interruptions"]:
        df = frames[key]
        df.loc[df["user_id"] == old_id, "user_id"] = DEMO_USER_ID

    print("Loading core records into SQLite...")
    with session_scope() as db:
        # Clear existing core records if any
        db.query(ContextSession).delete()
        db.query(Interruption).delete()
        db.query(TaskEvent).delete()
        db.query(Task).delete()
        db.query(Location).delete()
        db.query(User).delete()
        db.flush()

        for _, row in frames["users"].iterrows():
            db.add(User(
                id=UUID(row["id"]),
                email=row["email"],
                display_name=row["display_name"],
                timezone=row["timezone"],
                created_at=row["created_at"],
            ))
        db.flush()

        for _, row in frames["locations"].iterrows():
            db.add(Location(
                id=UUID(row["id"]),
                user_id=UUID(row["user_id"]),
                name=row["name"],
                location_type=row["location_type"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            ))
        db.flush()

        for _, row in frames["tasks"].iterrows():
            db.add(Task(
                id=UUID(row["id"]),
                user_id=UUID(row["user_id"]),
                location_id=UUID(row["location_id"]) if pd.notna(row["location_id"]) else None,
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
            ))
        db.flush()

        for _, row in frames["task_events"].iterrows():
            db.add(TaskEvent(
                id=UUID(row["id"]),
                user_id=UUID(row["user_id"]),
                task_id=UUID(row["task_id"]),
                location_id=UUID(row["location_id"]) if pd.notna(row["location_id"]) else None,
                event_type=TaskEventType(row["event_type"]),
                event_time=row["event_time"],
                event_metadata=None,
            ))
        db.flush()

        for _, row in frames["interruptions"].iterrows():
            db.add(Interruption(
                id=UUID(row["id"]),
                user_id=UUID(row["user_id"]),
                task_id=UUID(row["task_id"]) if pd.notna(row["task_id"]) else None,
                location_id=UUID(row["location_id"]) if pd.notna(row["location_id"]) else None,
                interruption_type=InterruptionType(row["interruption_type"]),
                source_label=row["source_label"],
                start_time=row["start_time"],
                end_time=row["end_time"] if pd.notna(row["end_time"]) else None,
                duration_seconds=int(row["duration_seconds"]) if pd.notna(row["duration_seconds"]) else None,
            ))
        db.flush()

    print("Reconstructing sessions from events & interruptions...")
    sessions_df = reconstruct_sessions(frames["task_events"], frames["interruptions"])
    print(f"Reconstructed {len(sessions_df)} sessions.")

    import uuid as _uuid
    with session_scope() as db:
        for _, row in sessions_df.iterrows():
            db.add(ContextSession(
                id=_uuid.uuid4(),
                user_id=UUID(str(row["user_id"])),
                task_id=UUID(str(row["task_id"])) if pd.notna(row.get("task_id")) else None,
                location_id=UUID(str(row["location_id"])) if pd.notna(row.get("location_id")) else None,
                session_start=row["session_start"],
                session_end=row["session_end"],
                focused_time_seconds=int(row["focused_time_seconds"]),
                interruption_time_seconds=int(row["interruption_time_seconds"]),
                resume_delay_seconds=float(row["resume_delay_seconds"]) if pd.notna(row.get("resume_delay_seconds")) else None,
                context_switch_count=int(row["context_switch_count"]),
                interruption_count=int(row["interruption_count"]),
            ))

    print("Populating behaviour metrics...")
    res = populate_analytics_tables(
        frames["tasks"], frames["task_events"], frames["interruptions"],
        sessions_df, locations_df=frames.get("locations"),
    )
    print(f"Inserted behaviour_metrics: {res}")
    print(f"Database fully loaded and verified for demo user: {DEMO_USER_ID}")

if __name__ == "__main__":
    main()
