"""Tests for Zscaler status monitor."""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.asyncio
async def test_zscaler_monitor_operational():
    """Test Zscaler monitor returns operational status."""
    from src.monitors.zscaler import ZscalerMonitor

    monitor = ZscalerMonitor()

    html_content = """
    <html>
        <body>
            <h1>Zscaler Trust</h1>
            <p>All systems operational</p>
        </body>
    </html>
    """

    with patch.object(monitor, "_http_get") as mock_get:
        mock_response = Mock()
        mock_response.text = html_content
        mock_response.elapsed.total_seconds.return_value = 0.220
        mock_get.return_value = mock_response

        result = await monitor.check_status()

        assert result.service_name == "zscaler"
        assert result.status == "operational"
        assert result.response_time_ms == 220
        assert result.details["indicator"] == "operational"
        assert result.details["source"] == "web_scraping"
        assert result.details["description"] == "Status: operational"
