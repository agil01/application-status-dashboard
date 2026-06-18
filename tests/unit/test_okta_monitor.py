"""Tests for Okta status monitor."""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.asyncio
async def test_okta_monitor_operational():
    """Test Okta monitor returns operational status."""
    from src.monitors.okta import OktaMonitor

    monitor = OktaMonitor()

    response_data = {
        "status": {"indicator": "none", "description": "All Systems Operational"}
    }

    with patch.object(monitor, "_http_get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = response_data
        mock_response.elapsed.total_seconds.return_value = 0.200
        mock_get.return_value = mock_response

        result = await monitor.check_status()

        assert result.service_name == "okta"
        assert result.status == "operational"
        assert result.response_time_ms == 200
