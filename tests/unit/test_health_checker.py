"""Tests for health check service."""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


@pytest.fixture
def db_session():
    """Create in-memory database for testing."""
    from src.database import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    session = Session(engine)
    yield session
    session.close()


@pytest.mark.asyncio
async def test_check_all_services(db_session):
    """Test checking all services."""
    from src.health_checker import HealthChecker
    from src.models import HealthCheck
    from src.monitors.base import HealthCheckResult

    checker = HealthChecker()

    # Mock monitor results
    mock_result = HealthCheckResult(
        service_name="github",
        status="operational",
        response_time_ms=234,
        details={"test": "data"},
    )

    with patch("src.health_checker.get_all_monitors") as mock_get_monitors:
        mock_monitor = AsyncMock()
        mock_monitor.service_name = "github"
        mock_monitor.execute_check.return_value = mock_result
        mock_get_monitors.return_value = [mock_monitor]

        await checker.check_all_services(db_session)

        # Verify health check was saved
        check = db_session.query(HealthCheck).filter_by(service_name="github").first()
        assert check is not None
        assert check.status == "operational"
        assert check.response_time_ms == 234


@pytest.mark.asyncio
async def test_detect_outage_after_three_failures(db_session):
    """Test outage detection after 3 consecutive failures."""
    from src.health_checker import HealthChecker
    from src.models import HealthCheck, Incident

    checker = HealthChecker()

    # Create 3 consecutive failures
    for i in range(3):
        check = HealthCheck(
            service_name="aws",
            status="outage",
            response_time_ms=0,
            checked_at=datetime.now(UTC) - timedelta(minutes=3 - i),
        )
        db_session.add(check)
    db_session.commit()

    with patch("src.health_checker.get_all_monitors") as mock_get_monitors:
        mock_monitor = AsyncMock()
        mock_monitor.service_name = "aws"
        mock_monitor.display_name = "AWS"
        mock_get_monitors.return_value = [mock_monitor]

        with patch(
            "src.notifications.slack.SlackNotifier.send_outage_alert"
        ) as mock_alert:
            mock_alert.return_value = True

            incident = await checker.detect_and_alert_incidents(db_session)

            # Verify incident created
            incidents = db_session.query(Incident).filter_by(service_name="aws").all()
            assert len(incidents) == 1
            assert incidents[0].consecutive_failures == 3
            assert incidents[0].notified is True


@pytest.mark.asyncio
async def test_detect_recovery(db_session):
    """Test recovery detection."""
    from src.health_checker import HealthChecker
    from src.models import HealthCheck, Incident

    checker = HealthChecker()

    # Create active incident
    incident = Incident(
        service_name="okta", severity="major", consecutive_failures=3, notified=True
    )
    db_session.add(incident)

    # Create 3 recovery checks (need 3 to meet threshold)
    for i in range(3):
        check = HealthCheck(
            service_name="okta",
            status="operational",
            response_time_ms=200,
            checked_at=datetime.now(UTC) - timedelta(minutes=3 - i),
        )
        db_session.add(check)
    db_session.commit()

    with patch("src.health_checker.get_all_monitors") as mock_get_monitors:
        mock_monitor = AsyncMock()
        mock_monitor.service_name = "okta"
        mock_monitor.display_name = "Okta"
        mock_get_monitors.return_value = [mock_monitor]

        with patch(
            "src.notifications.slack.SlackNotifier.send_recovery_alert"
        ) as mock_alert:
            mock_alert.return_value = True

            await checker.detect_and_alert_incidents(db_session)

            # Verify incident resolved
            db_session.refresh(incident)
            assert incident.resolved_at is not None


@pytest.mark.asyncio
async def test_no_duplicate_alerts(db_session):
    """Test no duplicate alerts for same incident."""
    from src.health_checker import HealthChecker
    from src.models import HealthCheck, Incident

    checker = HealthChecker()

    # Create existing notified incident
    incident = Incident(
        service_name="cloudflare",
        severity="major",
        consecutive_failures=3,
        notified=True,
    )
    db_session.add(incident)

    # Create more failures
    for i in range(3):
        check = HealthCheck(
            service_name="cloudflare", status="outage", response_time_ms=0
        )
        db_session.add(check)
    db_session.commit()

    with patch("src.health_checker.get_all_monitors") as mock_get_monitors:
        mock_monitor = AsyncMock()
        mock_monitor.service_name = "cloudflare"
        mock_monitor.display_name = "Cloudflare"
        mock_get_monitors.return_value = [mock_monitor]

        with patch(
            "src.notifications.slack.SlackNotifier.send_outage_alert"
        ) as mock_alert:
            await checker.detect_and_alert_incidents(db_session)

            # Should not send duplicate alert
            mock_alert.assert_not_called()
