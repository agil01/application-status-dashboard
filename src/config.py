"""Application configuration management."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # Slack Configuration
    slack_bot_token: str = Field(..., description="Slack bot token")
    slack_primary_channel: str = Field(
        ..., description="Primary Slack channel for notifications"
    )
    slack_additional_channels: str = Field(
        default="", description="Comma-separated additional channels"
    )

    # Database
    database_path: str = Field(
        default="data/status.db", description="SQLite database path"
    )

    # Monitoring Settings
    health_check_interval: int = Field(
        default=60, gt=0, description="Health check interval in seconds"
    )
    consecutive_failure_threshold: int = Field(
        default=3, gt=0, description="Number of consecutive failures before alert"
    )
    daily_heartbeat_hour: int = Field(
        default=8, ge=0, le=23, description="Hour for daily heartbeat (0-23)"
    )
    daily_heartbeat_timezone: str = Field(
        default="America/New_York", description="Timezone for daily heartbeat"
    )
    system_heartbeat_interval: int = Field(
        default=300, gt=0, description="System heartbeat interval in seconds"
    )
    system_heartbeat_alert_threshold: int = Field(
        default=900, gt=0, description="Alert if heartbeat stale (seconds)"
    )

    # Monitor Timeouts
    monitor_timeout: int = Field(
        default=30, gt=0, description="Monitor request timeout in seconds"
    )
    monitor_max_retries: int = Field(
        default=1, ge=0, description="Maximum retries for failed requests"
    )

    # Dashboard
    dashboard_poll_interval: int = Field(
        default=120, gt=0, description="Dashboard poll interval in seconds"
    )
    enable_sse: bool = Field(default=True, description="Enable Server-Sent Events")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, gt=0, le=65535, description="Server port")

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    log_file: str = Field(default="logs/application.log", description="Log file path")

    @property
    def additional_channels_list(self) -> list[str]:
        """Parse additional channels from comma-separated string."""
        if not self.slack_additional_channels:
            return []
        return [
            ch.strip() for ch in self.slack_additional_channels.split(",") if ch.strip()
        ]

    @property
    def all_slack_channels(self) -> list[str]:
        """Get all Slack channels (primary + additional)."""
        return [self.slack_primary_channel] + self.additional_channels_list


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
