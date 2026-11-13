"""
ContextIQ PostgreSQL Database Viewer Helper
Run anytime with: python view_database.py
"""
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg://postgres:Pujnivi%403587@localhost:5433/dataproject"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("=" * 70)
        print("  CONTEXTIQ POSTGRESQL DATABASE (localhost:5433/dataproject)")
        print("=" * 70)

        # 1. Table Counts
        tables = ['users', 'tasks', 'task_events', 'locations', 'predictions', 'recommendations', 'behaviour_metrics']
        print("\n--- TABLE ROW COUNTS ---")
        for t in tables:
            try:
                cnt = conn.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar()
                print(f"  * {t:<22}: {cnt} rows")
            except Exception as e:
                print(f"  * {t:<22}: Error ({e})")

        # 2. Users Table
        print("\n--- REGISTERED USERS ---")
        users = conn.execute(text("SELECT id, display_name, email, role_persona, custom_title, organization, primary_occupation FROM users")).fetchall()
        for u in users:
            print(f"  ID: {u[0]}")
            print(f"  Name: {u[1]} | Email: {u[2]}")
            print(f"  Role: {u[3]} | Title: {u[4]} | Org: {u[5]}")
            print(f"  Occupation: {u[6]}")
            print("  " + "-" * 50)

        # 3. Tasks Table Sample
        print("\n--- RECENT TASKS & CHORES ---")
        tasks = conn.execute(text("SELECT id, title, context_tag, priority, status FROM tasks ORDER BY created_at DESC LIMIT 15")).fetchall()
        for t in tasks:
            print(f"  * [{t[2] or 'General'}] {t[1]} ({t[3]}, Status: {t[4]})")

        print("=" * 70)
except Exception as e:
    print("Database Connection Error:", e)
