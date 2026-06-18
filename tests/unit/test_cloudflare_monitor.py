"""Tests for Cloudflare status monitor."""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.asyncio
async def test_cloudflare_monitor_operational():
    """Test Cloudflare monitor returns operational status."""
    from src.monitors.cloudflare import CloudflareMonitor

    monitor = CloudflareMonitor()

    response_data = {
        "status": {"indicator": "none", "description": "All Systems Operational"}
    }

    with patch.object(monitor, "_http_get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = response_data
        mock_response.elapsed.total_seconds.return_value = 0.123
        mock_get.return_value = mock_response

        result = await monitor.check_status()

        assert result.service_name == "cloudflare"
        assert result.status == "operational"
        assert result.response_time_ms == 123
        assert result.details["indicator"] == "none"
        assert result.details["description"] == "All Systems Operational"
