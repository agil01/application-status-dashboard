"""Tests for Slack notification system."""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_send_outage_alert():
    """Test sending outage alert to Slack."""
    from src.notifications.slack import SlackNotifier
    from src.models import Incident

    notifier = SlackNotifier()

    incident = Incident(
        service_name="github",
        severity="major",
        consecutive_failures=3,
        started_at=datetime.now(UTC),
    )

    with patch.object(notifier.client, "chat_postMessage") as mock_post:
        mock_post.return_value = {"ok": True, "ts": "1234567890.123456"}

        await notifier.send_outage_alert(incident, "GitHub")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["channel"] == "zendesk-test"
        assert "OUTAGE DETECTED" in call_kwargs["text"]
        assert "GitHub" in call_kwargs["text"]


@pytest.mark.asyncio
async def test_send_recovery_alert():
    """Test sending recovery alert to Slack."""
    from src.notifications.slack import SlackNotifier
    from src.models import Incident

    notifier = SlackNotifier()

    started = datetime.now(UTC) - timedelta(minutes=12)
    resolved = datetime.now(UTC)

    incident = Incident(
        service_name="aws",
        severity="major",
        consecutive_failures=3,
        started_at=started,
        resolved_at=resolved,
    )

    with patch.object(notifier.client, "chat_postMessage") as mock_post:
        mock_post.return_value = {"ok": True}

        await notifier.send_recovery_alert(incident, "AWS")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert "SERVICE RECOVERED" in call_kwargs["text"]
        assert "12 minutes" in call_kwargs["text"]


@pytest.mark.asyncio
async def test_send_daily_heartbeat():
    """Test sending daily heartbeat to Slack."""
    from src.notifications.slack import SlackNotifier

    notifier = SlackNotifier()

    with patch.object(notifier.client, "chat_postMessage") as mock_post:
        mock_post.return_value = {"ok": True}

        await notifier.send_daily_heartbeat(services_checked=7, incident_count=0)

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert "DAILY HEARTBEAT" in call_kwargs["text"]
        assert "7 services" in call_kwargs["text"]
        assert "No incidents" in call_kwargs["text"]


@pytest.mark.asyncio
async def test_send_system_alert():
    """Test sending system monitoring alert to Slack."""
    from src.notifications.slack import SlackNotifier

    notifier = SlackNotifier()

    with patch.object(notifier.client, "chat_postMessage") as mock_post:
        mock_post.return_value = {"ok": True}

        await notifier.send_system_alert("Monitoring system heartbeat stale")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert "MONITORING SYSTEM ALERT" in call_kwargs["text"]
        assert "heartbeat stale" in call_kwargs["text"]
