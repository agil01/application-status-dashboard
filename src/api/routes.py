"""API routes for status dashboard."""

import json
from datetime import datetime, timedelta, UTC
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.models import HealthCheck, Incident, SystemHeartbeat
from src.monitors import get_all_monitors

router = APIRouter(prefix="/api")


class ServiceStatus(BaseModel):
    """Service status response model."""

    service_name: str
    display_name: str
    status: str
    response_time_ms: Optional[int]
    last_checked: Optional[datetime]
    has_active_incident: bool
    status_url: str


class IncidentResponse(BaseModel):
    """Incident response model."""

    service_name: str
    severity: str
    started_at: datetime
    resolved_at: Optional[datetime]
    consecutive_failures: int


class DashboardStatus(BaseModel):
    """Dashboard status response."""

    services: List[ServiceStatus]
    active_incidents: int
    total_services: int
    last_updated: datetime


@router.get("/status", response_model=DashboardStatus)
async def get_status():
    """Get current status of all services."""
    with get_db_session() as session:
        monitors = get_all_monitors()
        services = []

        for monitor in monitors:
            # Get latest health check
            latest_check = (
                session.query(HealthCheck)
                .filter_by(service_name=monitor.service_name)
                .order_by(HealthCheck.checked_at.desc())
                .first()
            )

            # Check for active incident
            active_incident = (
                session.query(Incident)
                .filter_by(service_name=monitor.service_name, resolved_at=None)
                .first()
            )

            services.append(
                ServiceStatus(
                    service_name=monitor.service_name,
                    display_name=monitor.display_name,
                    status=latest_check.status if latest_check else "unknown",
                    response_time_ms=(
                        latest_check.response_time_ms if latest_check else None
                    ),
                    last_checked=latest_check.checked_at if latest_check else None,
                    has_active_incident=active_incident is not None,
                    status_url=monitor.url,
                )
            )

        active_incidents_count = (
            session.query(Incident).filter_by(resolved_at=None).count()
        )

        return DashboardStatus(
            services=services,
            active_incidents=active_incidents_count,
            total_services=len(monitors),
            last_updated=datetime.now(UTC),
        )


@router.get("/incidents", response_model=List[IncidentResponse])
async def get_incidents(active_only: bool = False):
    """Get incidents (active or all)."""
    with get_db_session() as session:
        query = session.query(Incident)

        if active_only:
            query = query.filter_by(resolved_at=None)

        incidents = query.order_by(Incident.started_at.desc()).limit(50).all()

        return [
            IncidentResponse(
                service_name=inc.service_name,
                severity=inc.severity,
                started_at=inc.started_at,
                resolved_at=inc.resolved_at,
                consecutive_failures=inc.consecutive_failures,
            )
            for inc in incidents
        ]


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    with get_db_session() as session:
        # Check system heartbeat
        latest_heartbeat = (
            session.query(SystemHeartbeat)
            .order_by(SystemHeartbeat.last_check_at.desc())
            .first()
        )

        if latest_heartbeat:
            time_since = datetime.now(UTC) - latest_heartbeat.last_check_at
            healthy = time_since < timedelta(minutes=10)
        else:
            healthy = False

        return {
            "status": "healthy" if healthy else "degraded",
            "timestamp": datetime.now(UTC).isoformat(),
            "services_monitored": len(get_all_monitors()),
        }
