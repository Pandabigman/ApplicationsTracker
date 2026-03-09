"""
Root conftest.py: provides shared fixtures for all backend tests.

Architecture:
- SQLite in-memory DB (one file per test run, wiped between tests)
- FastAPI dependency overrides for auth (bypasses Clerk) and DB
- TEST_USER_A / TEST_USER_B for isolation testing
"""
import os

# Set env vars BEFORE importing any app modules so database.py and auth.py
# don't fail during import due to missing env vars.
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/jobtracker_test")
os.environ.setdefault("CLERK_JWKS_URL", "https://test.clerk.dev/.well-known/jwks.json")
os.environ.setdefault("CLERK_SECRET_KEY", "sk_test_placeholder")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.auth import get_current_user

# ---------------------------------------------------------------------------
# Test Database – SQLite file DB (recreated per session)
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite:///./test.db"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """Create all tables once at the start of the test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session():
    """
    Provides a DB session for each test.
    All rows are deleted before the test starts so tests are isolated.
    """
    session = TestingSessionLocal()
    # Wipe data in reverse-dependency order (children before parents)
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    yield session
    session.close()


# ---------------------------------------------------------------------------
# Auth stubs
# ---------------------------------------------------------------------------

TEST_USER_A = "user_test_aaaa"
TEST_USER_B = "user_test_bbbb"


# ---------------------------------------------------------------------------
# Authenticated TestClient – all requests run as TEST_USER_A
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(db_session):
    """TestClient authenticated as TEST_USER_A with the test DB injected."""

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: TEST_USER_A

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Fixtures for cross-user isolation tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def other_user_app(db_session):
    """
    Creates an application owned by TEST_USER_B directly in the DB.
    Returns the application id so tests can try to access it as TEST_USER_A.
    """
    from app.models import Application, ActivityLog

    app_obj = Application(
        user_id=TEST_USER_B,
        company_name="B Corp",
        position_title="B Dev",
        status="Applied",
    )
    db_session.add(app_obj)
    db_session.flush()  # get PK without committing

    activity = ActivityLog(
        application_id=app_obj.id,
        activity_type="application_created",
        description="Applied to B Dev at B Corp",
        new_value="Applied",
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(app_obj)
    return app_obj.id


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

@pytest.fixture()
def make_application(client):
    """
    Returns a helper that POSTs an application as TEST_USER_A.
    Usage: app_data = make_application(company="Stripe", position="SWE")
    """
    def _make(company="Acme Corp", position="Software Engineer", status="Applied", **kwargs):
        payload = {
            "company_name": company,
            "position_title": position,
            "status": status,
            **kwargs,
        }
        r = client.post("/applications", json=payload)
        assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.json()}"
        return r.json()

    return _make
