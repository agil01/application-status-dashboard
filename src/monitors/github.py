"""GitHub status monitor."""

from src.monitors.base import BaseMonitor, HealthCheckResult


class GitHubMonitor(BaseMonitor):
    """Monitor for GitHub status."""

    API_URL = "https://www.githubstatus.com/api/v2/status.json"

    def __init__(self):
        """Initialize GitHub monitor."""
        super().__init__(service_name="github", display_name="GitHub", url=self.API_URL)

    async def check_status(self) -> HealthCheckResult:
        """Check GitHub status via API.

        Returns:
            HealthCheckResult with current status
        """
        response = await self._http_get(self.API_URL)
        data = response.json()

        # Extract status indicator
        status_info = data.get("status", {})
        indicator = status_info.get("indicator", "unknown")

        # Map to standard status
        status = self._map_status(indicator)

        # Calculate response time in milliseconds
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
