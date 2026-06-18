"""Monitor registry and utilities."""

from typing import Optional

from src.monitors.athena import AthenaMonitor
from src.monitors.aws import AWSMonitor
from src.monitors.cloudflare import CloudflareMonitor
from src.monitors.github import GitHubMonitor
from src.monitors.google_workspace import GoogleWorkspaceMonitor
from src.monitors.okta import OktaMonitor
from src.monitors.zscaler import ZscalerMonitor
from src.monitors.base import BaseMonitor


# Registry of all monitors
_MONITORS = [
    AthenaMonitor(),
    AWSMonitor(),
    CloudflareMonitor(),
    GitHubMonitor(),
    GoogleWorkspaceMonitor(),
    OktaMonitor(),
    ZscalerMonitor(),
]


def get_all_monitors() -> list[BaseMonitor]:
    """Get list of all service monitors.

    Returns:
        List of all monitor instances
    """
    return _MONITORS


def get_monitor_by_name(service_name: str) -> Optional[BaseMonitor]:
    """Get monitor by service name.

    Args:
        service_name: Service identifier (e.g., 'github')

    Returns:
        Monitor instance or None if not found
    """
    for monitor in _MONITORS:
        if monitor.service_name == service_name:
            return monitor
    return None


__all__ = [
    "get_all_monitors",
    "get_monitor_by_name",
    "BaseMonitor",
    "AthenaMonitor",
    "AWSMonitor",
    "CloudflareMonitor",
    "GitHubMonitor",
    "GoogleWorkspaceMonitor",
    "OktaMonitor",
    "ZscalerMonitor",
]
