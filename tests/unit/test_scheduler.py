"""Tests for scheduler setup."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from apscheduler.schedulers.asyncio import AsyncIOScheduler


def test_scheduler_initialization():
    """Test scheduler initializes with correct jobs."""
    from src.scheduler import init_scheduler

    scheduler = init_scheduler()

    assert scheduler is not None
    assert isinstance(scheduler, AsyncIOScheduler)

    # Check jobs are registered
    jobs = scheduler.get_jobs()
    job_names = [job.name for job in jobs]

    assert "health_check_job" in job_names
    assert "daily_heartbeat_job" in job_names
    assert "system_heartbeat_job" in job_names
    assert "system_monitor_job" in job_names


def test_health_check_job_interval():
    """Test health check job has correct interval."""
    from src.scheduler import init_scheduler
    from src.config import get_settings

    settings = get_settings()
    scheduler = init_scheduler()

    health_check_job = None
    for job in scheduler.get_jobs():
        if job.name == "health_check_job":
            health_check_job = job
            break

    assert health_check_job is not None
    # Trigger type should be interval
    assert (
        health_check_job.trigger.interval.total_seconds()
        == settings.health_check_interval
    )


def test_daily_heartbeat_job_schedule():
    """Test daily heartbeat job scheduled for 8 AM EST."""
    from src.scheduler import init_scheduler
    from src.config import get_settings

    settings = get_settings()
    scheduler = init_scheduler()

    heartbeat_job = None
    for job in scheduler.get_jobs():
        if job.name == "daily_heartbeat_job":
            heartbeat_job = job
            break

    assert heartbeat_job is not None
    # Check it's a cron trigger with correct schedule
    hour_field = None
    minute_field = None
    for field in heartbeat_job.trigger.fields:
        if field.name == "hour":
            hour_field = field
        if field.name == "minute":
            minute_field = field

    assert hour_field is not None
    assert str(hour_field) == str(settings.daily_heartbeat_hour)
    assert minute_field is not None
    assert str(minute_field) == "0"
