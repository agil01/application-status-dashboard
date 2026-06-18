"""Tests for GitHub status monitor."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch


@pytest.fixture
def github_response():
    """Load GitHub API response fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "github_response.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_github_monitor_operational(github_response):
    """Test GitHub monitor returns operational status."""
    from src.monitors.github import GitHubMonitor

    monitor = GitHubMonitor()

    # Mock HTTP response (use Mock, not AsyncMock, for response objects)
    with patch.object(monitor, "_http_get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = github_response
        mock_response.elapsed.total_seconds.return_value = 0.234
        mock_get.return_value = mock_response

        result = await monitor.check_status()

        assert result.service_name == "github"
        assert result.status == "operational"
        assert result.response_time_ms == 234
        assert result.details["indicator"] == "none"
        assert result.details["description"] == "All Systems Operational"


@pytest.mark.asyncio
async def test_github_monitor_outage():
    """Test GitHub monitor detects outage."""
    from src.monitors.github import GitHubMonitor

    monitor = GitHubMonitor()

    outage_response = {
        "status": {"indicator": "critical", "description": "Major Service Outage"}
    }

    with patch.object(monitor, "_http_get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = outage_response
        mock_response.elapsed.total_seconds.return_value = 0.150
        mock_get.return_value = mock_response

        result = await monitor.check_status()

        assert result.service_name == "github"
        assert result.status == "outage"
        assert result.response_time_ms == 150
        assert result.details["indicator"] == "critical"
        assert result.details["description"] == "Major Service Outage"


@pytest.mark.asyncio
async def test_github_monitor_degraded():
    """Test GitHub monitor detects degraded performance."""
    from src.monitors.github import GitHubMonitor

    monitor = GitHubMonitor()

    degraded_response = {
        "status": {"indicator": "minor", "description": "Degraded Performance"}
    }

    with patch.object(monitor, "_http_get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = degraded_response
        mock_response.elapsed.total_seconds.return_value = 0.500
        mock_get.return_value = mock_response

        result = await monitor.check_status()

        assert result.service_name == "github"
        assert result.status == "degraded"
        assert result.response_time_ms == 500
        assert result.details["indicator"] == "minor"
        assert result.details["description"] == "Degraded Performance"


@pytest.mark.asyncio
async def test_github_monitor_missing_status():
    """Test GitHub monitor handles missing status gracefully."""
    from src.monitors.github import GitHubMonitor
    from unittest.mock import Mock, patch

    monitor = GitHubMonitor()

    empty_response = {}  # No status object

    with patch.object(monitor, "_http_get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = empty_response
        mock_response.elapsed.total_seconds.return_value = 0.100
        mock_get.return_value = mock_response

        result = await monitor.check_status()

        assert result.service_name == "github"
        assert result.status == "unknown"  # Should map unknown indicator to "unknown"
        assert result.response_time_ms == 100
        assert result.details["indicator"] == "unknown"
        assert result.details["description"] == ""


@pytest.mark.asyncio
async def test_github_monitor_unknown_indicator():
    """Test GitHub monitor handles unknown indicator values."""
    from src.monitors.github import GitHubMonitor
    from unittest.mock import Mock, patch

    monitor = GitHubMonitor()

    unknown_response = {
        "status": {
            "indicator": "maintenance",  # Unknown indicator
            "description": "Scheduled Maintenance",
        }
    }

    with patch.object(monitor, "_http_get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = unknown_response
        mock_response.elapsed.total_seconds.return_value = 0.200
        mock_get.return_value = mock_response

        result = await monitor.check_status()

        assert result.service_name == "github"
        assert (
            result.status == "unknown"
        )  # BaseMonitor._map_status maps unknown indicators to "unknown"
        assert result.response_time_ms == 200
        assert result.details["indicator"] == "maintenance"
        assert result.details["description"] == "Scheduled Maintenance"
