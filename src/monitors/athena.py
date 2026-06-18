"""Athena Health status monitor."""

from src.monitors.base import BaseMonitor, HealthCheckResult


class AthenaMonitor(BaseMonitor):
    """Monitor for Athena Health status."""

    STATUS_URL = "https://status.athenahealth.com"

    def __init__(self):
        """Initialize Athena monitor."""
        super().__init__(
            service_name="athena", display_name="Athena Health", url=self.STATUS_URL
        )

    async def check_status(self) -> HealthCheckResult:
        """Check Athena status via web scraping.

        Returns:
            HealthCheckResult with current status
        """
        response = await self._http_get(self.STATUS_URL)
        soup = await self._parse_html(response.text)

        # Look for status indicators
        page_text = soup.get_text().lower()

        if "all systems operational" in page_text or "no issues" in page_text:
            status = "operational"
            indicator = "operational"
        elif "degraded" in page_text or "partial" in page_text:
            status = "degraded"
            indicator = "degraded"
        elif "outage" in page_text or "major" in page_text:
            status = "outage"
            indicator = "outage"
        else:
            # Try to find status component
            status_elem = soup.find(class_=["status", "component-status"])
            if status_elem:
                elem_text = status_elem.get_text().lower()
                if "operational" in elem_text:
                    status = "operational"
                    indicator = "operational"
                else:
                    status = "unknown"
                    indicator = "unknown"
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
