"""Slack notification system."""

import logging
from datetime import datetime, UTC
from typing import Optional

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from src.config import get_settings
from src.models import Incident, Alert

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Handle Slack notifications for monitoring events."""

    def __init__(self):
        """Initialize Slack notifier."""
        settings = get_settings()
        self.client = AsyncWebClient(token=settings.slack_bot_token)
        self.primary_channel = settings.slack_primary_channel
        self.additional_channels = settings.additional_channels_list

    async def send_outage_alert(
        self, incident: Incident, display_name: str, session: Optional[object] = None
    ) -> bool:
        """Send outage alert to Slack.

        Args:
            incident: Incident object
            display_name: Human-readable service name
            session: Database session for logging

        Returns:
            True if successful, False otherwise
        """
        message = self._format_outage_message(incident, display_name)
        return await self._send_to_channels(
            message=message,
            alert_type="outage",
            service_name=incident.service_name,
            session=session,
        )

    async def send_recovery_alert(
        self, incident: Incident, display_name: str, session: Optional[object] = None
    ) -> bool:
        """Send recovery alert to Slack.

        Args:
            incident: Incident object with resolved_at set
            display_name: Human-readable service name
            session: Database session for logging

        Returns:
            True if successful, False otherwise
        """
        message = self._format_recovery_message(incident, display_name)
        return await self._send_to_channels(
            message=message,
            alert_type="recovery",
            service_name=incident.service_name,
            session=session,
        )

    async def send_daily_heartbeat(
        self,
        services_checked: int,
        incident_count: int,
        session: Optional[object] = None,
    ) -> bool:
        """Send daily heartbeat to Slack.

        Args:
            services_checked: Number of services monitored
            incident_count: Number of incidents in last 24 hours
            session: Database session for logging

        Returns:
            True if successful, False otherwise
        """
        message = self._format_heartbeat_message(services_checked, incident_count)
        return await self._send_to_channels(
            message=message, alert_type="heartbeat", service_name=None, session=session
        )

    async def send_system_alert(
        self, alert_message: str, session: Optional[object] = None
    ) -> bool:
        """Send system monitoring alert to Slack.

        Args:
            alert_message: Alert message
            session: Database session for logging

        Returns:
            True if successful, False otherwise
        """
        message = self._format_system_alert_message(alert_message)
        return await self._send_to_channels(
            message=message,
            alert_type="system_down",
            service_name=None,
            session=session,
        )

    async def _send_to_channels(
        self,
        message: str,
        alert_type: str,
        service_name: Optional[str],
        session: Optional[object] = None,
    ) -> bool:
        """Send message to all configured channels.

        Args:
            message: Message text
            alert_type: Type of alert
            service_name: Service name (if applicable)
            session: Database session for logging

        Returns:
            True if at least one send succeeded
        """
        channels = [self.primary_channel] + self.additional_channels
        success = False

        for channel in channels:
            try:
                response = await self.client.chat_postMessage(
                    channel=channel,
                    text=message,
                    unfurl_links=False,
                    unfurl_media=False,
                )

                if response["ok"]:
                    success = True
                    logger.info(f"Sent {alert_type} alert to #{channel}")

                    # Log to database if session provided
                    if session is not None:
                        alert = Alert(
                            alert_type=alert_type,
                            service_name=service_name,
                            slack_channel=channel,
                            message=message,
                            success=True,
                        )
                        session.add(alert)

            except SlackApiError as e:
                logger.error(f"Failed to send to #{channel}: {e.response['error']}")

                # Log failure to database if session provided
                if session is not None:
                    alert = Alert(
                        alert_type=alert_type,
                        service_name=service_name,
                        slack_channel=channel,
                        message=message,
                        success=False,
                    )
                    session.add(alert)

        return success

    def _format_outage_message(self, incident: Incident, display_name: str) -> str:
        """Format outage alert message.

        Args:
            incident: Incident object
            display_name: Human-readable service name

        Returns:
            Formatted message
        """
        started_time = incident.started_at.strftime("%Y-%m-%d %I:%M %p EST")

        return f"""🚨 *OUTAGE DETECTED*

*Service:* {display_name}
*Started:* {started_time}
*Consecutive Failures:* {incident.consecutive_failures}
*Severity:* {incident.severity.upper()}

The monitoring system has detected {incident.consecutive_failures} consecutive failed health checks.
"""

    def _format_recovery_message(self, incident: Incident, display_name: str) -> str:
        """Format recovery alert message.

        Args:
            incident: Incident object with resolved_at
            display_name: Human-readable service name

        Returns:
            Formatted message
        """
        if incident.resolved_at is None:
            duration = "unknown"
        else:
            delta = incident.resolved_at - incident.started_at
            minutes = int(delta.total_seconds() / 60)
            if minutes < 60:
                duration = f"{minutes} minutes"
            else:
                hours = minutes // 60
                mins = minutes % 60
                duration = f"{hours}h {mins}m"

        resolved_time = (
            incident.resolved_at.strftime("%Y-%m-%d %I:%M %p EST")
            if incident.resolved_at
            else "N/A"
        )

        return f"""✅ *SERVICE RECOVERED*

*Service:* {display_name}
*Outage Duration:* {duration}
*Resolved:* {resolved_time}

The service has returned to operational status.
"""

    def _format_heartbeat_message(
        self, services_checked: int, incident_count: int
    ) -> str:
        """Format daily heartbeat message.

        Args:
            services_checked: Number of services monitored
            incident_count: Number of incidents in last 24 hours

        Returns:
            Formatted message
        """
        now = datetime.now().strftime("%Y-%m-%d %I:%M %p EST")

        if incident_count == 0:
            status_text = f"No incidents detected in the last 24 hours. ✨"
        else:
            status_text = f"{incident_count} incident(s) in the last 24 hours."

        return f"""💚 *DAILY HEARTBEAT*

Monitoring active. {services_checked} services checked.
{status_text}

*Last check:* {now}
"""

    def _format_system_alert_message(self, alert_message: str) -> str:
        """Format system monitoring alert message.

        Args:
            alert_message: Alert message

        Returns:
            Formatted message
        """
        return f"""⚠️ *MONITORING SYSTEM ALERT*

{alert_message}

Please investigate the monitoring system.
"""
