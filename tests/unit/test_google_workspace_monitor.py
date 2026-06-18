"""Tests for Google Workspace status monitor."""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.asyncio
async def test_google_workspace_monitor_operational():
    """Test Google Workspace monitor returns operational status."""
    from src.monitors.google_workspace import GoogleWorkspaceMonitor

    monitor = GoogleWorkspaceMonitor()

    html_content = """
    <html>
        <body>
            <div class="green">Available</div>
        </body>
    </html>
    """

    with patch.object(monitor, "_http_get") as mock_get:
        mock_response = Mock()
        mock_response.text = html_content
        mock_response.elapsed.total_seconds.return_value = 0.180
        mock_get.return_value = mock_response

        result = await monitor.check_status()

        assert result.service_name == "google_workspace"
        assert result.status == "operational"
        assert result.response_time_ms == 180
        assert result.details["indicator"] == "operational"
        assert result.details["source"] == "web_scraping"
        assert result.details["description"] == "Status: operational"
