"""Create all tables against the configured DATABASE_URL.

Usage:
    python scripts/init_db.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.base import Base
from app.database.session import engine
import app.models  # noqa: F401


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print(f"Tables created successfully against: {engine.url}")


if __name__ == "__main__":
    main()
