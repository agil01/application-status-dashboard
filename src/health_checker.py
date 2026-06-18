"""Health check service for monitoring all services."""

import asyncio
import json
import logging
from datetime import datetime, timedelta, UTC
from typing import Optional

from sqlalchemy.orm import Session

from src.config import get_settings
from src.database import get_db_session
from src.models import HealthCheck, Incident, SystemHeartbeat
from src.monitors import get_all_monitors, get_monitor_by_name
from src.notifications.slack import SlackNotifier

logger = logging.getLogger(__name__)


class HealthChecker:
    """Service for executing health checks and detecting incidents."""

    def __init__(self):
        """Initialize health checker."""
        self.settings = get_settings()
        self.notifier = SlackNotifier()

    async def check_all_services(self, session: Session) -> list[HealthCheck]:
        """Check all services concurrently.

        Args:
            session: Database session

        Returns:
            List of HealthCheck results
        """
        monitors = get_all_monitors()

        # Execute all checks concurrently
        tasks = [monitor.execute_check() for monitor in monitors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        health_checks = []

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Monitor check failed: {result}")
                continue

            # Save to database
            check = HealthCheck(
                service_name=result.service_name,
                status=result.status,
                response_time_ms=result.response_time_ms,
                checked_at=result.checked_at,
                details=json.dumps(result.details),
            )
            session.add(check)
            health_checks.append(check)

        session.commit()

        logger.info(f"Completed health checks for {len(health_checks)} services")
        return health_checks

    async def detect_and_alert_incidents(self, session: Session):
        """Detect incidents and send alerts.

        Checks for:
        - 3 consecutive failures → create incident and alert
        - Recovery from incident → resolve incident and alert

        Args:
            session: Database session
        """
        monitors = get_all_monitors()

        for monitor in monitors:
            # Get last N checks
            recent_checks = (
                session.query(HealthCheck)
                .filter_by(service_name=monitor.service_name)
                .order_by(HealthCheck.checked_at.desc())
                .limit(self.settings.consecutive_failure_threshold)
                .all()
            )

            if len(recent_checks) < self.settings.consecutive_failure_threshold:
                continue

            # Check for active incident
            active_incident = (
                session.query(Incident)
                .filter_by(service_name=monitor.service_name, resolved_at=None)
                .first()
            )

            # Check if all recent checks are failures
            all_failures = all(
                check.status in ("outage", "degraded") for check in recent_checks
            )

            if all_failures:
                # Consecutive failures detected
                if active_incident is None:
                    # Create new incident
                    severity = self._determine_severity(recent_checks)
                    incident = Incident(
                        service_name=monitor.service_name,
                        severity=severity,
                        consecutive_failures=len(recent_checks),
                    )
                    session.add(incident)
                    session.commit()

                    # Send alert
                    success = await self.notifier.send_outage_alert(
                        incident, monitor.display_name, session
                    )

                    if success:
                        incident.notified = True
                        session.commit()
                        logger.warning(
                            f"Outage detected for {monitor.display_name} "
                            f"({len(recent_checks)} consecutive failures)"
                        )

                elif not active_incident.notified:
                    # Incident exists but not notified yet
                    success = await self.notifier.send_outage_alert(
                        active_incident, monitor.display_name, session
                    )

                    if success:
                        active_incident.notified = True
                        session.commit()

            else:
                # At least one success in recent checks
                if active_incident is not None:
                    # Service recovered
                    active_incident.resolved_at = datetime.now(UTC)
                    session.commit()

                    # Send recovery alert
                    await self.notifier.send_recovery_alert(
                        active_incident, monitor.display_name, session
                    )

                    logger.info(f"Service recovered: {monitor.display_name}")

    async def update_system_heartbeat(self, session: Session):
        """Update system heartbeat to indicate monitoring is alive.

        Args:
            session: Database session
        """
        heartbeat = SystemHeartbeat(
            services_checked=len(get_all_monitors()), status="healthy"
        )
        session.add(heartbeat)
        session.commit()

        logger.debug("System heartbeat updated")

    async def check_system_heartbeat(self, session: Session):
        """Check if system heartbeat is stale and alert if needed.

        Args:
            session: Database session
        """
        latest_heartbeat = (
            session.query(SystemHeartbeat)
            .order_by(SystemHeartbeat.last_check_at.desc())
            .first()
        )

        if latest_heartbeat is None:
            return

        time_since_heartbeat = datetime.now(UTC) - latest_heartbeat.last_check_at
        threshold = timedelta(seconds=self.settings.system_heartbeat_alert_threshold)

        if time_since_heartbeat > threshold:
            minutes = int(time_since_heartbeat.total_seconds() / 60)
            message = f"System heartbeat not updated for {minutes} minutes. Monitoring may be down."

            await self.notifier.send_system_alert(message, session)
            logger.error(message)

    async def send_daily_heartbeat(self, session: Session):
        """Send daily 'all clear' heartbeat to Slack.

        Args:
            session: Database session
        """
        # Count incidents in last 24 hours
        yesterday = datetime.now(UTC) - timedelta(hours=24)
        incident_count = (
            session.query(Incident).filter(Incident.started_at >= yesterday).count()
        )

        services_checked = len(get_all_monitors())

        await self.notifier.send_daily_heartbeat(
            services_checked=services_checked,
            incident_count=incident_count,
            session=session,
        )

        logger.info(
            f"Daily heartbeat sent: {services_checked} services, {incident_count} incidents"
        )

    def _determine_severity(self, checks: list[HealthCheck]) -> str:
        """Determine incident severity based on recent checks.

        Args:
            checks: Recent health checks

        Returns:
            Severity level: minor, major, or critical
        """
        # If any check shows 'outage', it's at least major
        if any(check.status == "outage" for check in checks):
            return "major"
        # If all degraded, it's minor
        elif all(check.status == "degraded" for check in checks):
            return "minor"
        else:
            return "major"
