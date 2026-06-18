"""Tests for database models and operations."""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


@pytest.fixture
def db_session():
    """Create in-memory database for testing."""
    from src.database import Base, get_engine

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    session = Session(engine)
    yield session
    session.close()


def test_create_health_check(db_session):
    """Test creating a health check record."""
    from src.models import HealthCheck

    check = HealthCheck(
        service_name="github",
        status="operational",
        response_time_ms=234,
        details='{"indicator": "none"}'
    )

    db_session.add(check)
    db_session.commit()

    saved = db_session.query(HealthCheck).filter_by(service_name="github").first()
    assert saved is not None
    assert saved.status == "operational"
    assert saved.response_time_ms == 234


def test_create_incident(db_session):
    """Test creating an incident record."""
    from src.models import Incident

    incident = Incident(
        service_name="aws",
        severity="major",
        consecutive_failures=3
    )

    db_session.add(incident)
    db_session.commit()

    saved = db_session.query(Incident).filter_by(service_name="aws").first()
    assert saved is not None
    assert saved.severity == "major"
    assert saved.consecutive_failures == 3
    assert saved.resolved_at is None


def test_resolve_incident(db_session):
    """Test resolving an incident."""
    from src.models import Incident

    incident = Incident(
        service_name="okta",
        severity="minor",
        consecutive_failures=3
    )
    db_session.add(incident)
    db_session.commit()

    incident.resolved_at = datetime.utcnow()
    db_session.commit()

    saved = db_session.query(Incident).filter_by(service_name="okta").first()
    assert saved.resolved_at is not None


def test_get_recent_health_checks(db_session):
    """Test querying recent health checks."""
    from src.models import HealthCheck

    # Create 5 health checks
    for i in range(5):
        check = HealthCheck(
            service_name="cloudflare",
            status="operational" if i < 2 else "outage",
            response_time_ms=100 + i
        )
        db_session.add(check)

    db_session.commit()

    # Get last 3 checks
    recent = (
        db_session.query(HealthCheck)
        .filter_by(service_name="cloudflare")
        .order_by(HealthCheck.checked_at.desc())
        .limit(3)
        .all()
    )

    assert len(recent) == 3
    assert all(check.status == "outage" for check in recent)
