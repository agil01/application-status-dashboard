"""Tests for Athena Health status monitor."""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.asyncio
async def test_athena_monitor_operational():
    """Test Athena monitor returns operational status."""
    from src.monitors.athena import AthenaMonitor

    monitor = AthenaMonitor()

    html_content = """
    <html>
        <body>
            <div class="status">All systems operational</div>
        </body>
    </html>
    """

    with patch.object(monitor, "_http_get") as mock_get:
        mock_response = Mock()
        mock_response.text = html_content
        mock_response.elapsed.total_seconds.return_value = 0.250
        mock_get.return_value = mock_response

        result = await monitor.check_status()

        assert result.service_name == "athena"
        assert result.status == "operational"
