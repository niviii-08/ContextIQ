import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.database.base import Base  # noqa: E402
from app.database.session import get_db  # noqa: E402
import app.models  # noqa: E402,F401


@pytest.fixture()
def db_engine(tmp_path):
    """A fresh, file-backed SQLite database per test (avoids cross-test
    state leakage while still exercising real SQL, not just mocks)."""
    db_path = tmp_path / f"test_{uuid.uuid4().hex}.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    TestSessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)
    session = TestSessionLocal()
    yield session
    session.close()


@pytest.fixture()
def client(db_engine):
    """FastAPI TestClient wired to the isolated per-test database."""
    from fastapi.testclient import TestClient
    from app.main import app

    TestSessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)

    def _override_get_db():
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_user(db_session):
    from app.models.user import User

    user = User(email="test@example.com", display_name="Test User", timezone="UTC")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def sample_location(db_session, sample_user):
    from app.models.location import Location

    location = Location(user_id=sample_user.id, label="Home Office")
    db_session.add(location)
    db_session.commit()
    db_session.refresh(location)
    return location


def utc(*args, **kwargs) -> datetime:
    """Helper to build tz-aware UTC datetimes tersely in tests."""
    if args:
        return datetime(*args, tzinfo=timezone.utc)
    return datetime.now(timezone.utc)
