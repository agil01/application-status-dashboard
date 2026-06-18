"""Zscaler status monitor."""

from src.monitors.base import BaseMonitor, HealthCheckResult


class ZscalerMonitor(BaseMonitor):
    """Monitor for Zscaler status."""

    STATUS_URL = "https://trust.zscaler.com/zscaler.net"

    def __init__(self):
        """Initialize Zscaler monitor."""
        super().__init__(
            service_name="zscaler", display_name="Zscaler", url=self.STATUS_URL
        )

    async def check_status(self) -> HealthCheckResult:
        """Check Zscaler status via web scraping.

        Returns:
            HealthCheckResult with current status
        """
        response = await self._http_get(self.STATUS_URL)
        soup = await self._parse_html(response.text)

        page_text = soup.get_text().lower()

        if "all systems operational" in page_text or "operational" in page_text:
            status = "operational"
            indicator = "operational"
        elif "degraded" in page_text or "performance issue" in page_text:
            status = "degraded"
            indicator = "degraded"
        elif "outage" in page_text or "service disruption" in page_text:
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
