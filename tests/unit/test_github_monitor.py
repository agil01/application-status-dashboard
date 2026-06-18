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

        assert result.status == "outage"
        assert result.details["indicator"] == "critical"


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

        assert result.status == "degraded"
