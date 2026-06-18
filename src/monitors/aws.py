"""AWS Health status monitor."""

from src.monitors.base import BaseMonitor, HealthCheckResult


class AWSMonitor(BaseMonitor):
    """Monitor for AWS Health status."""

    STATUS_URL = "https://health.aws.amazon.com/health/status"

    def __init__(self):
        """Initialize AWS monitor."""
        super().__init__(service_name="aws", display_name="AWS", url=self.STATUS_URL)

    async def check_status(self) -> HealthCheckResult:
        """Check AWS status via web scraping.

        AWS doesn't have a simple public API, so we scrape the status page.

        Returns:
            HealthCheckResult with current status
        """
        response = await self._http_get(self.STATUS_URL)
        soup = await self._parse_html(response.text)

        # Look for status indicators in the page
        # AWS status page typically has a "Service is operating normally" message
        page_text = soup.get_text().lower()

        if "operating normally" in page_text or "service is operating" in page_text:
            status = "operational"
            indicator = "operational"
        elif "performance issues" in page_text or "degraded" in page_text:
            status = "degraded"
            indicator = "degraded"
        elif "service disruption" in page_text or "outage" in page_text:
            status = "outage"
            indicator = "outage"
        else:
            status = "unknown"
            indicator = "unknown"

        response_time_ms = int(response.elapsed.total_seconds() * 1000)

        return HealthCheckResult(
            service_name=self.service_name,
            status=status,
            response_time_ms=response_time_ms,
            details={"indicator": indicator, "source": "web_scraping"},
        )
