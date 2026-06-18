"""Tests for configuration management."""
import os
import pytest
from pydantic import ValidationError


def test_config_loads_from_env(monkeypatch):
    """Test configuration loads from environment variables."""
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
    monkeypatch.setenv("SLACK_PRIMARY_CHANNEL", "test-channel")
    monkeypatch.setenv("DATABASE_PATH", "test.db")

    from src.config import get_settings

    settings = get_settings()
    assert settings.slack_bot_token == "xoxb-test-token"
    assert settings.slack_primary_channel == "test-channel"
    assert settings.database_path == "test.db"


def test_config_has_defaults():
    """Test configuration has sensible defaults."""
    from src.config import Settings

    settings = Settings(
        slack_bot_token="test",
        slack_primary_channel="test"
    )

    assert settings.health_check_interval == 60
    assert settings.consecutive_failure_threshold == 3
    assert settings.daily_heartbeat_hour == 8
    assert settings.monitor_timeout == 30


def test_config_validates_required_fields():
    """Test configuration validates required fields."""
    from src.config import Settings

    with pytest.raises(ValidationError):
        Settings()  # Missing required fields
