"""APScheduler setup and job definitions."""

import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pytz import timezone

from src.config import get_settings
from src.database import get_db_session
from src.health_checker import HealthChecker

logger = logging.getLogger(__name__)


async def health_check_job():
    """Job to execute health checks for all services."""
    logger.info("Running health check job")

    checker = HealthChecker()

    with get_db_session() as session:
        # Check all services
        await checker.check_all_services(session)

        # Detect and alert on incidents
        await checker.detect_and_alert_incidents(session)


async def daily_heartbeat_job():
    """Job to send daily heartbeat at 8 AM EST."""
    logger.info("Running daily heartbeat job")

    checker = HealthChecker()

    with get_db_session() as session:
        await checker.send_daily_heartbeat(session)


async def system_heartbeat_job():
    """Job to update system heartbeat every 5 minutes."""
    logger.debug("Running system heartbeat job")

    checker = HealthChecker()

    with get_db_session() as session:
        await checker.update_system_heartbeat(session)


async def system_monitor_job():
    """Job to check if system heartbeat is stale."""
    logger.debug("Running system monitor job")

    checker = HealthChecker()

    with get_db_session() as session:
        await checker.check_system_heartbeat(session)


def init_scheduler() -> AsyncIOScheduler:
    """Initialize APScheduler with all jobs.

    Returns:
        Configured scheduler instance
    """
    settings = get_settings()

    scheduler = AsyncIOScheduler(timezone=timezone(settings.daily_heartbeat_timezone))

    # Health check job - runs every 60 seconds (or configured interval)
    scheduler.add_job(
        health_check_job,
        trigger=IntervalTrigger(seconds=settings.health_check_interval),
        id="health_check_job",
        name="health_check_job",
        replace_existing=True,
        misfire_grace_time=300,  # 5 minutes
    )

    # Daily heartbeat job - runs at 8 AM EST (or configured time)
    scheduler.add_job(
        daily_heartbeat_job,
        trigger=CronTrigger(
            hour=settings.daily_heartbeat_hour,
            minute=0,
            timezone=timezone(settings.daily_heartbeat_timezone),
        ),
        id="daily_heartbeat_job",
        name="daily_heartbeat_job",
        replace_existing=True,
    )

    # System heartbeat job - runs every 5 minutes
    scheduler.add_job(
        system_heartbeat_job,
        trigger=IntervalTrigger(seconds=settings.system_heartbeat_interval),
        id="system_heartbeat_job",
        name="system_heartbeat_job",
        replace_existing=True,
    )

    # System monitor job - checks heartbeat every 15 minutes
    scheduler.add_job(
        system_monitor_job,
        trigger=IntervalTrigger(seconds=settings.system_heartbeat_alert_threshold),
        id="system_monitor_job",
        name="system_monitor_job",
        replace_existing=True,
    )

    logger.info("Scheduler initialized with 4 jobs")
    return scheduler
