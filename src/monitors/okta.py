"""Okta status monitor."""

from src.monitors.base import BaseMonitor, HealthCheckResult


class OktaMonitor(BaseMonitor):
    """Monitor for Okta status."""

    API_URL = "https://status.okta.com/api/v2/status.json"

    def __init__(self):
        """Initialize Okta monitor."""
        super().__init__(service_name="okta", display_name="Okta", url=self.API_URL)

    async def check_status(self) -> HealthCheckResult:
        """Check Okta status via API.

        Returns:
            HealthCheckResult with current status
        """
        response = await self._http_get(self.API_URL)
        data = response.json()

        status_info = data.get("status", {})
        indicator = status_info.get("indicator", "unknown")
        status = self._map_status(indicator)

        response_time_ms = int(response.elapsed.total_seconds() * 1000)

        return HealthCheckResult(
            service_name=self.service_name,
            status=status,
            response_time_ms=response_time_ms,
            details={
                "indicator": indicator,
                "description": status_info.get("description", ""),
            },
        )
