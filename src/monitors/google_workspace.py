"""Google Workspace status monitor."""

from src.monitors.base import BaseMonitor, HealthCheckResult


class GoogleWorkspaceMonitor(BaseMonitor):
    """Monitor for Google Workspace status."""

    STATUS_URL = "https://www.google.com/appsstatus/dashboard/"

    def __init__(self):
        """Initialize Google Workspace monitor."""
        super().__init__(
            service_name="google_workspace",
            display_name="Google Workspace",
            url=self.STATUS_URL,
        )

    async def check_status(self) -> HealthCheckResult:
        """Check Google Workspace status via web scraping.

        Returns:
            HealthCheckResult with current status
        """
        response = await self._http_get(self.STATUS_URL)
        soup = await self._parse_html(response.text)

        # Google Workspace dashboard shows green/yellow/red indicators
        page_text = soup.get_text().lower()

        # Look for service disruption indicators
        if "service outage" in page_text or "service disruption" in page_text:
            status = "outage"
            indicator = "outage"
        elif "service degradation" in page_text or "service issue" in page_text:
            status = "degraded"
            indicator = "degraded"
        else:
            # Check for "available" or "no issues" indicators
            if "available" in page_text or soup.find(class_="green"):
                status = "operational"
                indicator = "operational"
            else:
                status = "unknown"
                indicator = "unknown"

        response_time_ms = int(response.elapsed.total_seconds() * 1000)

        return HealthCheckResult(
            service_name=self.service_name,
            status=status,
            response_time_ms=response_time_ms,
            details={
                "indicator": indicator,
                "description": f"Status: {status}",
                "source": "web_scraping",
            },
        )
