"""Base monitor class for service status checking."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

from src.config import get_settings


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    service_name: str
    status: str  # operational, degraded, outage, unknown
    response_time_ms: int
    details: dict[str, Any]
    checked_at: datetime = None

    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.now(UTC)


class BaseMonitor(ABC):
    """Base class for service status monitors."""

    def __init__(
        self,
        service_name: str,
        display_name: str,
        url: str,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """Initialize monitor.

        Args:
            service_name: Internal service identifier (e.g., 'github')
            display_name: Human-readable service name (e.g., 'GitHub')
            url: Status page URL or API endpoint
            timeout: Request timeout in seconds (default from settings)
            max_retries: Maximum retry attempts (default from settings)
        """
        settings = get_settings()

        self.service_name = service_name
        self.display_name = display_name
        self.url = url
        self.timeout = timeout or settings.monitor_timeout
        self.max_retries = max_retries or settings.monitor_max_retries

        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": "StatusMonitor/1.0"},
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @abstractmethod
    async def check_status(self) -> HealthCheckResult:
        """Check service status and return result.

        This method must be implemented by subclasses.

        Returns:
            HealthCheckResult with status information
        """
        raise NotImplementedError("Subclasses must implement check_status()")

    async def execute_check(self) -> HealthCheckResult:
        """Execute health check with timeout and error handling.

        Returns:
            HealthCheckResult (may have status='unknown' on error)
        """
        try:
            # Execute check with timeout
            result = await asyncio.wait_for(self.check_status(), timeout=self.timeout)
            return result

        except asyncio.TimeoutError:
            raise

        except Exception as e:
            # Return unknown status on unexpected errors
            return HealthCheckResult(
                service_name=self.service_name,
                status="unknown",
                response_time_ms=0,
                details={"error": str(e)},
            )

    async def _http_get(self, url: str) -> httpx.Response:
        """Make HTTP GET request with retry logic.

        Args:
            url: URL to fetch

        Returns:
            HTTP response

        Raises:
            httpx.HTTPError: On request failure after retries
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.get(url)
                response.raise_for_status()
                return response

            except httpx.HTTPError as e:
                last_error = e
                if attempt < self.max_retries:
                    # Exponential backoff: 2^attempt seconds
                    await asyncio.sleep(2**attempt)
                continue

        # All retries failed
        raise last_error

    async def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content.

        Args:
            html: HTML string

        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, "lxml")

    def _map_status(self, indicator: str) -> str:
        """Map status indicator to standard status.

        Common mappings for Atlassian Statuspage format:
        - none -> operational
        - minor -> degraded
        - major -> degraded
        - critical -> outage

        Args:
            indicator: Raw status indicator

        Returns:
            Standardized status string
        """
        indicator = indicator.lower()

        if indicator in ("none", "operational", "ok", "up"):
            return "operational"
        elif indicator in ("minor", "degraded", "warning"):
            return "degraded"
        elif indicator in ("major", "critical", "down", "outage"):
            return "outage"
        else:
            return "unknown"
