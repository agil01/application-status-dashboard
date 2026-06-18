"""SQLAlchemy database models."""

from datetime import datetime, UTC
from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class HealthCheck(Base):
    """Health check results table."""

    __tablename__ = "health_checks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(String(50), nullable=False, index=True)
    status = Column(
        String(20), nullable=False
    )  # operational, degraded, outage, unknown
    response_time_ms = Column(Integer, nullable=True)
    checked_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True
    )
    details = Column(Text, nullable=True)  # JSON string

    __table_args__ = (Index("idx_service_time", "service_name", "checked_at"),)

    def __repr__(self):
        return f"<HealthCheck(service={self.service_name}, status={self.status}, checked_at={self.checked_at})>"


class Incident(Base):
    """Incident tracking table."""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(String(50), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    resolved_at = Column(DateTime, nullable=True, index=True)
    severity = Column(String(20), nullable=False)  # minor, major, critical
    consecutive_failures = Column(Integer, default=0)
    notified = Column(Boolean, default=False)

    __table_args__ = (Index("idx_service_active", "service_name", "resolved_at"),)

    def __repr__(self):
        status = "active" if self.resolved_at is None else "resolved"
        return f"<Incident(service={self.service_name}, severity={self.severity}, status={status})>"


class SystemHeartbeat(Base):
    """System heartbeat tracking table."""

    __tablename__ = "system_heartbeat"

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_check_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    services_checked = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)  # healthy, degraded

    def __repr__(self):
        return (
            f"<SystemHeartbeat(last_check={self.last_check_at}, status={self.status})>"
        )


class Alert(Base):
    """Alert history table."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(
        String(20), nullable=False
    )  # outage, recovery, heartbeat, system_down
    service_name = Column(String(50), nullable=True)
    sent_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    slack_channel = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    success = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Alert(type={self.alert_type}, service={self.service_name}, sent_at={self.sent_at})>"
