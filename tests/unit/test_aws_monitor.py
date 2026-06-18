"""Tests for AWS Health status monitor."""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.asyncio
async def test_aws_monitor_operational():
    """Test AWS monitor returns operational status."""
    from src.monitors.aws import AWSMonitor

    monitor = AWSMonitor()

    html_content = """
    <html>
        <body>
            <h1>AWS Health Dashboard</h1>
            <p>Service is operating normally</p>
        </body>
    </html>
    """

    with patch.object(monitor, "_http_get") as mock_get:
        mock_response = Mock()
        mock_response.text = html_content
        mock_response.elapsed.total_seconds.return_value = 0.300
        mock_get.return_value = mock_response

        result = await monitor.check_status()

        assert result.service_name == "aws"
        assert result.status == "operational"
        assert result.response_time_ms == 300
        assert result.details["indicator"] == "operational"
        assert result.details["source"] == "web_scraping"
        assert result.details["description"] == "Status: operational"
