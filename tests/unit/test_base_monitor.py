"""Tests for base monitor class."""
import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_base_monitor_check_status_abstract():
    """Test base monitor check_status is abstract."""
    from src.monitors.base import BaseMonitor, HealthCheckResult

    class TestMonitor(BaseMonitor):
        pass

    # Can't instantiate without implementing check_status
    with pytest.raises(TypeError):
        monitor = TestMonitor(service_name="test", display_name="Test", url="https://example.com")


@pytest.mark.asyncio
async def test_base_monitor_timeout_handling():
    """Test monitor handles timeout."""
    from src.monitors.base import BaseMonitor, HealthCheckResult

    class TestMonitor(BaseMonitor):
        async def check_status(self) -> HealthCheckResult:
            import asyncio
            await asyncio.sleep(100)  # Simulate long request
            return HealthCheckResult(
                service_name=self.service_name,
                status="operational",
                response_time_ms=100,
                details={}
            )

    monitor = TestMonitor(
        service_name="test",
        display_name="Test",
        url="https://example.com",
        timeout=1  # 1 second timeout
    )

    with pytest.raises(asyncio.TimeoutError):
        await monitor.execute_check()


@pytest.mark.asyncio
async def test_base_monitor_execute_check():
    """Test monitor execute_check method."""
    from src.monitors.base import BaseMonitor, HealthCheckResult

    class TestMonitor(BaseMonitor):
        async def check_status(self) -> HealthCheckResult:
            return HealthCheckResult(
                service_name=self.service_name,
                status="operational",
                response_time_ms=234,
                details={"test": "data"}
            )

    monitor = TestMonitor(
        service_name="test",
        display_name="Test Service",
        url="https://example.com"
    )

    result = await monitor.execute_check()

    assert result.service_name == "test"
    assert result.status == "operational"
    assert result.response_time_ms == 234
    assert isinstance(result.checked_at, datetime)


@pytest.mark.asyncio
async def test_base_monitor_http_get():
    """Test HTTP GET helper method."""
    from src.monitors.base import BaseMonitor, HealthCheckResult

    class TestMonitor(BaseMonitor):
        async def check_status(self) -> HealthCheckResult:
            return HealthCheckResult(
                service_name=self.service_name,
                status="operational",
                response_time_ms=100,
                details={}
            )

    monitor = TestMonitor(
        service_name="test",
        display_name="Test",
        url="https://httpbin.org/json"
    )

    response = await monitor._http_get("https://httpbin.org/json")

    assert response.status_code == 200
    assert "slideshow" in response.json()
